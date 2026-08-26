import { Command } from "commander";

export function createProgram(): Command {
  const program = new Command();

  program
    .name("{{ cookiecutter.project_slug }}")
    .description("{{ cookiecutter.description }}")
    .version("0.1.0");

  program
    .command("hello")
    .description("Print a greeting.")
    .option("-n, --name <name>", "Name to greet.", "World")
    .action((options: { name: string }) => {
      console.log(`Hello, ${options.name}!`);
    });

  return program;
}
