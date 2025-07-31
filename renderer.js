const { ipcRenderer } = require('electron');
const CryptoJS = require('crypto-js');

// Application state
let currentSaveData = null;
let currentFilePath = null;
let isModified = false;

// AES encryption constants
const AES_KEY_WORDS = [2815074099, 1725469378, 4039046167, 874293617, 3063605751, 3133984764, 4097598161, 3620741625];
const AES_KEY = CryptoJS.lib.WordArray.create(AES_KEY_WORDS);
const AES_IV = CryptoJS.enc.Hex.parse('7475383967656A693334307438397532');

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
        startupAnimation();
    }, 100);
});

function startupAnimation() {
    const overlay = document.getElementById('startup-overlay');
    const progressFill = document.getElementById('startup-progress');
    const progressPercent = document.getElementById('progress-percent');
    const statusText = document.getElementById('startup-status');

    if (!overlay || !progressFill || !progressPercent || !statusText) {
        initializeApp();
        return;
    }

    // Initialize
    progressFill.style.width = '0%';
    progressPercent.textContent = '0%';

    const steps = [
        { progress: 25, status: 'Loading Vault-Tec Database...', delay: 300 },
        { progress: 50, status: 'Initializing Encryption...', delay: 300 },
        { progress: 75, status: 'Connecting Systems...', delay: 300 },
        { progress: 100, status: 'Welcome to Vault-Tec!', delay: 400 }
    ];

    let currentStep = 0;

    function updateProgress() {
        if (currentStep < steps.length) {
            const step = steps[currentStep];
            
            statusText.textContent = step.status;
            progressFill.style.width = step.progress + '%';
            progressPercent.textContent = step.progress + '%';

            currentStep++;
            setTimeout(updateProgress, step.delay);
        } else {
            setTimeout(() => {
                overlay.classList.add('fade-out');
                setTimeout(() => {
                    overlay.style.display = 'none';
                    initializeApp();
                }, 800);
            }, 200);
        }
    }

    setTimeout(updateProgress, 500);
}

function initializeApp() {
    initializeEventListeners();
    initializeTabSystem();
    updateUI();
    setStatus('Ready');
    
    setTimeout(() => {
        showToast('Vault-Tec Save Editor ready!', 'success');
    }, 200);
}

function initializeEventListeners() {
    // Navigation tabs
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.addEventListener('click', () => switchTab(tab.dataset.tab));
    });

    // File operations
    const openFileBtn = document.getElementById('open-file-btn');
    const getStartedBtn = document.getElementById('get-started-btn');
    const saveBtn = document.getElementById('save-btn');
    const backupBtn = document.getElementById('backup-btn');
    
    if (openFileBtn) openFileBtn.addEventListener('click', openFile);
    if (getStartedBtn) getStartedBtn.addEventListener('click', openFile);
    if (saveBtn) saveBtn.addEventListener('click', saveFile);
    if (backupBtn) backupBtn.addEventListener('click', createBackup);

    // Resource operations
    const maxResourcesBtn = document.getElementById('max-resources-btn');
    const resetResourcesBtn = document.getElementById('reset-resources-btn');
    const applyResourcesBtn = document.getElementById('apply-resources-btn');
    
    if (maxResourcesBtn) maxResourcesBtn.addEventListener('click', maxAllResources);
    if (resetResourcesBtn) resetResourcesBtn.addEventListener('click', resetResources);
    if (applyResourcesBtn) applyResourcesBtn.addEventListener('click', applyResourceChanges);

    // Vault operations
    const applyVaultBtn = document.getElementById('apply-vault-btn');
    if (applyVaultBtn) applyVaultBtn.addEventListener('click', applyVaultChanges);

    // Raw data operations
    const formatJsonBtn = document.getElementById('format-json-btn');
    const copyJsonBtn = document.getElementById('copy-json-btn');
    
    if (formatJsonBtn) formatJsonBtn.addEventListener('click', formatJSON);
    if (copyJsonBtn) copyJsonBtn.addEventListener('click', copyJSON);

    // Dweller operations
    const maxAllDwellersBtn = document.getElementById('max-all-dwellers-btn');
    const refreshDwellersBtn = document.getElementById('refresh-dwellers-btn');
    
    if (maxAllDwellersBtn) maxAllDwellersBtn.addEventListener('click', maxAllDwellers);
    if (refreshDwellersBtn) refreshDwellersBtn.addEventListener('click', populateDwellers);

    // IPC listeners
    ipcRenderer.on('file-opened', handleFileOpened);
    ipcRenderer.on('menu-save', saveFile);
}

