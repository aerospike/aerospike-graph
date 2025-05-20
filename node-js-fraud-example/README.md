## Prerequisites

1.**Node.js 14+** (for the Express app)

2.**Docker** (for Aerospike Graph)

---

## Install Dependencies

```bash
# navigate to this directory in your terminal
npm i
```

## Start the Server

```bash
# must have node for this
node index.js
```

## Open the Web Page

Once you see ouput Server listening on http://localhost:5000
Navigate to that address on a web browser

## Play around with the Graph

This example gives you 4 visualized queries:

### Transactions Between Users

Select two people at the top right of the web page,
then see all transactions that occurred from those
two users

### Outgoing Transactions from User

Select a single user at the top right of the web page.
then see all transactions they sent to other users.

### Incoming Transactions from User

Select a single user at the top right of the web page.
then see all transactions other users sent to them.

### Full Graph

No input is required for this query, displays the full graph