import { describe, it, before, after } from 'mocha'
import { expect } from 'chai'
import  supertest from 'supertest'
import { server } from '../index.js';
import gremlin from "gremlin";
import {HOST, PORT} from "../public/consts.js";
const {DriverRemoteConnection} = gremlin.driver;
const {traversal} = gremlin.process.AnonymousTraversalSource;

describe('Express Endpoint Testing', function() {
    let request;
    let g;

    // Give the Aerospike Graph container a moment to be ready before launching Express.
    before(async function() {
        this.timeout(15_000);
        request = supertest(server);
        let gremlinConn = new DriverRemoteConnection(`ws://${HOST}:${PORT}/gremlin`);
        g = traversal().withRemote(gremlinConn);
        const check = await g.inject(0).next();
        if (check.value !== 0) {
            console.error("Failed to connect to Gremlin server");
            return;
        }
        await g.V().drop().iterate()
    });

    after(function(done) {
        server.close(done);
    });

    it('GET /ping should return a 200 string', async function() {
        // If no vertices exist yet, we still want a 200 with an empty array
        const res = await request.get('/ping').expect(200);
        expect(res.body).to.be.an('string');
        expect(res.body).to.equal('pong');
    });

    it('GET /names should return names of all person vertices in db', async function() {
        const params = new URLSearchParams({
                name: ""
            }
        )
        await g.addV("User").property("name", "becky")
            .addV("User").property("name", "keisha")
            .addV("User").property("name", "ashley").next()

        const res = await request.get(`/names?${params}`).expect(200);
        expect(res.body).to.be.an('object')
        expect(res.body.names).to.be.an('array')
        expect(res.body.names).to.have.same.members([
            'keisha',
            'becky',
            'ashley'
        ]);

    } )

    it('POST /graph/ should return graph', async function() {
        // Define a dummy node payload
        const payload = { label: 'person', properties: { name: 'TestUser' } };
        /*const res = await request
            .post('/graph')
            .send(payload)
            .set('Content-Type', 'application/json')
            .expect(201);

        expect(res.body).to.include.keys('id', 'label');
        expect(res.body.label).to.equal('person');
        expect(res.body.properties.name).to.equal('TestUser');
        */
    });

});
