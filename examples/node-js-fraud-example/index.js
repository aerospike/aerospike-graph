// Holds main server/app and gremlin logic

import gremlin from "gremlin"
import express from "express"
import path from "path"
import {fileURLToPath} from 'url';
import {dirname} from 'path';

// Gremlin imports
const {traversal} = gremlin.process.AnonymousTraversalSource;
const {DriverRemoteConnection} = gremlin.driver;
const {t, direction} = gremlin.process;

// Connection Variables
const HOST = "localhost";
const PORT = 8182;
const HTTP_PORT = 5000;

// Create Express app
const app = express();
const server = app.listen(HTTP_PORT, () =>
    console.log(`Server listening on http://localhost:${HTTP_PORT}`)
);

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

export const drc = new DriverRemoteConnection(
    `ws://${HOST}:${PORT}/gremlin`
);

export const g = traversal().withRemote(drc);

app.get("/", (req, res) => {
    res.sendFile(path.join(__dirname, "public", "index.html"));
});

app.get("/graph", async (req, res) => {
    try {
        let newGraph

        const {routeKey = 'between', user1, user2} = req.query;
        switch (routeKey) {
            case "home":
                newGraph = await getFullGraph(g);
                break;
            case "outgoing":
                newGraph = await userTransactions(user1, "out");
                break;
            case "incoming":
                newGraph = await userTransactions(user1, "in");
                break;
            default:
                newGraph = await transactionsBetweenUsers(user1, user2);
                break;
        }

        res.json(newGraph);
    } catch (e) {
        console.error("Error in /graph:", e);
        res.status(500).json({error: e.message});
    }
});

app.use(express.static(path.join(__dirname, "public")));

const userNames = [
    "Alice",
    "Bob",
    "Charlie",
    "Diana",
    "Eve",
    "Frank",
    "Grace",
    "Heidi",
    "Ivan",
    "Judy",
];

// Shut down server and clear graph data
async function closeConnection() {
    try {
        console.log("Closing connection...");
        await g.V().drop().iterate();
        await drc.close();
        server.close(() => process.exit(0));
        console.log("Connection Closed!");
    } catch (error) {
        console.error("Error closing connection:", error);
    }
}

// Populates gremlin server with transaction data
async function populateGraph() {
    try {
        await g.V().drop().iterate(); // Clear the graph before populating
        console.log("Populating graph...");

        const check = await g.inject(0).next();
        if (check.value !== 0) {
            console.error("Failed to connect to Gremlin server");
            return;
        }

        // Create people
        const userVertices = await Promise.all(
            userNames.map((name, i) =>
                g
                    .addV("User")
                    .property("userId", `U${i + 1}`)
                    .property("name", name)
                    .property("age", 25 + randomInt(-6, 40))
                    .next()
            )
        );

        // Create Accounts
        const balances = [
            5000, 3000, 4000, 2000, 6000, 7000, 8000, 9000, 10000, 11000,
        ];
        const accountVertices = [];
        for (let i = 0; i < balances.length; i++) {
            const bal = balances[i];
            // Insert one Account vertex, then await it before moving on
            const result = await g
                .addV("Account")
                .property("accountId", `A${i + 1}`)
                .property("balance", bal)
                .next();
            accountVertices.push(result);
        }

        // Link Users to Accounts
        await Promise.all(
            userVertices.map((u, i) =>
                g
                    .addE("owns")
                    .from_(u.value)
                    .to(accountVertices[i].value)
                    .property("since", `${2020 + randomInt(-8, 4)}`)
                    .iterate()
            )
        );

        const devices = ["mobile", "terminal", "web"];
        // Create random transactions
        for (let i = 1; i <= 100; i++) {
            const users = await g.V().hasLabel("Account").sample(2).toList();
            const from = users[0];
            const to = users[1];
            const amt = randomInt(1, 1001);
            const txId = `T${i}`;
            const type = Math.random() < 0.5 ? "debit" : "credit";
            const month = String(randomInt(1, 12)).padStart(2, "0");
            const day = String(randomInt(1, 28)).padStart(2, "0");
            const date = `2025-${month}-${day}`;
            const device = devices[Math.floor(Math.random() * devices.length)];
            await g
                .addE("Transaction")
                .from_(from)
                .to(to)
                .property("transactionId", txId)
                .property("amount", amt)
                .property("device", device)
                .property("type", type)
                .property("timestamp", convertTimestampToLong(date))
                .iterate();
        }

        console.log("Graph population complete.");
    } catch (error) {
        console.error("Error populating graph:", error);
    }
}

