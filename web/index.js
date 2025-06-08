const { app, BrowserWindow } = require('electron');
const path = require('path');
const { exec } = require('child_process');
const http = require('http');
const { ipcMain } = require('electron');
const { spawn } = require('child_process');
let serverProcess;
let mainWindow;

function checkServerReady(url, callback) {
  const req = http.get(url, res => {
    callback(true);
  });
  req.on('error', () => {
    callback(false);
  });
}

function waitForServer(url, onReady) {
  const interval = setInterval(() => {
    checkServerReady(url, ready => {
      if (ready) {
        clearInterval(interval);
        onReady();
      }
    });
  }, 200);
}

function createWindow() {
    mainWindow = new BrowserWindow({
    width: 1500,
    height: 1200,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  });
  // 先加载本地 loading 页面
  mainWindow.loadFile(path.join(__dirname, 'loading.html'));
  const isDev = !app.isPackaged;
  const root_path = process.resourcesPath;
  const exePath = isDev
    ? path.join(__dirname, '..', 'MousePupilAIbackend')
    : path.join(root_path, "..","..","..",'MousePupilAIbackend');
  mainWindow.webContents.send('server-log',`[server_path]: ${exePath}`);
  console.log(exePath)
  serverProcess = spawn(exePath, [], {
    cwd: path.dirname(exePath),
    stdio: ['ignore', 'pipe', 'pipe']
  });
  serverProcess.stdout.on('data', data => {
  if (mainWindow && mainWindow.webContents) {
    mainWindow.webContents.send('server-log', `[stdout]: ${data}`);
    }
  });

  serverProcess.stderr.on('data', data => {
  if (mainWindow && mainWindow.webContents) {
    mainWindow.webContents.send('server-log', `[stderr]: ${data}`);
    }
  });

  serverProcess.on('exit', (code, signal) => {
  if (mainWindow && mainWindow.webContents) {
    mainWindow.webContents.send('server-log', `[server exited] code: ${code}, signal: ${signal}`);
    }
  });



  // 检查服务端口是否可用
  waitForServer('http://localhost:28989', () => {
    mainWindow.loadURL('http://localhost:28989');
  });

  mainWindow.on('closed', () => {
    if (serverProcess) serverProcess.kill();
    mainWindow = null;
  });
}

app.whenReady().then(createWindow);
app.on('window-all-closed', () => app.quit());