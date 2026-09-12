const { app, BrowserWindow, shell, ipcMain, dialog } = require('electron');
const path = require('path');
const { spawn, execSync } = require('child_process');

let mainWindow;
let backendProcess = null;

function killBackend() {
  if (!backendProcess) return;
  try {
    const pid = backendProcess.pid;
    if (process.platform === 'win32') {
      // Windows 下用 taskkill 强制终止整个进程树
      execSync(`taskkill /pid ${pid} /T /F`, { stdio: 'ignore' });
    } else {
      backendProcess.kill('SIGTERM');
    }
  } catch (e) {
    // 进程可能已经退出，忽略错误
  }
  backendProcess = null;
}

function startBackend() {
  return new Promise((resolve, reject) => {
    let backendExe;
    let backendCwd;

    if (app.isPackaged) {
      backendExe = path.join(process.resourcesPath, 'backend.exe');
      backendCwd = path.dirname(backendExe);
      console.log('Starting backend:', backendExe);
      console.log('Working dir:', backendCwd);
    } else {
      backendExe = process.platform === 'win32' ? 'python' : 'python3';
      backendCwd = path.join(__dirname, '..', '..', 'backend');
      console.log('Starting backend with Python, cwd:', backendCwd);
    }

    const args = app.isPackaged ? [] : ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000'];

    backendProcess = spawn(backendExe, args, {
      cwd: backendCwd,
      stdio: ['ignore', 'pipe', 'pipe'],
      detached: false,
      env: { ...process.env }
    });

    let started = false;
    let output = '';

    backendProcess.stdout.on('data', (data) => {
      const str = data.toString();
      output += str;
      console.log('[Backend stdout]:', str);
      if (!started && (output.includes('Uvicorn running') || output.includes('Application startup complete'))) {
        started = true;
        console.log('Backend server started successfully');
        resolve();
      }
    });

    backendProcess.stderr.on('data', (data) => {
      console.error('[Backend stderr]:', data.toString());
    });

    backendProcess.on('error', (err) => {
      console.error('Failed to start backend:', err);
      reject(err);
    });

    backendProcess.on('close', (code) => {
      console.log(`Backend process exited with code ${code}`);
    });

    setTimeout(() => {
      if (!started) {
        console.log('Backend start timeout, proceeding anyway...');
        resolve();
      }
    }, 20000);
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1000,
    minHeight: 700,
    frame: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false
    },
    title: 'GitHub仓库分析器',
    show: false,
    autoHideMenuBar: true
  });

  ipcMain.on('window:minimize', () => {
    if (mainWindow) mainWindow.minimize();
  });

  ipcMain.on('window:toggleMaximize', () => {
    if (mainWindow) {
      if (mainWindow.isMaximized()) {
        mainWindow.unmaximize();
      } else {
        mainWindow.maximize();
      }
    }
  });

  ipcMain.on('window:close', () => {
    if (mainWindow) mainWindow.close();
  });

  ipcMain.handle('window:isMaximized', () => {
    return mainWindow ? mainWindow.isMaximized() : false;
  });

  // 弹出系统目录选择器，返回选中的绝对路径（取消则返回 null）
  ipcMain.handle('dialog:selectDirectory', async () => {
    if (!mainWindow) return null;
    const result = await dialog.showOpenDialog(mainWindow, {
      title: '选择保存目录',
      properties: ['openDirectory', 'createDirectory'],
    });
    if (result.canceled || result.filePaths.length === 0) return null;
    return result.filePaths[0];
  });

  mainWindow.setMenuBarVisibility(false);

  if (!app.isPackaged) {
    mainWindow.loadURL('http://127.0.0.1:5173');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, '..', 'dist', 'index.html'));
  }

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });
}

app.whenReady().then(async () => {
  try {
    await startBackend();
  } catch (err) {
    console.error('Failed to start backend:', err);
  }
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  killBackend();
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  killBackend();
});