// Returns the D3 formatted elements of paths between two given users
async function transactionsBetweenUsers(user1, user2) {
    if (user1 === user2) { // edge case where user chooses 2 of the same user
        return {nodes: [], links: []};
    }
    const p1 = await g.V().has("User", "name", user2).id().next();
    const p2 = await g.V().has("User", "name", user1).id().next();
    const paths = await g
        .V(p1.value)
        .outE()
        .otherV()
        .bothE()
        .otherV()
        .bothE()
        .otherV()
        .hasId(p2.value)
        .path()
        .by(t.id)
        .toList();
    const processedPath = await processPaths(paths)
    const {vData, eData} = processedPath
    return makeD3Els(vData, eData)
}

// Returns D3 Formatted elements either outgoing or incoming transactions of user1
async function userTransactions(user1, dir) {
    const p1 = await g.V().hasLabel("User").has("name", user1).id().next()
    let paths
    if (dir === "out")
        paths = await g.V(p1.value)
            .outE().otherV().outE()
            .otherV().bothE().otherV().hasLabel("User").path().by(t.id).toList()
    else
        paths = await g.V(p1.value)
            .outE().otherV().inE()
            .otherV().bothE().otherV().hasLabel("User").path().by(t.id).toList()
    const processedPath = await processPaths(paths)
    const {vData, eData} = processedPath

    return makeD3Els(vData, eData)
}

// Retrieve D3 formatted elements of full graph
export async function getFullGraph() {
    const vData = await g.V().valueMap(true).toList();
    const eData = await g.E().elementMap().toList();
    return makeD3Els(vData, eData);
}

// Given list of paths, produces the list of values for nodes and edges
async function processPaths(paths) {
    const vertexes = new Set(),
        edges = new Set();
    if(paths.length === 0){
        return {vData: [], eData: []}
    }
    paths.forEach(path => {
        let i = 0;
        for (const elem of path.objects) {
            if (i % 2 === 0) vertexes.add(elem);
            else edges.add(elem);
            i++;
        }
    })

    const vList = Array.from(vertexes),
        eList = Array.from(edges);
    const vData = await g.V(vList).valueMap(true).toList();
    const eData = await g.E(eList).elementMap().toList();

    return {vData, eData}
}

// Given lists of values for nodes and edges, format them for D3 Visualization
function makeD3Els(vData, eData) {
    const nodes = vData.map((v) => ({
        id: v.get(t.id),
        label: v.get("name") || v.get("accountId") || String(v.get("id")),
    }));

    const links = eData.map((e) => ({
        source: e.get(direction.out).get(t.id),
        target: e.get(direction.in).get(t.id),
        label: e.has("transactionId")
            ? `$${e.get("transactionId")}->${e.get("amount")}`
            : e.get(t.label),
    }));
    return {nodes, links}
}

function convertTimestampToLong(dateStr) {
    const dt = new Date(dateStr + "T00:00:00Z");
    return Math.floor(dt.getTime() / 1000);
}

function randomInt(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
}

(async () => {
    console.log("Connecting to graph and populating data...");
    await populateGraph(g)
})();

process.on('SIGINT', closeConnection);  // e.g. Ctrl+C
process.on('SIGTERM', closeConnection);  // e.g. Docker stop / kill