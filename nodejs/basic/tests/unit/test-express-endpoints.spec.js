import { describe, it, before, after } from 'mocha'
import { expect } from 'chai'
import  supertest from 'supertest'
import { app } from '../../index.js';
import { g } from "./test-setup.spec.js";

describe('Express Endpoint Testing', function() {
    let request;

    // Give the Aerospike Graph container a moment to be ready before launching Express.
    before(async function() {
        this.timeout(15_000);
        request = supertest(app);
        const check = await g.inject(0).next();
        if (check.value !== 0) {
            console.error("Failed to connect to Gremlin server");
            return;
        }
        await g.V().drop().iterate()
        let becky = await g.addV("User").property("name", "becky").next()
        let keisha = await g.addV("User").property("name", "keisha").next()
        let ashley  = await g.addV("User").property("name", "ashley").next()

        let aB = await g.addV("Account").property("accountId", "aB").next()
        let aK = await g.addV("Account").property("accountId", "aK").next()
        let aA = await g.addV("Account").property("accountId", "aA").next()

        await g.addE("owns").to(aB.value).from_(becky.value).iterate()
        await g.addE("owns").to(aK.value).from_(keisha.value).next()
        await g.addE("owns").to(aA.value).from_(ashley.value).next()

        await g.addE("Transaction").from_(aK.value).to(aB.value).property("amount", 600).next()
        await g.addE("Transaction").from_(aA.value).to(aB.value).property("amount", 400).next()
        await g.addE("Transaction").from_(aA.value).to(aB.value).property("amount", 5600).next()
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

        const payload = { routeKey: "incoming", user1: "becky" , user2: null};
        const res = await request
            .get('/graph')
            .query(payload)
            .set('Content-Type', 'application/json')
            .expect(200);
        expect(res.body).to.include.keys('nodes', 'links');
        let edges = res.body.links
        let vertices = res.body.nodes
        expect(edges).to.be.an('array');
        expect(vertices).to.be.an('array');

        edges.forEach((edge, idx) => {
            expect(edge).to.be.an('object')
                .that.has.all.keys('source','target','label','data');

            expect(edge.source,  `item ${idx} source`).to.be.a('number');
            expect(edge.target,  `item ${idx} target`).to.be.a('number');
            expect(edge.label,   `item ${idx} label`).to.be.a('string');
            expect(edge.data,    `item ${idx} data`).to.be.an('object');
        });

        vertices.forEach((vert, idx) => {
            expect(vert).to.be.an('object')
                .that.has.all.keys('id','label','data');

            expect(vert.id,  `item ${idx} source`).to.be.a('number');
            expect(vert.label,   `item ${idx} label`).to.be.a('string');
            expect(vert.data,    `item ${idx} data`).to.be.an('object');
        });
    });

});
