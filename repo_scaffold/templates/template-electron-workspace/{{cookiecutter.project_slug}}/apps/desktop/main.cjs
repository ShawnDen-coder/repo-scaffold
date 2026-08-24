const { app, BrowserWindow } = require('electron')

app.whenReady().then(() => {
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
})