function initializeTabSystem() {
    switchTab('overview');
}

function switchTab(tabName) {
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.tab === tabName);
    });

    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.toggle('active', content.id === `${tabName}-tab`);
    });
}

function openFile() {
    ipcRenderer.send('open-file-dialog');
}

async function handleFileOpened(event, fileData) {
    showLoading(true);
    setStatus('Loading save file...');

    try {
        currentFilePath = fileData.path;
        document.getElementById('current-file').textContent = fileData.name;
        
        const decryptedData = decryptSaveData(fileData.data.trim());
        currentSaveData = JSON.parse(decryptedData);
        
        populateResourceInputs();
        populateVaultInfo();
        populateDwellers();
        updateRawData();
        
        document.getElementById('save-btn').disabled = false;
        document.getElementById('backup-btn').disabled = false;
        
        switchTab('resources');
        
        setStatus('Save file loaded successfully');
        showToast('Save file loaded successfully', 'success');
        setModified(false);
        
    } catch (error) {
        console.error('Error loading save file:', error);
        showToast(`Error loading save file: ${error.message}`, 'error');
        setStatus('Error loading save file');
    } finally {
        showLoading(false);
    }
}

function decryptSaveData(base64Data) {
    try {
        const ciphertext = CryptoJS.enc.Base64.parse(base64Data);
        const cipherParams = CryptoJS.lib.CipherParams.create({
            ciphertext: ciphertext
        });
        
        const decrypted = CryptoJS.AES.decrypt(cipherParams, AES_KEY, {
            iv: AES_IV,
            mode: CryptoJS.mode.CBC,
            padding: CryptoJS.pad.Pkcs7
        });
        
        const decryptedString = decrypted.toString(CryptoJS.enc.Utf8);
        
        if (!decryptedString) {
            throw new Error('Decryption failed - invalid key or corrupted data');
        }
        
        return decryptedString;
    } catch (error) {
        throw new Error(`Decryption failed: ${error.message}`);
    }
}

function encryptSaveData(jsonString) {
    try {
        const encrypted = CryptoJS.AES.encrypt(jsonString, AES_KEY, {
            iv: AES_IV,
            mode: CryptoJS.mode.CBC,
            padding: CryptoJS.pad.Pkcs7
        });
        
        return encrypted.toString();
    } catch (error) {
        throw new Error(`Encryption failed: ${error.message}`);
    }
}

function populateResourceInputs() {
    if (!currentSaveData || !currentSaveData.vault || !currentSaveData.vault.storage) {
        console.log('No vault storage data found');
        return;
    }

    const resources = currentSaveData.vault.storage.resources;
    console.log('Available resources:', Object.keys(resources));
    
    const resourceMap = {
        'caps-input': 'Nuka',
        'food-input': 'Food',
        'water-input': 'Water',
        'power-input': 'Energy',
        'stimpaks-input': 'StimPack',
        'radaway-input': 'RadAway',
        'quantum-input': 'NukaColaQuantum',
        'lunchbox-input': 'Lunchbox',
        'mrhandy-input': 'MrHandy',
        'petcarrier-input': 'PetCarrier'
    };

    Object.entries(resourceMap).forEach(([inputId, resourceKey]) => {
        const input = document.getElementById(inputId);
        if (input && resources[resourceKey] !== undefined) {
            input.value = Math.floor(resources[resourceKey]);
            console.log(`Set ${inputId} to ${resources[resourceKey]}`);
        } else {
            console.log(`Could not find ${inputId} or ${resourceKey}`);
        }
    });
}

