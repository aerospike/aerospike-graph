import assert from "assert"

import {app} from '../index.js'

describe('Server startup', function() {
    let server;

    afterEach(function(done) {
        if (server && server.listening) {
            server.close(() => done());
        } else {
            done();
        }
    });

    it('should compile & start listening without errors', function(done) {
        server = app.listen(0, () => {
            const addr = server.address();
            assert(addr && addr.port > 0, 'Expected server to be listening on a port');
            done();
        });

        server.on('error', (err) => done(err));
    });
});
