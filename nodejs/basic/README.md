# Node.js basic example

A Node.js Express application that visualizes graph queries against Aerospike Graph Service (AGS) in a web browser.

## Prerequisites

- Node.js 14 or later (for the Express app).
- Docker (for AGS).

> **Note:** AGS requires Apache TinkerPop 3.7.x Gremlin client drivers. TinkerPop 3.8.x and 4.0.x are incompatible.

## Install dependencies

From the repository root, change into the Node.js example directory and install dependencies:

```shell
cd nodejs/basic
npm ci
```

## Start the server

```shell
npm start
```

## Open the web page

When the server prints `Server listening on http://localhost:5000`, the app is running. Open `http://localhost:5000` in a web browser to use the UI.

If the response shows the following error:

```text
http://localhost:5000/index.html sent back an error.
Error code 403: Forbidden
```

Port 5000 is already in use. Stop the conflicting process and retry.

## Interact with the graph

This example provides four visualized queries. In each visualization, you can:

- Left-click and drag in white space to move around the graph.
- Use the scroll wheel to zoom in and out.
- Left-click, hold, and drag a node to move it. Connections follow electron physics, so pulling a node too far can move the entire subgraph.
- Left-click on a node to open a modal showing its properties.
- Left-click on an edge to open a modal showing its properties.

The four visualized queries available in the sidebar are:

### Transactions between users

Select two people from the top-right of the page, then click **Reload Graph** to see all transactions between them.

### Outgoing transactions from a user

Select a single user from the top-right of the page, then click **Reload Graph** to see all transactions that user sent to others.

### Incoming transactions for a user

Select a single user from the top-right of the page, then click **Reload Graph** to see all transactions other users sent to that user.

### Fraud detection

Queries the database and ranks users by likelihood of being fraudulent (most likely first). Displays the graph of the most likely user and shows the recent increase in their transactions in the top-right.