function populateVaultInfo() {
    if (!currentSaveData || !currentSaveData.vault) {
        return;
    }

    const vault = currentSaveData.vault;
    
    const vaultNameInput = document.getElementById('vault-name-input');
    if (vaultNameInput && vault.VaultName !== undefined) {
        vaultNameInput.value = vault.VaultName;
    }

    const vaultModeInput = document.getElementById('vault-mode-input');
    if (vaultModeInput && vault.VaultMode !== undefined) {
        vaultModeInput.value = vault.VaultMode;
    }

    const vaultThemeInput = document.getElementById('vault-theme-input');
    if (vaultThemeInput && vault.VaultTheme !== undefined) {
        vaultThemeInput.value = vault.VaultTheme;
    }
}

function applyResourceChanges() {
    if (!currentSaveData || !currentSaveData.vault || !currentSaveData.vault.storage) {
        showToast('No save data loaded', 'warning');
        return;
    }

    console.log('Applying resource changes...');
    const resources = currentSaveData.vault.storage.resources;
    console.log('Current resources before changes:', resources);
    
    const resourceMap = {
        'caps-input': 'Nuka',
        'food-input': 'Food',
        'water-input': 'Water',
        'power-input': 'Energy',
        'stimpaks-input': 'StimPack',
        'radaway-input': 'RadAway',
        'quantum-input': 'NukaColaQuantum',
        'lunchbox-input': 'Lunchbox',
        'mrhandy-input': 'MrHandy',
        'petcarrier-input': 'PetCarrier'
    };

    let changesApplied = 0;

    Object.entries(resourceMap).forEach(([inputId, resourceKey]) => {
        const input = document.getElementById(inputId);
        if (input && input.value.trim()) {
            const value = parseFloat(input.value);
            if (!isNaN(value) && value >= 0) {
                console.log(`Changing ${resourceKey} from ${resources[resourceKey]} to ${value}`);
                resources[resourceKey] = value;
                changesApplied++;
            }
        }
    });

    console.log('Resources after changes:', resources);
    console.log(`Applied ${changesApplied} changes`);

    if (changesApplied > 0) {
        setModified(true);
        updateRawData();
        showToast(`Applied ${changesApplied} resource changes`, 'success');
    } else {
        showToast('No valid changes to apply', 'warning');
    }
}

function maxAllResources() {
    const maxValues = {
        'caps-input': 999999,
        'food-input': 999999,
        'water-input': 999999,
        'power-input': 999999,
        'stimpaks-input': 999999,
        'radaway-input': 999999,
        'quantum-input': 999,
        'lunchbox-input': 999,
        'mrhandy-input': 99,
        'petcarrier-input': 999
    };

    Object.entries(maxValues).forEach(([inputId, value]) => {
        const input = document.getElementById(inputId);
        if (input) {
            input.value = value;
        }
    });

    applyResourceChanges();
}

function resetResources() {
    populateResourceInputs();
    showToast('Resources reset to saved values', 'info');
}

function applyVaultChanges() {
    if (!currentSaveData || !currentSaveData.vault) {
        showToast('No save data loaded', 'warning');
        return;
    }

    const vault = currentSaveData.vault;
    let changesApplied = 0;

    const vaultNameInput = document.getElementById('vault-name-input');
    if (vaultNameInput && vaultNameInput.value.trim()) {
        vault.VaultName = vaultNameInput.value.trim();
        changesApplied++;
    }

    const vaultModeInput = document.getElementById('vault-mode-input');
    if (vaultModeInput && vaultModeInput.value) {
        vault.VaultMode = vaultModeInput.value;
        changesApplied++;
    }

    const vaultThemeInput = document.getElementById('vault-theme-input');
    if (vaultThemeInput && vaultThemeInput.value.trim()) {
        const theme = parseInt(vaultThemeInput.value);
        if (!isNaN(theme) && theme >= 0) {
            vault.VaultTheme = theme;
            changesApplied++;
        }
    }

    if (changesApplied > 0) {
        setModified(true);
        updateRawData();
        showToast(`Applied ${changesApplied} vault changes`, 'success');
    } else {
        showToast('No valid changes to apply', 'warning');
    }
}

