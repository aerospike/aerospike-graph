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
   ```
   Or using the person vertex directly:
   ```groovy
   g.V('CQE72NZMJL').outE('has_account', 'has_card').inV().outE("owns").inV().outE("transaction").inV().path()
   ```
4. Real-Time Check Query:
   ```groovy
   g.V('CQE72NZMJL')
   .out('has_account', 'has_card')
   .out('owns')
   .out('transaction')
   .dedup()
   .hasId('7797767385@ybl')

## Scenario 2: Evaluating First-Time Connections
Sender `A` sends money to `9524356932@ybl (C)`. A has previously transacted with `B`, and `B` has transacted with `C`.

### Steps:
```groovy
# Verify if `9524356932@ybl` was part of previous transactions:
g.V('CQE72NZMJL')
  .out('has_account', 'has_card')
  .out('owns')
  .out('transaction')
  .dedup()
  .hasId('9524356932@ybl')

# Extend the query to include second-degree transactions:
g.V('CQE72NZMJL')
  .out('has_account', 'has_card')
  .out('owns')
  .out('transaction')
  .dedup()
  .out('transaction')
  .hasId("9524356932@ybl")
```
## Scenario 3: Velocity of Outgoing Transactions 
### Steps:
```groovy
# Calculate average outgoing transaction amount for each sender VPA:
g.V('CQE72NZMJL')
  .out('has_account', 'has_card')
  .out('owns')
  .group()
    .by(id)
    .by(local(
       outE('transaction')
       .values('amount')
       .mean()
    ))

# Calculate average transaction amount across all sender VPAs:
g.V('CQE72NZMJL')
  .outE('has_account', 'has_card')
  .inV()
  .outE('owns')
  .inV()
  .outE('transaction')
  .values('amount')
  .mean()
```
## Scenario 4: Device Reuse Detection
### Steps:
```groovy
# List all devices used by the user:
g.V('CQE72NZMJL').out("known_device").valueMap()

# Next Step: Extend to include other users sharing the same household based on additional address data.

```
## Scenario 5: Transactional IP City Analysis
### Steps:
```groovy
# IP Cities in the immediate network:
g.V('CQE72NZMJL')
  .out("has_account", "has_card")
  .out("owns")
  .outE("transaction")
  .values("ip_city")
  .dedup()
  .toList()

# IP Cities in the extended network:
g.V('CQE72NZMJL')
  .out('has_account', 'has_card')
  .out('owns')
  .out('transaction')
  .outE('transaction')
  .values('ip_city')
  .dedup()
  .toList()
```
## Scenario 6: Fraud and Flagged Activity Counts
### Steps:
```groovy
# Blocked accounts/cards in the immediate network:
g.V('CQE72NZMJL')
  .out('has_account', 'has_card')
  .has('fraud_block', true)
  .count()

# Blocked accounts/cards in the extended network:
g.V('CQE72NZMJL')
  .out('has_account', 'has_card')
  .out('owns')
  .out('transaction')
  .in('owns')
  .has('fraud_block', true)
  .count()

# Flagged persons/merchants in the extended network:
g.V('CQE72NZMJL')
  .out('has_account', 'has_card')
  .out('owns')
  .out("transaction")
  .in("owns")
  .out("has_account", "has_card")
  .has("fraud_flag", true)

# Count fraud-flagged transactions in the immediate network:
g.V('CQE72NZMJL')
  .out('has_account', 'has_card')
  .out('owns')
  .outE("transaction")
  .has("fraud_flag", true)
  .count()

# Count fraud-flagged transactions in the extended network:
g.V('CQE72NZMJL')
  .out('has_account', 'has_card')
  .out('owns')
  .out("transaction")
  .outE("transaction")
  .has("fraud_flag", true)
  .count()
