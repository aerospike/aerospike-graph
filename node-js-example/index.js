/**
 * Node JS Example using Aerospike Graph
 * This file implements a server that manages a graph database of users, accounts, and transactions
 * to demonstrate fraud detection patterns using graph traversal.
 */

// Import required dependencies
import gremlin from "gremlin"
import express from "express"
import path, {dirname} from "path"
import {fileURLToPath} from 'url';

// Import specific Gremlin components for graph traversal and connection
const {traversal} = gremlin.process.AnonymousTraversalSource;
const {DriverRemoteConnection} = gremlin.driver;
const {t, direction} = gremlin.process;

// Connection Variables
const HOST = "localhost";
const PORT = 8182;  // Gremlin server port
const HTTP_PORT = 5000;  // Express server port

// Initialize Express application
const app = express();
const server = app.listen(HTTP_PORT, () =>
    console.log(`Server listening on http://localhost:${HTTP_PORT}`)
);

// Setup ES module compatibility for __dirname
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Initialize Gremlin connection and graph traversal source
// This creates the main graph traversal object used throughout the application
export const drc = new DriverRemoteConnection(
    `ws://${HOST}:${PORT}/gremlin`
);
export const g = traversal().withRemote(drc);

// Route handlers
// Serve the main application page
app.get("/", (req, res) => {
    res.sendFile(path.join(__dirname, "public", "index.html"));
});

/**
 * API endpoint to fetch graph data based on different query parameters
 * Supports different view modes:
 * - home: full graph view
 * - outgoing: transactions originating from a user
 * - incoming: transactions received by a user
 * - between: transactions between two users (default)
 */
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

// Serve static files from public directory
app.use(express.static(path.join(__dirname, "public"), {
    dotfiles: 'allow',
}));

// Sample user data for populating the graph
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

/**
 * Gracefully shuts down the server and clears graph data
 * Triggered on SIGINT and SIGTERM signals
 */
async function closeConnection() {
    try {
        console.log("Closing connection...");
        const check = await g.inject(0).next();
        if (check.value === 0) {
            await g.V().drop().iterate();
            await drc.close();
            console.log("Graph Cleared")
        }
        server.close(() => process.exit(0));
        console.log("Connection Closed!");
    } catch (error) {
        console.error("Error closing connection:", error);
    }
}

/**
 * Initializes the graph database with sample data
 * Creates:
 * - User vertices with properties (userId, name, age)
 * - Account vertices with properties (accountId, balance)
 * - Ownership edges between Users and Accounts
 * - Random Transaction edges between Accounts
 */
