const { app, BrowserWindow, Menu, dialog, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');

let mainWindow;

// Disable GPU acceleration to prevent crashes
app.disableHardwareAcceleration();

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    },
    show: false,
    backgroundColor: '#1a1a2e'
  });

  mainWindow.loadFile('index.html');

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  if (process.argv.includes('--dev')) {
    mainWindow.webContents.openDevTools();
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  createMenu();
}

function createMenu() {
  const template = [
    {
      label: 'File',
      submenu: [
        {
          label: 'Open Save File',
          accelerator: 'CmdOrCtrl+O',
          click: () => openSaveFile()
        },
        {
          label: 'Save',
          accelerator: 'CmdOrCtrl+S',
          click: () => mainWindow.webContents.send('menu-save')
        },
        { type: 'separator' },
        {
          label: 'Exit',
          click: () => app.quit()
        }
      ]
    }
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

async function openSaveFile() {
  try {
    const result = await dialog.showOpenDialog(mainWindow, {
      title: 'Open Fallout Shelter Save File',
      filters: [
        { name: 'Save Files', extensions: ['sav'] },
        { name: 'All Files', extensions: ['*'] }
      ],
      properties: ['openFile']
    });

    if (!result.canceled && result.filePaths.length > 0) {
      const filePath = result.filePaths[0];
      const fileData = fs.readFileSync(filePath, 'utf8');
      mainWindow.webContents.send('file-opened', {
        path: filePath,
        data: fileData,
        name: path.basename(filePath)
      });
    }
  } catch (error) {
    console.error('Error:', error);
  }
}

// IPC handlers
ipcMain.on('open-file-dialog', () => {
  openSaveFile();
});

ipcMain.handle('save-file', async (event, filePath, data) => {
  try {
    console.log('Main process: Saving file to:', filePath);
    console.log('Main process: Data length:', data.length);

    fs.writeFileSync(filePath, data, 'utf8');
    console.log('Main process: File saved successfully');

    return { success: true };
  } catch (error) {
    console.error('Main process: Save error:', error);
    return { success: false, error: error.message };
  }
});

ipcMain.handle('create-backup', async (event, originalPath) => {
  try {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const backupPath = `${originalPath}.backup_${timestamp}`;
    fs.copyFileSync(originalPath, backupPath);
    return { success: true, backupPath };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

app.whenReady().then(() => {
  createWindow();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});