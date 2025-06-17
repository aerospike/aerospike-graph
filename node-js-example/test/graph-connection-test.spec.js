import { describe, it, before, after } from 'mocha'
import { expect } from 'chai'
import gremlin from "gremlin";
import {drc} from "../gremlin.js";
const {traversal} = gremlin.process.AnonymousTraversalSource;
const __ = gremlin.process.statics;

describe('Aerospike Graph connectivity', function() {
    let g;

    before(async function() {
        this.timeout(10_000);
        g = traversal().withRemote(drc);
        const check = await g.inject(0).next();
        if (check.value !== 0) {
            console.error("Failed to connect to Gremlin server");
            return;
        }
        await g.V().drop().iterate()
    });

    after(async function() {
        // Close the Gremlin connection
        await drc.close()
        console.log("Closing Graph Connection")
    });

    it('should be able to run a simple Gremlin query', async function() {
        // E.g., get up to 1 vertex or return a constant
        const result = await g.V().limit(1).toList();
        // If the graph is empty, result is an empty array; the call still succeeded
        expect(result).to.be.an('array');
    });

    it('check we can add and read vertices and edges', async function() {
        let v1 = await g.addV("User").property("name", "donnie").next()
        let v2 = await g.addV("User").property("name", "joe").next()
        let e1 = await g.addE("loves").to(v1.value).from_(v2.value).next()
        const resultV = await g.V(v2.value).out().next()
        const resultE = await g.V(v1.value).inE().next()
        expect(resultV.value.id).to.equal(v1.value.id)
        expect(resultE.value.id).to.equal(e1.value.id)
    });
});
