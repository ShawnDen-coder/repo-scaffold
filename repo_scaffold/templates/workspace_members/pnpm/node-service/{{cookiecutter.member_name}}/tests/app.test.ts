import request from "supertest";
import { describe, expect, it } from "vitest";

import { createApp } from "../src/app.js";

describe("health endpoint", () => {
  it("returns ok", async () => {
    const response = await request(createApp()).get("/health");
    expect(response.body).toEqual({ status: "ok" });
  });
});
