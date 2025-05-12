## Prerequisites

1. **Node.js 14+** (for the Express app)

2. **Docker** (for Aerospike Graph)

---

## Install Dependencies

Navigate to the `node-js-fraud-example` directory and run
the following command:

```bash
npm i
```

## Start the Server

```bash
node index.js
```

## Open the Web Page

The shell output `Server listening on http://localhost:5000`
indicates that the app is running.
Navigate to `http://localhost:5000` in a web browser
to use the app's UI.

## Play around with the Graph

This example gives you four visualized queries:

### Transactions Between Users

Select two people at the top right of the web page,
then see all transactions that occurred from those
two users.

### Outgoing Transactions from User

Select a single user at the top right of the web page.
then see all transactions they sent to other users.

### Incoming Transactions from User

Select a single user at the top right of the web page.
then see all transactions other users sent to them.

### Full Graph

No input is required for this query. It displays the full graph.