function updateRawData() {
    const textarea = document.getElementById('raw-data-textarea');
    if (currentSaveData && textarea) {
        textarea.value = JSON.stringify(currentSaveData, null, 2);
    }
}

function formatJSON() {
    const textarea = document.getElementById('raw-data-textarea');
    if (!textarea) return;
    
    try {
        const parsed = JSON.parse(textarea.value);
        textarea.value = JSON.stringify(parsed, null, 2);
        showToast('JSON formatted successfully', 'success');
    } catch (error) {
        showToast('Invalid JSON format', 'error');
    }
}

function copyJSON() {
    const textarea = document.getElementById('raw-data-textarea');
    if (!textarea) return;
    
    textarea.select();
    document.execCommand('copy');
    showToast('JSON copied to clipboard', 'success');
}

async function saveFile() {
    if (!currentSaveData || !currentFilePath) {
        showToast('No file loaded to save', 'warning');
        return;
    }

    console.log('Starting save process...');
    console.log('Current file path:', currentFilePath);
    console.log('Save data exists:', !!currentSaveData);

    showLoading(true);
    setStatus('Saving file...');

    try {
        console.log('Converting to JSON...');
        const jsonString = JSON.stringify(currentSaveData);
        console.log('JSON string length:', jsonString.length);
        
        console.log('Encrypting data...');
        const encryptedData = encryptSaveData(jsonString);
        console.log('Encrypted data length:', encryptedData.length);
        
        console.log('Sending to main process...');
        const result = await ipcRenderer.invoke('save-file', currentFilePath, encryptedData);
        console.log('Save result:', result);
        
        if (result.success) {
            setModified(false);
            setStatus('File saved successfully');
            showToast('File saved successfully', 'success');
            console.log('Save completed successfully');
        } else {
            throw new Error(result.error);
        }
        
    } catch (error) {
        console.error('Error saving file:', error);
        showToast(`Error saving file: ${error.message}`, 'error');
        setStatus('Error saving file');
    } finally {
        showLoading(false);
    }
}

async function createBackup() {
    if (!currentFilePath) {
        showToast('No file loaded to backup', 'warning');
        return;
    }

    try {
        const result = await ipcRenderer.invoke('create-backup', currentFilePath);
        
        if (result.success) {
            showToast(`Backup created: ${require('path').basename(result.backupPath)}`, 'success');
        } else {
            throw new Error(result.error);
        }
        
    } catch (error) {
        console.error('Error creating backup:', error);
        showToast(`Error creating backup: ${error.message}`, 'error');
    }
}

function setStatus(message) {
    const statusText = document.getElementById('status-text');
    if (statusText) {
        statusText.textContent = message;
    }
}

function setModified(modified) {
    isModified = modified;
    updateUI();
}

function updateUI() {
    if (isModified) {
        document.title = 'Fallout Shelter Save Editor - Modified';
    } else {
        document.title = 'Fallout Shelter Save Editor';
    }
}

function showLoading(show) {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.classList.toggle('show', show);
    }
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 4000);
}

