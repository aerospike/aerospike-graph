const gremlin = require('gremlin');
const { DriverRemoteConnection } = gremlin.driver;
const { traversal } = gremlin.process;

class RoundRobinClientRemoteConnection {
    constructor(
        endpoints,
        traversalSource = 'g',
        healthCheckIntervalSec = 10,
        logger = null
    ) {
        this._traversalSource = traversalSource;
        this._logger =
            logger ||
            ((level, msg) => {
                if (level === 'debug') console.debug(msg);
                else if (level === 'info') console.info(msg);
                else if (level === 'warn') console.warn(msg);
                else console.log(msg);
            });

        this._clients = endpoints.map(
            (host) => new DriverRemoteConnection(`ws://${host}/gremlin`, { traversalSource })
        );
        this._available = Array(this._clients.length).fill(true);
        this._pos = 0;

        this._stopped = false;
        this._healthIntervalMs = Math.max(1, healthCheckIntervalSec) * 1000;
        this._healthTimer = setInterval(() => this._healthCheckLoop(), this._healthIntervalMs);

        this._debug(`Initialized load-balancer with endpoints: ${endpoints.join(', ')}`);
    }

    async submit(bytecode, requestOptions) {
        let lastErr = null;

        for (let attempt = 0; attempt < this._clients.length; attempt++) {
            const healthy = [];
            for (let i = 0; i < this._available.length; i++) {
                if (this._clients[i] && this._available[i]) healthy.push(i);
            }
            if (healthy.length === 0) {
                throw new Error('No healthy Gremlin hosts available');
            }
            const pick = healthy[this._pos % healthy.length];
            this._pos += 1;

            const pickedConn = this._clients[pick];

            try {
                const rs = await pickedConn.submit(bytecode, requestOptions);
                this._available[pick] = true;
                this._debug(`Traversal submitted via connection #${pick}`);
                return rs;
            } catch (e) {
                const idxNow = this._clients.indexOf(pickedConn);
                if (idxNow !== -1) this._available[idxNow] = false;
                this._warn(`Connection #${idxNow !== -1 ? idxNow : '?'} failed: ${e?.message || e} – marking host down`);
                lastErr = e;
            }
        }

        this._error('All endpoints failed – raising');
        const err = new Error('All Gremlin endpoints failed');
        err.cause = lastErr;
        throw err;
    }

    async close() {
        if (this._stopped) return;
        clearInterval(this._healthTimer);
        this._stopped = true;

        const tasks = [];
        for (const c of this._clients) {
            if (!c) continue;
            try {
                tasks.push(c.close().catch(() => {}));
            } catch {}
        }
        await Promise.allSettled(tasks);
        this._debug('Load balancer closed');
    }

    addHost(endpoint) {
        const c = new DriverRemoteConnection(`ws://${endpoint}/gremlin`, {
            traversalSource: this._traversalSource,
        });
        this._clients.push(c);
        this._available.push(true);
        this._info(`Added host ${endpoint}`);
    }

    removeHost(endpoint) {
        let removed = false;
        for (let i = this._clients.length - 1; i >= 0; i--) {
            const c = this._clients[i];
            const url = c && (c.url || c._url || '');
            if (c && url.includes(endpoint)) {
                try { c.close().catch(() => {}); } catch {}
                this._clients[i] = null;
                this._available[i] = false;
                removed = true;
            }
        }
        if (removed) this._info(`Removed host ${endpoint}`); else this._warn(`Tried to remove non-existent host ${endpoint}`);
    }

    getClients() {
        return this._clients.filter(Boolean);
    }

    getAvailable() {
        const out = [];
        for (let i = 0; i < this._clients.length; i++) {
            if (this._clients[i]) out.push(!!this._available[i]);
        }
        return out;
    }

    async _healthCheckLoop() {
        if (this._stopped) return;
        this._debug('Running health check');
        const tasks = [];

        for (let i = 0; i < this._clients.length; i++) {
            const conn = this._clients[i];
            if (!conn) continue;
            if (this._available[i]) continue;
            tasks.push(
                (async () => {
                    try {
                        const g = traversal().withRemote(conn);
                        await g.V().limit(1).toList();
                        this._available[i] = true;
                        this._info(`Host #${i} is healthy again`);
                    } catch {
                        this._available[i] = false;
                        this._debug(`Host #${i} still down`);
                    }
                })()
            );
        }
        await Promise.allSettled(tasks);
    }

    _debug(msg) {
        this._logger('debug', msg);
    }
    _info(msg) {
        this._logger('info', msg);
    }
    _warn(msg) {
        this._logger('warn', msg);
    }
    _error(msg) {
        this._logger('error', msg);
    }
}

module.exports = { RoundRobinClientRemoteConnection };
