## Prerequisites


1. **Node.js 14+** (for the Express app)

2. **Docker** (for Aerospike Graph)


## Install Dependencies


Navigate to the `node-js-example` directory and run
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

If you get the error 
```
http://localhost:5000/index.html sent back and error.
Error code 403: Forbidden
```
You are most likely running a process on the port localhost:5000 already, terminate it and try again


## Play around with the Graph

This example gives you four visualized queries.
In each of these queries, when the graph is visualized
you can do the following actions:

- Left click and drag in white space to move around the graph
- Use scroll wheel to zoom in and out of the graph
- Left click, hold, and drag a node to move it around the graph, the connections follow electron phyiscs, so pulling to far can result in moving the entire subgraph
- Left click on a node to open a modal showing its properties
- Left click on an edge to open a modal showing its properties

The four visualized queries found on the sidebar include:

### Transactions Between Users

Select two people at the top right of the web page,
then click the **Reload Graph** button and see all transactions that occurred from those
two users.

### Outgoing Transactions from User

Select a single user at the top right of the web page.
then click the **Reload Graph** button and see all transactions they sent to other users.

### Incoming Transactions from User

Select a single user at the top right of the web page.
then click the **Reload Graph** button and see all transactions other users sent to them.

### Fraud Detection

Queries the database and ranks users by most to least likely
to be fraudulent. Displays the graph of the most likely node, 
and the increase in transactions they have in the top right.
