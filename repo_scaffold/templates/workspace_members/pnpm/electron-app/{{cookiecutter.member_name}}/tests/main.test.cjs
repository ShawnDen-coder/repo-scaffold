const test = require('node:test')
const assert = require('node:assert/strict')
const fs = require('node:fs')

test('Electron entry point exists', () => {
  assert.equal(fs.existsSync('main.cjs'), true)
})
