// make a branch of git repo or a fork and then do a pr

const gremlin = require("gremlin");
const traversal = gremlin.process.AnonymousTraversalSource.traversal;
const DriverRemoteConnection = gremlin.driver.DriverRemoteConnection;
const io = gremlin.structure.io;
const { Graph } = gremlin.structure;

// Connect to the Aerospike Graph Service
const g = traversal().withRemote(
  new DriverRemoteConnection("ws://localhost:8182/gremlin")
);

// Function to perform the operations from the python example, used as a test/prototype
//    Quite literally line for line the same. This function is not used in this script
async function performOperations() {
  try {
    // Add a new vertex
    await g
      .addV("foo")
      .property("company", "aerospike")
      .property("scale", "unlimited")
      .iterate();

    // Read back the new vertex
    const v = await g.V().has("company", "aerospike").next();

    // Print out its element map
    console.log("Values:", await g.V(v.value).values().toList());

    // Update a property
    await g.V(v.value).property("scale", "infinite").iterate();

    // Print out the new property
    console.log("Updated:", await g.V(v.value).values().toList());

    // Delete the vertex
    await g.V(v.value).drop().iterate();
  } catch (error) {
    console.error("Error performing operations:", error);
  }
}

async function printAllVertices() {
  const vertices = await g.V().toList();
  vertices.forEach((vertex) => console.log(vertex));
}

async function printAllEdges() {
  const edges = await g.E().toList();
  edges.forEach((edge) => console.log(edge));
}

async function printAllVertexProperties() {
  const props = await g.V().valueMap(true).toList();
  props.forEach((vertex) => console.log(vertex));
}

//Adds a node into the graph based on user input passed through properties
async function addNode(props) {
  console.log("Adding node with properties:", props);
  const node = g
    .addV(props.labelV)
    .property("type", props.type)
    .property("code", props.code);
  await node.next();
  console.log("Node created successfully");
}

//Query for airport with code
async function getAirportsWithCode() {
  //prompt the user for the code
  const code = await new Promise((resolve) => {
    rl.question("Enter the Airport Code: ", (answer) => {
      resolve(answer);
    });
  });
  //Turn the code to a list to print contents
  const result = await g.V().has("code", code).valueMap().toList();
  if (result.length <= 0) {
    console.log("No Airports found");
  } else {
    result?.forEach((vertex) => console.log(vertex));
  }
  await delay(3000);
}

// Function to handle cases of user input from loop

function promptForCommand() {
  console.log(
    "Enter a command:\n" +
      "Load Airport Data ----> load\n" +
      "Add a Node to Graph ----> add\n" +
      "Clear all data in the Graph ----> clear\n" +
      "Close the application (Will not clear data) ----> exit\n" +
      "Print All Vertices in Graph ----> pv\n" +
      "Print All Edges in Graph ----> pe\n" +
      "Print All Vertex Properties ----> pvp\n" +
      "Print All Vertices with Airport Code ----> aws\n" +
      "Check if there is Direct Flights to and From Airport with code ----> df"
  );
  rl.question("", async (input) => {
    try {
      await handleUserInput(input);
    } catch (error) {
      console.error("An error occurred:", error);
      promptForCommand();
    }
  });
}

async function main() {
  promptForCommand();
}

main().catch((error) => console.error("An error occurred in main:", error));