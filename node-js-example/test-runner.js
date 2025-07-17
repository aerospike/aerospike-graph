import { spawn } from "child_process";
import { setTimeout } from "timers/promises";

let serverProcess;

async function runTests() {
  try {
    console.log("Starting server...");

    // Start the server
    serverProcess = spawn("node", ["server.js"], {
      stdio: ["inherit", "inherit", "inherit"],
      env: { ...process.env, NODE_ENV: "test" },
    });

    // Wait for server to start up
    await setTimeout(3000);

    console.log("Running Playwright tests...");

    // Run Playwright tests
    const playwrightProcess = spawn("npx.cmd", ["playwright", "test"], {
      stdio: ["inherit", "inherit", "inherit"],
      shell: true,
    });

    // Wait for Playwright tests to complete
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
    // Clean up server process
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

// Handle cleanup on script termination
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
