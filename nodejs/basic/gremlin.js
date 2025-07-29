import gremlin from "gremlin"

// Import specific Gremlin components for graph traversal and connection
const {traversal} = gremlin.process.AnonymousTraversalSource;
const {DriverRemoteConnection} = gremlin.driver;
const {t, direction} = gremlin.process;
const __ = gremlin.process.statics;
import {P} from "gremlin/lib/process/traversal.js";

// Import required functions and data
import {banks, devices, userNames, HOST, PORT} from "./public/consts.js";
import {randomInt, convertTimestampToLong} from "./index.js";

// Initialize Gremlin connection and graph traversal source
// This creates the main graph traversal object used throughout the application
export const drc = new DriverRemoteConnection(`ws://${HOST}:${PORT}/gremlin`);
export const g = traversal().withRemote(drc);

/**
 * Initializes the graph database with sample data
 * Creates:
 * - User vertices with properties (userId, name, age)
 * - Account vertices with properties (accountId, balance)
 * - Ownership edges between Users and Accounts
 * - Random Transaction edges between Accounts
 * - Fraudulent Hub Nodes
 */
export async function populateGraph() {
    try {
        console.log("Populating graph...");

        // Verify connection by injecting test value
        // Returns 0 if connection is successful
        const check = await g.inject(0).next();
        if (check.value !== 0) {
            console.error("Failed to connect to Gremlin server");
            return;
        }

        // Clear existing vertices before populating
        await g.V().drop().iterate();

        // Create user vertices with properties
        // g.addV("User") - creates vertex with "User" label
        // property() - adds properties to the vertex
        const userVertices = await Promise.all(userNames.map((name, i) => g
            .addV("User")
            .property("userId", `U${i + 1}`)
            .property("name", name)
            .property("age", 25 + randomInt(-6, 45))
            .next()));

        // Create account vertices
        // g.addV("Account") - creates vertex with "Account" label
        // property() - adds accountId and balance properties
        const accountVertices = [];
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

        // Create edges between users and accounts
        // addE("owns") - creates edge with "owns" label
        // from_() - specifies source vertex
        // to() - specifies target vertex
        await Promise.all(userVertices.map((u, i) => g
            .addE("owns")
            .from_(u.value)
            .to(accountVertices[i].value)
            .property("since", `${2020 + randomInt(-15, 5)}`)
            .iterate()));

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
                const year = String(randomInt(2000, 2025))
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

/**
 * Creates given number of fraudulent Hub nodes in graph database
 * @param {Integer} startingVertIndex - Index where new vertexes should be added starting from
 * @param {Integer} startingTransIndex - Index where new transaction edges should be added starting from
 * @param {Integer} numHubs - Number of Hubs to be created
 */
async function generateHubs(startingVertIndex, startingTransIndex, numHubs) {
    let hubsArr = []
    let accountsArr = []

    // Create user vertices with properties
    // g.addV("User") - creates vertex with "User" label
    // property() - adds properties to the vertex
    for (let i = 0; i < numHubs; i++) {
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

    // Create account vertices
    // g.addV("Account") - creates vertex with "Account" label
    // property() - adds accountId and balance properties
    for (let i = 0; i < numHubs; i++) {
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

    // Create edges between users and accounts
    // addE("owns") - creates edge with "owns" label
    // from_() - specifies source vertex
    // to() - specifies target vertex
    for (let i = 0; i < numHubs; i++) {
        await g
            .addE("owns")
            .from_(accountsArr[i].value)
            .to(hubsArr[i].value)
            .property("since", `${2020 + randomInt(-15, 5)}`)
            .iterate()
    }

    //Make Random Large amount of Transactions
    for (let i = 0; i < numHubs; i++) {
        let goonsAmt = randomInt(5, 8)
        let goons = await g.V().hasLabel("Account").sample(goonsAmt).toList()
        for (const goon of goons) {
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

/**
 * Queries all accounts in database and ranks them based on total outgoing transaction amount
 * @param {Integer} amount - top amount of accounts from ranking returned, if null returns whole array
 * @returns {Array} - Array of objects containing accountID, totalAmount of outgoing transactions in $, and reference to owner Vertex
 */
export async function rankMostTraffic(amount = null) {
    const lists = await g.V()
        .hasLabel("Account")
        .project("accountId", "totalAmount", "ownerVert") //make map with keys
        .by("accountId") //fill accountId bin with vertexes accountId prop
        .by(__.coalesce( //run anonymous traversal and grab transactionEdges
            __.outE("Transaction").values("amount").sum(), __.constant(0) //default to 0
        ))
        .by(__.in_("owns")
            .hasLabel("User")
            .limit(1)
            .valueMap(true))
        .toList();

    lists.sort((a, b) => {
        const totalA = a.get("totalAmount")
        const totalB = b.get("totalAmount")
        return totalB - totalA
    })
    if (amount) {
        return lists.slice(0, amount)
    }
    return lists;
}

/**
 * Queries for either all usernames in graph database, or all usernames of users that interact with given username
 * @param {String} name - "" or username in database
 * @returns {Array} - List of username strings
 */
export async function getAllNames(name) {
    if (name === "") {
        return await g.V().hasLabel("User").values("name").toList()
    } else { // Grab all names of people affiliated with user
        return await g.V().has("User", "name", name)
            .out("owns").bothE("Transaction")
            .otherV().in_("owns").hasLabel("User")
            .values("name").dedup().toList()
    }
}

/**
 * Processes raw graph paths into vertex and edge data
 * @param {Array} paths - Array of graph paths
 * @returns {Object} Object containing processed vertex and edge data
 */
async function processPaths(paths) {
    const vertexes = new Set(), edges = new Set();
    if (paths.length === 0) {
        return {vData: [], eData: []}
    }
    paths.forEach(path => {
        let i = 0;
        for (const elem of path.objects) {
            if (i % 2 === 0) vertexes.add(elem); else edges.add(elem);
            i++;
        }
    })

    const vList = Array.from(vertexes), eList = Array.from(edges);
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
export function makeD3Els(vData, eData) {
    const nodes = vData.map(v => {
        const props = Object.fromEntries(Array.from(v.entries()).map(([k, val]) => [k, Array.isArray(val) && val.length === 1 ? val[0] : val]));
        return {
            id: props.id, label: props.name || props.accountId || String(props.id), data: props
        }
    });

    const links = eData.map(e => {
        const excludedKeys = ['IN', 'OUT'];
        let props = Object.fromEntries(Array.from(e.entries())
            .map(([k, val]) => [String(k), Array.isArray(val) && val.length === 1 ? val[0] : val]));

        for (const key of excludedKeys) {
            delete props[key];
        }
        return {
            source: e.get(direction.out).get(t.id),
            target: e.get(direction.in).get(t.id),
            label: e.has("transactionId") ? `$${e.get("transactionId")}->${e.get("amount")}` : e.get(t.label),
            data: props
        }
    });
    return {nodes, links}
}

/**
 * Finds and formats all paths of transactions between two users
 * @param {string} user1 - Name of the first user
 * @param {string} user2 - Name of the second user
 * @returns {Object} D3-formatted graph data showing transaction paths
 */
export async function transactionsBetweenUsers(user1, user2) {
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

/**
 * Retrieves all transactions (incoming or outgoing) for a specific user
 * @param {string} user1 - Name of the user
 * @param {string} dir - Direction of transactions ('in' or 'out')
 * @returns {Object} D3-formatted graph data showing user's transactions
 */
export async function userTransactions(user1, dir) {
    const p1 = await g.V().hasLabel("User").has("name", user1).id().next()
    let paths
    if (dir === "out") {
        paths = await g.V(p1.value)            // Start from user vertex
            .outE().otherV().outE()            // Follow outgoing transaction path
            .otherV().bothE().otherV()         // Continue to connected vertices
            .hasLabel("User")                  // End at user vertices
            .path().by(t.id).toList()          // Collect path with IDs
         }
    else {
        paths = await g.V(p1.value)            // Start from user vertex
            .outE().otherV().inE()             // Follow incoming transaction path
            .otherV().bothE().otherV()         // Continue to connected vertices
            .hasLabel("User")                  // End at user vertices
            .path().by(t.id).toList()          // Collect path with IDs
         }
    const processedPath = await processPaths(paths)
    const {vData, eData} = processedPath

    return makeD3Els(vData, eData)
}