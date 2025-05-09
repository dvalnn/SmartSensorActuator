import {
  Application,
  ThingDescription,
  ThingModel,
  ThingModelHelpers,
} from "../deps.ts";
import { initMQTTConnector } from "./connectors/mqttConnector.ts";
import { createAppRouter } from "./routes/index.ts";
import { HTTP_HOSTNAME, HTTP_PORT } from "./config/config.ts";

export function startApp(): void {
  // Shared state: Map<model, Map<uuid, ThingDescription>>
  const hostedThings = new Map<string, Map<string, ThingDescription>>();
  const hostedModels = new Map<string, ThingModel>();
  const tmTools = new ThingModelHelpers();

  // Initialize MQTT handler
  initMQTTConnector(tmTools, hostedModels, hostedThings);

  // Initialize HTTP server
  const router = createAppRouter(hostedThings, hostedModels);
  const app = new Application();
  app.use(router.routes());
  app.use(router.allowedMethods());

  console.log(`HTTP server listening on port ${HTTP_PORT}`);
  app.listen({ hostname: HTTP_HOSTNAME, port: HTTP_PORT });
}
