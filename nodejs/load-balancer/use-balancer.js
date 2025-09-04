const gremlin = require('gremlin');
const { traversal } = gremlin.process;
const { RoundRobinClientRemoteConnection } = require('./load-balancer');

const endpoints = ['localhost:8181', 'localhost:8182', 'localhost:8183'];

const lbLogger = (level, msg) => {
    const ts = new Date().toISOString();
    console.log(`${ts} RoundRobinClientRemoteConnection ${level.toUpperCase()}: ${msg}`);
};

(async () => {
    const rr = new RoundRobinClientRemoteConnection(
        endpoints,
        'g',
        2,
        lbLogger // debug logger
    );

    try {
        const g = traversal().withRemote(rr);

        const user1 = await g.addV('User').property('userId', 'U1').property('name', 'Alice').property('age', 30).next();
        const user2 = await g.addV('User').property('userId', 'U2').property('name', 'Bob').property('age', 25).next();
        const user3 = await g.addV('User').property('userId', 'U3').property('name', 'Charlie').property('age', 35).next();

        const account1 = await g.addV('Account').property('accountId', 'A1').property('balance', 1000).next();
        const account2 = await g.addV('Account').property('accountId', 'A2').property('balance', 500).next();
        const account3 = await g.addV('Account').property('accountId', 'A3').property('balance', 750).next();

        await g.addE('owns').from_(user1.value).to(account1.value).iterate();
        await g.addE('owns').from_(user2.value).to(account2.value).iterate();
        await g.addE('owns').from_(user3.value).to(account3.value).iterate();

        let i = 1;
        while (true) {
            try {
                const list = await g.V().limit(i).toList();
                console.log(`Fetched ${list.length} vertices`);
            } catch (e) {
                console.warn('Traversal failed:', e.message || e);
            }
            await new Promise((r) => setTimeout(r, 3000));
            i += 1;
        }
    } catch (e) {
        console.error('Fatal error:', e);
    } finally {
        process.on('SIGINT', async () => {
            await rr.close();
            console.log('Load balancer closed. Goodbye!');
            process.exit(0);
        });
    }
})();
