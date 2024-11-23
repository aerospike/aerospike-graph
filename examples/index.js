// make a branch of git repo or a fork and then do a pr

const gremlin = require("gremlin");
const traversal = gremlin.process.AnonymousTraversalSource.traversal;
const DriverRemoteConnection = gremlin.driver.DriverRemoteConnection;
const io = gremlin.structure.io;
const { Graph } = gremlin.structure;
const readline = require("readline");

// Connect to the Aerospike Graph Service
const g = traversal().withRemote(
  new DriverRemoteConnection("ws://localhost:8182/gremlin")
);

//Create the readline for looping in the main function
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
});

//Function to load GraphML file from the container
//    Make sure to change it to wherever your graphml file is located in the container (Declared in the docker-compose file under volumes)
async function loadGraphML() {
  try {
    await g.io("/opt/graphml/air-routes-small-latest.graphml").read().iterate();
    console.log("GraphML file loaded successfully");
  } catch (error) {
    console.error("Error loading GraphML file:", error);
  }
}
//Used after executing a function
function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

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
  await delay(3000);
}

async function printAllEdges() {
  const edges = await g.E().toList();
  edges.forEach((edge) => console.log(edge));
  await delay(3000);
}

async function printAllVertexProperties() {
  const props = await g.V().valueMap(true).toList();
  props.forEach((vertex) => console.log(vertex));
  await delay(3000);
}

//Adds a node into the graph based on user input passed through properties
async function addNode(props) {
  console.log("Adding node with properties:", props);
  const node = g
    .addV(props.labelV)
    .property("type", props.type)
    .property("code", props.code)
    .property("icao", props.icao)
    .property("city", props.city)
    .property("desc", props.desc)
    .property("region", props.region)
    .property("runways", props.runways)
    .property("longest", props.longest)
    .property("elev", props.elev)
    .property("country", props.country)
    .property("lat", props.lat)
    .property("lon", props.lon);
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

//Tells you if there are direct flights to airports specified
async function hasDirectFlights() {
  //Prompt User for the Codes
  const fromCode = await new Promise((resolve) => {
    rl.question("Enter the Airport Code to Come From: ", (answer) => {
      resolve(answer);
    });
  });
  const toCode = await new Promise((resolve) => {
    rl.question("Enter the Airport Code to Go To: ", (answer) => {
      resolve(answer);
    });
  });

  //Query to get vertices with fromCode, jump 1 edge out, then check if the out node has the toCode
  const result = await g
    .V()
    .has("airport", "code", fromCode)
    .out()
    .has("code", toCode)
    .toList();
  if (result.length <= 0) {
    console.log("No Direct flights found :(");
  } else {
    console.log("Yes! " + fromCode + " offers direct flights to " + toCode);
  }
  await delay(3000);
}

//Whole ton of nested questions to prompt user for all of the properties in a Airport Node
function promptUserForNode(callback) {
  const properties = {};
  rl.question("Enter node id: ", (id) => {
    properties.id = id;
    rl.question("Enter labelV: ", (labelV) => {
      properties.labelV = labelV;
      rl.question("Enter type: ", (type) => {
        properties.type = type;
        rl.question("Enter code: ", (code) => {
          properties.code = code;
          rl.question("Enter icao: ", (icao) => {
            properties.icao = icao;
            rl.question("Enter city: ", (city) => {
              properties.city = city;
              rl.question("Enter desc: ", (desc) => {
                properties.desc = desc;
                rl.question("Enter region: ", (region) => {
                  properties.region = region;
                  rl.question("Enter runways: ", (runways) => {
                    properties.runways = runways;
                    rl.question("Enter longest: ", (longest) => {
                      properties.longest = longest;
                      rl.question("Enter elev: ", (elev) => {
                        properties.elev = elev;
                        rl.question("Enter country: ", (country) => {
                          properties.country = country;
                          rl.question("Enter lat: ", (lat) => {
                            properties.lat = lat;
                            rl.question("Enter lon: ", (lon) => {
                              properties.lon = lon;
                              //Call the function to the add node, passing in all of the user input
                              addNode(properties).then(() => {
                                callback(); // Call the callback to continue the loop
                              });
                            });
                          });
                        });
                      });
                    });
                  });
                });
              });
            });
          });
        });
      });
    });
  });
}

// Function to handle cases of user input from loop
async function handleUserInput(input) {
  switch (input.trim().toLowerCase()) {
    case "load":
      await loadGraphML();
      break;
    case "pv":
      printAllVertices();
      break;
    case "pe":
      printAllEdges();
      break;
    case "pvp":
      printAllVertexProperties();
      break;
    case "aws":
      await getAirportsWithCode();
      break;
    case "df":
      await hasDirectFlights();
      break;
    case "add":
      promptUserForNode(promptForCommand);
      return;
    case "clear":
      await g.V().drop().iterate();
      console.log("Graph data cleared successfully");
      break;
    case "exit":
      console.log("Exiting application...");
      rl.close();
      process.exit(0);
      break;
    default:
      console.log("Unknown command. Please try again.");
      break;
  }
  promptForCommand();
}
// Function to prompt for user commands
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
