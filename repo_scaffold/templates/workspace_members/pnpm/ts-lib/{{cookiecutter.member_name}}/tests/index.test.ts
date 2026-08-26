import { describe, expect, it } from "vitest";

describe("{{ cookiecutter.package_name }}", () => {
  it("loads its public entry point", async () => {
    await expect(import("../src/index.js")).resolves.toEqual({});
  });
});
