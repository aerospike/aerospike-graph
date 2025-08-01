import { before, after } from "mocha";
import { drc } from "../../gremlin.js";
import gremlin from "gremlin";
const { traversal } = gremlin.process.AnonymousTraversalSource;

export let g;
before(async function () {
  g = traversal().withRemote(drc);
  const check = await g.inject(0).next();
  if (check.value !== 0) {
    throw new Error("Failed to connect to Gremlin server");
  }
  await g.V().drop().iterate()
  console.log("Global: Connection verified");
});

after(async function () {
  await drc.close();
  console.log("Global: Connection closed");
});
