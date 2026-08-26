import { describe, expect, it } from "vitest";

import { createProgram } from "../src/program.js";

describe("createProgram", () => {
  it("uses the generated binary name", () => {
    expect(createProgram().name()).toBe("{{ cookiecutter.project_slug }}");
  });
});
