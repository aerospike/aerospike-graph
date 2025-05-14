// Holds main server/app and gremlin logic

import gremlin from "gremlin"
import express from "express"
import path, {dirname} from "path"
import {fileURLToPath} from 'url';

import {banks, devices, userNames} from "./public/consts.js";
import {P} from "gremlin/lib/process/traversal.js";

// Gremlin imports
const {traversal} = gremlin.process.AnonymousTraversalSource;
const {DriverRemoteConnection} = gremlin.driver;
const {t, direction} = gremlin.process;
const __ = gremlin.process.statics;

// Connection Variables
const HOST = "localhost";
const PORT = 8182;
const HTTP_PORT = 5000;
let serverFlag = false;
// Create Express app
const app = express();
const server = app.listen(HTTP_PORT, () =>
    serverFlag = true
);

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);


export const drc = new DriverRemoteConnection(
    `ws://${HOST}:${PORT}/gremlin`
);

export const g = traversal().withRemote(drc);

app.use(express.static(path.join(__dirname, "public"), {
    dotfiles: 'allow',
}));

app.get("/ping", (req, res) => res.send("pong"));
app.get("/", (req, res) => {
    res.sendFile(path.join(__dirname, "public", "index.html"));
});

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
                const vert  =  await g.V()
                    .has("accountId",id)
                    .inE("owns")                             // traverse incoming “owns” edges → User
                    .otherV()
                    .hasLabel("User")
                    .valueMap(true)
                    .toList()
                const name = vert[0].get("name")[0]
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

app.get("/names", async (req, res) => {
    try {
        const names = await g.V().hasLabel("User").values("name").toList()
        res.json({names});
    } catch (e) {
        console.error("Error in /graph:", e);
        res.status(500).json({error: e.message});
    }
});

app.get("/hub", async (req, res) => {
    try {
        const hub = await grabMostFraudulent()
        res.json({hub});
    } catch (e) {
        console.error("Error in /graph:", e);
        res.status(500).json({error: e.message});
    }
});
// Shut down server and clear graph data
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
        const accountVertices = [];
        const userVertices = await Promise.all(
            userNames.map((name, i) =>
                g
                    .addV("User")
                    .property("userId", `U${i + 1}`)
                    .property("name", name)
                    .property("age", 25 + randomInt(-6, 45))
                    .next()
            )
        );


        for (let i = 0; i < userNames.length; i++) {
            const bal = randomInt(500, 10000);
            const bank = banks[randomInt(0, banks.length - 1)]
            // Insert one Account vertex, then await it before moving on
            const result = await g
                .addV("Account")
                .property("accountId", `A${i + 1}`)
                .property("balance", bal)
                .property("bank", bank)
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
                    .property("since", `${2020 + randomInt(-15, 5)}`)
                    .iterate()
            )
        );

        // Create random transactions
        let transAmt = 0
        for (const account of accountVertices) {
            const transactions = randomInt(7, 14)
            for (let i = 0; i < transactions; i++) {
                transAmt++
                const toAcc = await g.V().hasLabel("Account").hasId(P.neq(account.id)).sample(1).toList();
                const from = account.value;
                const to = toAcc[0];
                const amt = randomInt(1, 1001);
                const txId = `T${i}`;
                const type = Math.random() < 0.5 ? "debit" : "credit";
                const year = String(randomInt(2000,2025))
                const month = String(randomInt(1, 12)).padStart(2, "0");
                const day = String(randomInt(1, 28)).padStart(2, "0");
                const date = `${year}-${month}-${day}`;
                const device = devices[randomInt(0, devices.length - 1)];
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
        }

        await generateHubs(userNames.length, transAmt, 2)
        console.log("Graph population complete.");
    } catch (error) {
        console.error("Error populating graph:", error);
    }
}

