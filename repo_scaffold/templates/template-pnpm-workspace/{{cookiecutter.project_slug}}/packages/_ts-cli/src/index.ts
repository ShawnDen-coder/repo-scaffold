import { Command } from 'commander'

const program = new Command()

program
  .name('{{cookiecutter.package_slug}}')
  .description('{{cookiecutter.description}}')
  .version('0.1.0')

program
  .command('hello')
  .description('Say hello')
  .option('-n, --name <name>', 'Name to greet', 'World')
  .action((options) => {
    console.log(`Hello, ${options.name}!`)
  })

program.parse()
