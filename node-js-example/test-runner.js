import { spawn } from "cross-spawn";
import { setTimeout } from "timers/promises";

let serverProcess;

function waitForGraphPopulation(serverProcess) {
  return new Promise((resolve, reject) => {
    let outputBuffer = "";

    const timeout = setTimeout(20000).then(() =>{
      reject(
          new Error('Timeout waiting for "Graph population complete." message')
      );
    })

    serverProcess.stdout.on("data", (data) => {
      const output = data.toString();
      process.stdout.write(output); // Still show the output in console
      outputBuffer += output;

      if (outputBuffer.includes("Graph population complete.")) {
        clearTimeout(timeout);
        resolve();
      }
    });

    serverProcess.on("error", (error) => {
      clearTimeout(timeout);
      reject(new Error(`Server process error: ${error.message}`));
    });

    serverProcess.on("exit", (code) => {
      clearTimeout(timeout);
      if (code !== 0) {
        reject(
          new Error(
            `Server exited with code ${code} before graph population completed`
          )
        );
      }
    });
  });
}

async function runTests() {
  try {
    console.log("Starting server...");

    serverProcess = spawn("node", ["server.js"], {
      stdio: ["inherit", "pipe", "pipe"],
      env: { ...process.env, NODE_ENV: "test" },
    });

    await waitForGraphPopulation(serverProcess);

    console.log("Running Playwright tests...");

    const playwrightProcess = spawn("npx", ["playwright", "test"], {
      stdio: "inherit",
    });

    await new Promise((resolve, reject) => {
      playwrightProcess.on("close", (code) => {
        if (code === 0) {
          console.log("Tests completed successfully");
          resolve();
        } else {
          console.log(`Tests failed with exit code ${code}`);
          reject(new Error(`Tests failed with exit code ${code}`));
        }
      });
    });
  } catch (error) {
    console.error("Test execution failed:", error);
    process.exit(1);
  } finally {
    if (serverProcess) {
      console.log("Stopping server...");
      serverProcess.kill("SIGTERM");
      await setTimeout(1000);
      if (!serverProcess.killed) {
        serverProcess.kill("SIGKILL");
      }
    }
  }
}

process.on("SIGINT", () => {
  console.log("Received SIGINT, cleaning up...");
  if (serverProcess) {
    serverProcess.kill("SIGTERM");
  }
  process.exit(0);
});

process.on("SIGTERM", () => {
  console.log("Received SIGTERM, cleaning up...");
  if (serverProcess) {
    serverProcess.kill("SIGTERM");
  }
  process.exit(0);
});

runTests();
