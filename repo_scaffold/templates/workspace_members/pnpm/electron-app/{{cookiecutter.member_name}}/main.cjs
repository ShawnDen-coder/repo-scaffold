const { app, BrowserWindow } = require('electron')

function createWindow() {
  const window = new BrowserWindow({
    width: 1440,
    height: 900,
    webPreferences: { contextIsolation: true, nodeIntegration: false },
  })

  if (app.isPackaged) {
    window.loadFile(`${__dirname}/../web/dist/index.html`)
  } else {
    window.loadURL(process.env.ELECTRON_RENDERER_URL || 'http://localhost:5180')
  }
}

app.whenReady().then(createWindow)

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})
