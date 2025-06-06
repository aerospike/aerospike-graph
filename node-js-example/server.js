import { app } from "./index.js";
import {drc, populateGraph} from "./gremlin.js";
import { HTTP_PORT } from "./public/consts.js";

let server;

async function bootstrap() {
    try {
        console.log("Connecting to graph…");
        await populateGraph();
        server = app.listen(HTTP_PORT, () => {
            console.log(`Server listening on http://localhost:${HTTP_PORT}`);
        });
    } catch (e) {
        console.error("Failed initial graph population:", e);
        process.exit(1);
    }
}

bootstrap();

process.on("SIGINT", () => {
    console.log("SIGINT called")
    drc.close().then(() =>
        {
            if (server) server.close(() => process.exit(0));
        }
    )
});
process.on("SIGTERM", () => {
    console.log("SIGTERM called")
    drc.close().then(() =>
    {
        if (server) server.close(() => process.exit(0));
    }
    )
});
