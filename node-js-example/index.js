/**
 * Node JS Example using Aerospike Graph
 * This file implements a server that manages a graph database of users, accounts, and transactions
 * to demonstrate fraud detection patterns using graph traversal.
 */
import express from "express"
import path, {dirname} from "path"
import {fileURLToPath} from 'url';
import {HTTP_PORT} from "./public/consts.js";

// Gremlin Function Imports
import {populateGraph, userTransactions, transactionsBetweenUsers, getAllNames, rankMostTraffic} from "./gremlin.js";


// Initialize Express App
let serverFlag = false;
const app = express();
export const server = app.listen(HTTP_PORT, () =>
    serverFlag = true
);

// Setup ES module compatibility for __dirname
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Serve the main application page
app.use(express.static(path.join(__dirname, "public"), {
    dotfiles: 'allow',
}));

app.get("/", (req, res) => {
    res.sendFile(path.join(__dirname, "public", "index.html"));
});

app.get("/ping", (req, res) => {
    console.log("pong")
    res.json("pong")
});

/**
 * API endpoint to fetch graph data based on different query parameters
 * Supports different view modes:
 * - hub: full graph view of most likely fraudulent node
 * - outgoing: transactions originating from a user
 * - incoming: transactions received by a user
 * - between: transactions between two users (default)
 */
app.get("/graph", async (req, res) => {
    try {
        let newGraph

        const {routeKey = 'between', user1, user2} = req.query;
        switch (routeKey) {
            case "outgoing":
                newGraph = await userTransactions(user1, "out");
                break;
            case "hub":
                const fraud = await grabMostFraudulent()
                const increase = fraud.increase.toFixed(2)
                const id = (fraud.fraudVert.get("accountId"))
                const vert  =  fraud.fraudVert.get("ownerVert")
                const name = vert.get("name")[0]
                const state = {
                    userVert: vert,
                    name: name,
                    increase,
                    id
                }
                const {nodes, links} = await userTransactions(name, "out");
                newGraph = {nodes, links, state, stateName: "hub"}
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

// API Endpoint to retreive list of names in the Graph DB
app.get("/names", async (req, res) => {
    try {
        const {name} = req.query;
        const names = await getAllNames(name)
        res.json({names});
    } catch (e) {
        console.error("Error in /graph:", e);
        res.status(500).json({error: e.message});
    }
});

// API Endpoint to return list of vertices in order of most fraudulent to least with increase of mean outgoing transactions
app.get("/hub", async (req, res) => {
    try {
        const hub = await grabMostFraudulent()
        res.json({hub});
    } catch (e) {
        console.error("Error in /graph:", e);
        res.status(500).json({error: e.message});
    }
});

// Returns sorted list of vertices from most likely fraudulent to least based on outgoing transactions
async function grabMostFraudulent(){
    const lists = await rankMostTraffic(null)
    const amounts = lists.map(item => item.get("totalAmount"));

    const n  = lists.length;
    const q3 = amounts[Math.floor(n * 0.25)];
    const q1 = amounts[Math.ceil(n * 0.75)];
    const iqr = q3 - q1;

    const lowerFence = q1 - 1.5 * iqr;
    const upperFence = q3 + 1.5 * iqr;

    const filtered = amounts.filter(x => x >= lowerFence && x <= upperFence);
    const mean =
        filtered.reduce((sum, x) => sum + x, 0) / filtered.length;
    return {fraudVert: lists[0], increase: amounts[0]/mean}
}

export function convertTimestampToLong(dateStr) {
    const dt = new Date(dateStr + "T00:00:00Z");
    return Math.floor(dt.getTime() / 1000);
}

export function randomInt(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
}

/**
 * Shuts down the server and clears graph data
 * Triggered on SIGINT and SIGTERM signals
 */
async function closeConnection() {
    try {
        console.log("Closing connection...");
        server.close(() => process.exit(0));
        console.log("Connection Closed!");
    } catch (error) {
        console.error("Error closing connection:", error);
    }
}

// Initialize the graph database when the application starts
if (process.env.NODE_ENV !== "test") {
    (async () => {
        try {
            console.log("Connecting to graph...");
            await populateGraph();
            if (serverFlag) {
                console.log(`Server listening on http://localhost:${HTTP_PORT}`)
            }
        } catch (e) {
            console.error("Failed initial graph population:", e);
        }
    })();
}
process.on('SIGINT', closeConnection);
process.on('SIGTERM', closeConnection);
