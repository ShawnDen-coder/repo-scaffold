import { createApp } from "./app.js";

const port = Number(process.env.PORT ?? 3000);

createApp().listen(port, () => {
  console.log(`Service listening on port ${port}`);
});

export { createApp } from "./app.js";
