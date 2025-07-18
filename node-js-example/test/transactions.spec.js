import { describe, it } from "mocha";
import { expect } from "chai";
import { transactionsBetweenUsers, g } from "../gremlin.js";

describe("Transactions Between Users", () => {
  it("returns formatted graph data", async () => {
    const result = await transactionsBetweenUsers("Alice", "Bob");
    expect(result).to.have.property("nodes");
    expect(result).to.have.property("links");
    expect(result.nodes.length).to.equal(4);
    expect(result.links.length).to.equal(5);
  });
});
