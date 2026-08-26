const { app, BrowserWindow } = require('electron')
const path = require('node:path')
const fs = require('node:fs')

const fallbackRenderer = path.join(__dirname, 'renderer', 'index.html')
const packagedRenderer = path.join(__dirname, '../web/dist/index.html')

function createWindow() {
  const window = new BrowserWindow({
    width: 1440,
    height: 900,
    webPreferences: { contextIsolation: true, nodeIntegration: false },
  })

  if (app.isPackaged) {
    window.loadFile(
      process.env.ELECTRON_RENDERER_PATH ||
        (fs.existsSync(packagedRenderer) ? packagedRenderer : fallbackRenderer),
    )
  } else {
    window
      .loadURL(process.env.ELECTRON_RENDERER_URL || 'http://localhost:5173')
      .catch(() => window.loadFile(fallbackRenderer))
  }
}

app.whenReady().then(createWindow)

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})