async function populateGraph() {
    try {
        // Clear existing vertices before populating
        // g.V() selects all vertices
        // drop() removes them from the graph
        await g.V().drop().iterate();

        // Verify connection by injecting test value
        // Returns 0 if connection is successful
        const check = await g.inject(0).next();

        // Create user vertices with properties
        // g.addV("User") - creates vertex with "User" label
        // property() - adds properties to the vertex
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

        // Create account vertices
        // g.addV("Account") - creates vertex with "Account" label
        // property() - adds accountId and balance properties
        const balances = [
            5000, 3000, 4000, 2000, 6000, 7000, 8000, 9000, 10000, 11000,
        ];
        const accountVertices = [];
        for (let i = 0; i < balances.length; i++) {
            const bal = balances[i];
            const result = await g
                .addV("Account")
                .property("accountId", `A${i + 1}`)
                .property("balance", bal)
                .next();
            accountVertices.push(result);
        }

        // Create edges between users and accounts
        // addE("owns") - creates edge with "owns" label
        // from_() - specifies source vertex
        // to() - specifies target vertex
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

/**
 * Finds and formats all paths of transactions between two users
 * @param {string} user1 - Name of the first user
 * @param {string} user2 - Name of the second user
 * @returns {Object} D3-formatted graph data showing transaction paths
 */
async function transactionsBetweenUsers(user1, user2) {
    if (user1 === user2) { // edge case where user chooses 2 of the same user
        return {nodes: [], links: []};
    }
    const p1 = await g.V().has("User", "name", user2).id().next();
    const p2 = await g.V().has("User", "name", user1).id().next();
    const paths = await g
        .V(p1.value)          // Start from user2's vertex
        .outE()               // Get outgoing edges
        .otherV()             // Move to connected vertices
        .bothE()              // Get both incoming and outgoing edges
        .otherV()             // Move to connected vertices
        .bothE()              // Get both incoming and outgoing edges
        .otherV()             // Move to connected vertices
        .hasId(p2.value)      // Filter for paths ending at user1
        .path()               // Collect the entire path
        .by(t.id)             // Store vertex/edge IDs in path
        .toList();            // Convert to list
    const processedPath = await processPaths(paths)
    const {vData, eData} = processedPath
    return makeD3Els(vData, eData)
}

/**
 * Retrieves all transactions (incoming or outgoing) for a specific user
 * @param {string} user1 - Name of the user
 * @param {string} dir - Direction of transactions ('in' or 'out')
 * @returns {Object} D3-formatted graph data showing user's transactions
 */
async function userTransactions(user1, dir) {
    const p1 = await g.V().hasLabel("User").has("name", user1).id().next()
    let paths
    if (dir === "out")
        paths = await g.V(p1.value)            // Start from user vertex
            .outE().otherV().outE()            // Follow outgoing transaction path
            .otherV().bothE().otherV()         // Continue to connected vertices
            .hasLabel("User")                  // End at user vertices
            .path().by(t.id).toList()          // Collect path with IDs
    else
        paths = await g.V(p1.value)            // Start from user vertex
            .outE().otherV().inE()             // Follow incoming transaction path
            .otherV().bothE().otherV()         // Continue to connected vertices
            .hasLabel("User")                  // End at user vertices
            .path().by(t.id).toList()          // Collect path with IDs
    const processedPath = await processPaths(paths)
    const {vData, eData} = processedPath

    return makeD3Els(vData, eData)
}

/**
 * Retrieves the complete graph data
 * @returns {Object} D3-formatted data containing all nodes and edges
 */
export async function getFullGraph() {
    const vData = await g.V().valueMap(true).toList();
    const eData = await g.E().elementMap().toList();
    return makeD3Els(vData, eData);
}

/**
 * Processes raw graph paths into vertex and edge data
 * @param {Array} paths - Array of graph paths
 * @returns {Object} Object containing processed vertex and edge data
 */
async function processPaths(paths) {
    const vertexes = new Set(),
        edges = new Set();
    if (paths.length === 0) {
        return {vData: [], eData: []}
    }
    paths.forEach(path => {
        let i = 0;
        for (const elem of path.objects) {
            if (i % 2 === 0) vertexes.add(elem);  // Even indices are vertices
            else edges.add(elem);                  // Odd indices are edges
            i++;
        }
    })

    // Get full property maps for vertices and edges
    const vList = Array.from(vertexes),
        eList = Array.from(edges);
    const vData = await g.V(vList).valueMap(true).toList();
    const eData = await g.E(eList).elementMap().toList();

    return {vData, eData}
}

/**
 * Converts raw graph data into D3-compatible format
 * @param {Array} vData - Array of vertex data
 * @param {Array} eData - Array of edge data
 * @returns {Object} Formatted data for D3 visualization
 */
function makeD3Els(vData, eData) {
    const nodes = vData.map(v => {
        const props = Object.fromEntries(
            Array.from(v.entries()).map(([k, val]) => [
                k,
                Array.isArray(val) && val.length === 1 ? val[0] : val
            ])
        );
        return {
            id: props.id,
            label: props.name || props.accountId || String(props.id),
            data: props
        }
    });

    const links = eData.map(e => {
        const excludedKeys = ['IN', 'OUT'];
        let props = Object.fromEntries(
            Array.from(e.entries())
                .map(([k, val]) => [String(k),
                    Array.isArray(val) && val.length === 1 ? val[0] : val
                ])
        );

        for (const key of excludedKeys) {
            delete props[key];
        }
        return {
            source: e.get(direction.out).get(t.id),
            target: e.get(direction.in).get(t.id),
            label: e.has("transactionId")
                ? `$${e.get("transactionId")}->${e.get("amount")}`
                : e.get(t.label),
            data: props
        }
    });
    return {nodes, links}
}

/**
 * Utility function to convert date string to Unix timestamp
 * @param {string} dateStr - Date string in YYYY-MM-DD format
 * @returns {number} Unix timestamp in seconds
 */
function convertTimestampToLong(dateStr) {
    const dt = new Date(dateStr + "T00:00:00Z");
    return Math.floor(dt.getTime() / 1000);
}

/**
 * Utility function to generate random integer within range
 * @param {number} min - Minimum value (inclusive)
 * @param {number} max - Maximum value (inclusive)
 * @returns {number} Random integer
 */
function randomInt(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
}

// Initialize the graph database when the application starts
(async () => {
    console.log("Connecting to graph, clearing existing data and populating data...");
    await populateGraph(g)
})();

// Setup graceful shutdown handlers
process.on('SIGINT', closeConnection);  // Handle Ctrl+C
process.on('SIGTERM', closeConnection); // Handle Docker stop/kill