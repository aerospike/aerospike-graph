import { describe, it, before } from "mocha";
import { expect } from "chai";
import { rankMostTraffic } from "../gremlin.js";
import { g } from "./setup.spec.js";

describe("Fraud Detection Logic", () => {
  before(async function () {
    const check = await g.inject(0).next();
    if (check.value !== 0) {
      console.error("Failed to connect to Gremlin server");
      return;
    }
    await g.V().drop().iterate();
    let Alice = await g.addV("User").property("name", "Alice").next();
    let Bob = await g.addV("User").property("name", "Bob").next();

    let aA = await g.addV("Account").property("accountId", "aA").next();
    let aB = await g.addV("Account").property("accountId", "aB").next();

    await g.addE("owns").to(aA.value).from_(Alice.value).iterate();
    await g.addE("owns").to(aB.value).from_(Bob.value).next();

    await g
      .addE("Transaction")
      .from_(aA.value)
      .to(aB.value)
      .property("amount", 600)
      .next();
    await g
      .addE("Transaction")
      .from_(aB.value)
      .to(aA.value)
      .property("amount", 400)
      .next();
    await g
      .addE("Transaction")
      .from_(aA.value)
      .to(aB.value)
      .property("amount", 5600)
      .next();
  });

  it("ranks accounts by outgoing transaction amount", async () => {
    const result = await rankMostTraffic();
    expect(result[0].get("accountId")).to.equal("aA");
    expect(result[1].get("accountId")).to.equal("aB");
  });
});
