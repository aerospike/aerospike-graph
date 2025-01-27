# Real-Time Fraud Detection with Aerospike Graph

## Scenario 1: Evaluating Known Beneficiary
### Case:
Rajesh Kumar (VPA: `8056629010@ybl`) is sending INR 40,000 to `7797767385@ybl`. Check if this is a known beneficiary.

### Steps:
1. **Find the VPA and load all outgoing transactions:**
   ```groovy
   g.V("8056629010@ybl")
2. Check if Sender’s VPA has transacted with Receiver’s VPA before:
   ```groovy
   g.V("8056629010@ybl").out("transaction").hasId("7797767385@ybl")
3. Explore other VPAs of the sender and evaluate transactions with the receiver:
   ```groovy
   g.V("8056629010@ybl").in("owns").in("has_account").outE('has_account', 'has_card').inV().outE("owns").inV().outE("transaction").inV().path()

Or using the person vertex directly:
   ```groovy
  g.V('CQE72NZMJL').outE('has_account', 'has_card').inV().outE("owns").inV().outE("transaction").inV().path()

4. Real-Time Check Query:
   ```groovy
   g.V('CQE72NZMJL')
   .out('has_account', 'has_card')
   .out('owns')
   .out('transaction')
   .dedup()
   .hasId('7797767385@ybl')