//Creates hub nodes (dense nodes) that could be fraudulent actors
async function generateHubs(startingVertIndex, startingTransIndex, numHubs){
    let hubsArr = []
    let accountsArr = []

    //Make Hub Vertices
    for(let i = 0; i<numHubs; i++){
        const bal = randomInt(90000, 250000);
        const bank = banks[randomInt(0, banks.length - 1)]
        const vert = await g
            .addV("User")
            .property("userId", `U${startingVertIndex + i + 1}`)
            .property("name", "ShadyMan" + i)
            .property("age", 25 + randomInt(-6, 45))
            .next()
        accountsArr.push(vert)
    }

    //Make accounts
    for(let i = 0; i<numHubs; i++){
        const bal = randomInt(90000, 250000);
        const bank = banks[randomInt(0, banks.length - 1)]
        const vert = await g
            .addV("Account")
            .property("accountId", `A${startingVertIndex + i + 1}`)
            .property("balance", bal)
            .property("bank", bank)
            .next()
        hubsArr.push(vert)
    }

    //Connect accounts and Shady people
    for(let i = 0; i < numHubs; i++){
        await g
            .addE("owns")
            .from_(accountsArr[i].value)
            .to(hubsArr[i].value)
            .property("since", `${2020 + randomInt(-15, 5)}`)
            .iterate()
    }

    //Make Transactions
    for (let i = 0; i < numHubs; i++) {
        let goonsAmt = randomInt(5, 8)
        let goons = await g.V().hasLabel("Account").sample(goonsAmt).toList()
        for (let k = 0; k < goons.length; k++) {
            const goon = goons[k]
            for (let j = 0; j < randomInt(9, 25); j++) {
                const amt = randomInt(5000, 30000);
                const txId = `T${startingTransIndex + i + 1}`;
                const type = Math.random() < 0.5 ? "debit" : "credit";
                const year = String(randomInt(2000, 2025))
                const month = String(randomInt(1, 12)).padStart(2, "0");
                const day = String(randomInt(1, 28)).padStart(2, "0");
                const date = `${year}-${month}-${day}`;
                const device = devices[randomInt(0, devices.length - 1)];
                await g
                    .addE("Transaction")
                    .from_(hubsArr[i].value)
                    .to(goon)
                    .property("transactionId", txId)
                    .property("amount", amt)
                    .property("device", device)
                    .property("type", type)
                    .property("timestamp", convertTimestampToLong(date))
                    .iterate();
            }
        }
    }

}

//Returns the given top amount of accounts in terms of outgoing
// null amount gives whole list of vertices
async function poorMansPageRank(amount = null){
    //const accounts = g.V().hasLabel("Account").toList();
    const lists = await g.V()
        .hasLabel("Account")
        .project("accountId","totalAmount") //make map with keys
        .by("accountId") //fill accountId bin with vertexes accountId prop
        .by(__.coalesce( //run anonymous traversal and grab transactionEdges
            __.outE("Transaction").values("amount").sum(),
            __.constant(0)//default to 0
        ))
        .toList();

    lists.sort((a, b) => {
        const totalA = a.get("totalAmount")
        const totalB = b.get("totalAmount")
        return totalB - totalA
    })
    if(amount){
        return lists.slice(0, amount)
    }
    return lists;
}

async function grabMostFraudulent(){
    const lists = await poorMansPageRank(null)
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

// Given list of paths, produces the list of values for nodes and edges
async function processPaths(paths) {
    const vertexes = new Set(),
        edges = new Set();
    if (paths.length === 0) {
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

function convertTimestampToLong(dateStr) {
    const dt = new Date(dateStr + "T00:00:00Z");
    return Math.floor(dt.getTime() / 1000);
}

function randomInt(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
}

(async () => {
    try {
        console.log("Connecting to graph...");
        await populateGraph(g);

        if(serverFlag){
            console.log(`Server listening on http://localhost:${HTTP_PORT}`)
        }
    } catch (e) {
        console.error("Failed initial graph population:", e);
    }
})();

//process.on('SIGINT', closeConnection);  // e.g. Ctrl+C
//process.on('SIGTERM', closeConnection);  // e.g. Docker stop / kill