// Dwellers Management
function populateDwellers() {
    const dwellersList = document.getElementById('dwellers-list');
    
    if (!currentSaveData || !currentSaveData.dwellers || !currentSaveData.dwellers.dwellers) {
        if (dwellersList) {
            dwellersList.innerHTML = `
                <div class="placeholder">
                    <i class="fas fa-users"></i>
                    <p>No dwellers found in save file</p>
                </div>
            `;
        }
        return;
    }

    const dwellers = currentSaveData.dwellers.dwellers;
    
    if (dwellers.length === 0) {
        dwellersList.innerHTML = `
            <div class="placeholder">
                <i class="fas fa-users"></i>
                <p>No dwellers in vault</p>
            </div>
        `;
        return;
    }

    console.log(`Found ${dwellers.length} dwellers`);

    dwellersList.innerHTML = dwellers.map((dweller, index) => {
        const name = dweller.name || `Dweller ${index + 1}`;
        const level = dweller.experience?.currentLevel || 1;
        const happiness = Math.round(dweller.happiness?.happinessValue || 0);
        const health = Math.round(dweller.health?.healthValue || 100);
        const gender = dweller.gender === 2 ? 'Female' : 'Male';
        const pregnant = dweller.relations?.pregnant || false;
        
        // SPECIAL stats
        const special = dweller.serializeableSpecialStats || {};
        const strength = special.stats?.[1] || 1;
        const perception = special.stats?.[2] || 1;
        const endurance = special.stats?.[3] || 1;
        const charisma = special.stats?.[4] || 1;
        const intelligence = special.stats?.[5] || 1;
        const agility = special.stats?.[6] || 1;
        const luck = special.stats?.[7] || 1;

        return `
            <div class="dweller-card" data-index="${index}">
                <div class="dweller-header">
                    <h3 class="dweller-name">${name}</h3>
                    <span class="dweller-gender ${gender.toLowerCase()}">${gender}</span>
                    ${pregnant ? '<span class="pregnant-badge">Pregnant</span>' : ''}
                </div>
                
                <div class="dweller-stats">
                    <div class="stat-row">
                        <span>Level:</span>
                        <input type="number" class="dweller-input" data-field="experience.currentLevel" value="${level}" min="1" max="50">
                    </div>
                    <div class="stat-row">
                        <span>Happiness:</span>
                        <input type="number" class="dweller-input" data-field="happiness.happinessValue" value="${happiness}" min="0" max="100">%
                    </div>
                    <div class="stat-row">
                        <span>Health:</span>
                        <input type="number" class="dweller-input" data-field="health.healthValue" value="${health}" min="0" max="100">%
                    </div>
                </div>

                <div class="special-stats">
                    <h4>SPECIAL</h4>
                    <div class="special-grid">
                        <div class="special-stat">
                            <label>S</label>
                            <input type="number" class="special-input" data-stat="1" value="${strength}" min="1" max="10">
                        </div>
                        <div class="special-stat">
                            <label>P</label>
                            <input type="number" class="special-input" data-stat="2" value="${perception}" min="1" max="10">
                        </div>
                        <div class="special-stat">
                            <label>E</label>
                            <input type="number" class="special-input" data-stat="3" value="${endurance}" min="1" max="10">
                        </div>
                        <div class="special-stat">
                            <label>C</label>
                            <input type="number" class="special-input" data-stat="4" value="${charisma}" min="1" max="10">
                        </div>
                        <div class="special-stat">
                            <label>I</label>
                            <input type="number" class="special-input" data-stat="5" value="${intelligence}" min="1" max="10">
                        </div>
                        <div class="special-stat">
                            <label>A</label>
                            <input type="number" class="special-input" data-stat="6" value="${agility}" min="1" max="10">
                        </div>
                        <div class="special-stat">
                            <label>L</label>
                            <input type="number" class="special-input" data-stat="7" value="${luck}" min="1" max="10">
                        </div>
                    </div>
                </div>

                <div class="dweller-actions">
                    <button class="secondary-btn apply-dweller-btn" data-index="${index}">
                        <i class="fas fa-check"></i>
                        Apply Changes
                    </button>
                    <button class="secondary-btn max-special-btn" data-index="${index}">
                        <i class="fas fa-arrow-up"></i>
                        Max SPECIAL
                    </button>
                </div>
            </div>
        `;
    }).join('');

    // Add event listeners for dweller editing
    addDwellerEventListeners();
}

function addDwellerEventListeners() {
    // Apply changes buttons
    document.querySelectorAll('.apply-dweller-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const index = parseInt(e.target.closest('.apply-dweller-btn').dataset.index);
            applyDwellerChanges(index);
        });
    });

    // Max SPECIAL buttons
    document.querySelectorAll('.max-special-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const index = parseInt(e.target.closest('.max-special-btn').dataset.index);
            maxDwellerSpecial(index);
        });
    });
}

