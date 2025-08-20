const gremlin = require('gremlin');
const { traversal } = gremlin.process;
const net = require('node:net');
const { execSync } = require('node:child_process');
const { RoundRobinClientRemoteConnection } = require('../load-balancer');

jest.setTimeout(60000);

const ENDPOINTS = ['localhost:8181', 'localhost:8182', 'localhost:8183'];

function loggerCollector() {
    const lines = [];
    return {
        fn: (level, msg) => lines.push(`${level}:${msg}`),
        dump: () => lines.join('\n'),
        count: (needle) => lines.filter((l) => l.includes(needle)).length,
        clear: () => (lines.length = 0),
    };
}

async function setupGraph(rr) {
    const g = traversal().withRemote(rr);
    await g.V().drop().iterate();
    const user1 = await g.addV('User').property('userId', 'U1').property('name', 'Alice').property('age', 30).next();
    const user2 = await g.addV('User').property('userId', 'U2').property('name', 'Bob').property('age', 25).next();
    const user3 = await g.addV('User').property('userId', 'U3').property('name', 'Charlie').property('age', 35).next();

    const account1 = await g.addV('Account').property('accountId', 'A1').property('balance', 1000).next();
    const account2 = await g.addV('Account').property('accountId', 'A2').property('balance', 500).next();
    const account3 = await g.addV('Account').property('accountId', 'A3').property('balance', 750).next();
    await g.addE('owns').from_(user1.value).to(account1.value).iterate();
    await g.addE('owns').from_(user2.value).to(account2.value).iterate();
    await g.addE('owns').from_(user3.value).to(account3.value).iterate();

    rr._pos = 0;
}

describe('RoundRobinClientRemoteConnection (JS)', () => {
    test('host add and removal', async () => {
        const log = loggerCollector();
        const rr = new RoundRobinClientRemoteConnection(ENDPOINTS, 'g', 2, log.fn);
        try {
            const initialHosts = rr.getClients();
            const initialAvail = rr.getAvailable();

            const toRemove = ENDPOINTS[1];
            rr.removeHost(toRemove);

            const postRemoveHosts = rr.getClients();
            const postRemoveAvail = rr.getAvailable();

            let removed = true;
            for (const c of postRemoveHosts) {
                const u = c.url || c._url || '';
                if (u.includes(toRemove)) removed = false;
            }
            expect(removed).toBe(true);
            expect(initialHosts.length).toBe(postRemoveHosts.length + 1);
            expect(initialAvail.length).toBe(postRemoveAvail.length + 1);

            rr.addHost(toRemove);

            const postAddHosts = rr.getClients();
            const postAddAvail = rr.getAvailable();

            let added = false;
            for (const c of postAddHosts) {
                const u = c.url || c._url || '';
                if (u.includes(toRemove)) added = true;
            }
            expect(added).toBe(true);
            expect(postRemoveHosts.length).toBe(postAddHosts.length - 1);
            expect(postRemoveAvail.length).toBe(postAddAvail.length - 1);
        }finally{
            await rr.close()
        }
    });

    test('rotation logs 0,1,2,0,1', async () => {
        const log = loggerCollector();
        const rr = new RoundRobinClientRemoteConnection(ENDPOINTS, 'g', 2, log.fn);
        try {
            await setupGraph(rr);
            log.clear(); // ignore seed logs

            const g = traversal().withRemote(rr);
            for (let i = 1; i <= 5; i++) {
                await g.V().has('name', 'Alice').limit(i).toList();
            }

            const got0 = log.count('Traversal submitted via connection #0');
            const got1 = log.count('Traversal submitted via connection #1');
            const got2 = log.count('Traversal submitted via connection #2');
            expect(got0).toBe(2);
            expect(got1).toBe(2);
            expect(got2).toBe(1);
        }finally {
            await rr.close();
        }
    });

    test('health check: mark down then recover', async () => {
        const log = loggerCollector();
        const rr = new RoundRobinClientRemoteConnection(ENDPOINTS, 'g', 2, log.fn);
        try {
            await setupGraph(rr);

            const name = 'aerospike-graph-service-2';
            const port = ENDPOINTS[1].split(':')[1];

            // Stop container and wait for port to close
            try {
                execSync(`docker stop ${name}`, {stdio: 'inherit'});
            } catch (e) {
                await rr.close();
                return; // skip if container not found
            }
            await waitPortClosed(`127.0.0.1`, +port, 25000);

            // trigger some traffic so the LB attempts the down host and marks it unhealthy
            const g = traversal().withRemote(rr);
            for (let i = 0; i < 3; i++) {
                try {
                    await g.V().has('name', 'Alice').limit(1).toList();
                } catch { /* ignore */
                }
                await sleep(200);
            }

            await sleep(2000); // allow LB state to settle

            const avail = rr.getAvailable();
            expect(avail.some((x) => x === false)).toBe(true);

            // Start container and wait for port to open
            execSync(`docker start ${name}`, {stdio: 'inherit'});
            await waitPortOpen(`127.0.0.1`, +port, 30000);

            // health loop should bring it back after a few ticks
            await sleep(8000);
            const avail2 = rr.getAvailable();
            expect(avail2.every((x) => x === true)).toBe(true);
        } finally {
            await rr.close();
        }
    });
});

function sleep(ms) {
    return new Promise((r) => setTimeout(r, ms));
}

function waitPortOpen(host, port, timeoutMs) {
    const deadline = Date.now() + timeoutMs;
    return new Promise((resolve, reject) => {
        const tryOnce = () => {
            const s = net.createConnection({ host, port }, () => {
                s.end();
                resolve();
            });
            s.on('error', () => {
                if (Date.now() > deadline) reject(new Error(`port ${host}:${port} not open`));
                else setTimeout(tryOnce, 300);
            });
        };
        tryOnce();
    });
}

function waitPortClosed(host, port, timeoutMs) {
    const deadline = Date.now() + timeoutMs;
    return new Promise((resolve, reject) => {
        const tryOnce = () => {
            const s = net.createConnection({ host, port }, () => {
                s.end();
                if (Date.now() > deadline) reject(new Error(`port ${host}:${port} still open`));
                else setTimeout(tryOnce, 300);
            });
            s.on('error', () => resolve()); // connection refused => closed
        };
        tryOnce();
    });
}