function applyDwellerChanges(dwellerIndex) {
    if (!currentSaveData || !currentSaveData.dwellers || !currentSaveData.dwellers.dwellers[dwellerIndex]) {
        showToast('Dweller not found', 'error');
        return;
    }

    const dweller = currentSaveData.dwellers.dwellers[dwellerIndex];
    const card = document.querySelector(`.dweller-card[data-index="${dwellerIndex}"]`);
    
    if (!card) return;

    let changesApplied = 0;

    // Apply basic stats
    card.querySelectorAll('.dweller-input').forEach(input => {
        const field = input.dataset.field;
        const value = parseFloat(input.value);
        
        if (!isNaN(value)) {
            setNestedValue(dweller, field, value);
            changesApplied++;
        }
    });

    // Apply SPECIAL stats
    card.querySelectorAll('.special-input').forEach(input => {
        const statIndex = parseInt(input.dataset.stat);
        const value = parseInt(input.value);
        
        if (!isNaN(value) && value >= 1 && value <= 10) {
            if (!dweller.serializeableSpecialStats) {
                dweller.serializeableSpecialStats = { stats: {} };
            }
            if (!dweller.serializeableSpecialStats.stats) {
                dweller.serializeableSpecialStats.stats = {};
            }
            
            dweller.serializeableSpecialStats.stats[statIndex] = value;
            changesApplied++;
        }
    });

    if (changesApplied > 0) {
        setModified(true);
        updateRawData();
        showToast(`Applied ${changesApplied} changes to dweller`, 'success');
    } else {
        showToast('No valid changes to apply', 'warning');
    }
}

function maxDwellerSpecial(dwellerIndex) {
    const card = document.querySelector(`.dweller-card[data-index="${dwellerIndex}"]`);
    if (!card) return;

    // Set all SPECIAL stats to 10
    card.querySelectorAll('.special-input').forEach(input => {
        input.value = 10;
    });

    applyDwellerChanges(dwellerIndex);
}

function setNestedValue(obj, path, value) {
    const keys = path.split('.');
    let current = obj;
    
    for (let i = 0; i < keys.length - 1; i++) {
        if (!current[keys[i]]) {
            current[keys[i]] = {};
        }
        current = current[keys[i]];
    }
    
    current[keys[keys.length - 1]] = value;
}

// Advanced Editing Functions
function addAdvancedResourceOptions() {
    // Add lunchbox and other premium resources
    const advancedResources = {
        'lunchbox-input': 'Lunchbox',
        'mrhandy-input': 'MrHandy',
        'petcarrier-input': 'PetCarrier',
        'craftedoutfit-input': 'CraftedOutfit',
        'craftedweapon-input': 'CraftedWeapon',
        'craftedtheme-input': 'CraftedTheme'
    };

    if (currentSaveData && currentSaveData.vault && currentSaveData.vault.storage) {
        const resources = currentSaveData.vault.storage.resources;
        
        Object.entries(advancedResources).forEach(([inputId, resourceKey]) => {
            const input = document.getElementById(inputId);
            if (input && resources[resourceKey] !== undefined) {
                input.value = Math.floor(resources[resourceKey]);
            }
        });
    }
}

function maxAllDwellers() {
    if (!currentSaveData || !currentSaveData.dwellers || !currentSaveData.dwellers.dwellers) {
        showToast('No dwellers found', 'warning');
        return;
    }

    const dwellers = currentSaveData.dwellers.dwellers;
    let modifiedCount = 0;

    dwellers.forEach((dweller, index) => {
        // Max level
        if (dweller.experience) {
            dweller.experience.currentLevel = 50;
            dweller.experience.experienceValue = 2916000; // Max XP for level 50
        }

        // Max happiness and health
        if (dweller.happiness) {
            dweller.happiness.happinessValue = 100;
        }
        if (dweller.health) {
            dweller.health.healthValue = 100;
        }

        // Max SPECIAL
        if (!dweller.serializeableSpecialStats) {
            dweller.serializeableSpecialStats = { stats: {} };
        }
        if (!dweller.serializeableSpecialStats.stats) {
            dweller.serializeableSpecialStats.stats = {};
        }

        for (let i = 1; i <= 7; i++) {
            dweller.serializeableSpecialStats.stats[i] = 10;
        }

        modifiedCount++;
    });

    if (modifiedCount > 0) {
        setModified(true);
        updateRawData();
        populateDwellers(); // Refresh the display
        showToast(`Maxed out ${modifiedCount} dwellers`, 'success');
    }
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}