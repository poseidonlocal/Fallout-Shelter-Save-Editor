// Simple test to verify the Electron app functionality
const fs = require('fs');
const CryptoJS = require('crypto-js');

// Test the decryption with the actual save file
function testDecryption() {
    try {
        console.log('Testing Fallout Shelter save decryption...');
        
        // Read the save file
        const saveData = fs.readFileSync('Vault1.sav', 'utf8');
        console.log('Save file loaded, length:', saveData.length);
        
        // AES constants (same as in renderer.js)
        const AES_KEY_WORDS = [2815074099, 1725469378, 4039046167, 874293617, 3063605751, 3133984764, 4097598161, 3620741625];
        const AES_KEY = CryptoJS.lib.WordArray.create(AES_KEY_WORDS);
        const AES_IV = CryptoJS.enc.Hex.parse('7475383967656A693334307438397532');
        
        console.log('Key:', AES_KEY.toString());
        console.log('IV:', AES_IV.toString());
        
        // Create cipher text object from base64 string (same as renderer.js)
        const ciphertext = CryptoJS.enc.Base64.parse(saveData);
        const cipherParams = CryptoJS.lib.CipherParams.create({
            ciphertext: ciphertext
        });
        
        // Decrypt
        const decrypted = CryptoJS.AES.decrypt(cipherParams, AES_KEY, {
            iv: AES_IV,
            mode: CryptoJS.mode.CBC,
            padding: CryptoJS.pad.Pkcs7
        });
        
        const decryptedString = decrypted.toString(CryptoJS.enc.Utf8);
        console.log('Decryption successful!');
        console.log('Decrypted length:', decryptedString.length);
        console.log('First 200 chars:', decryptedString.substring(0, 200));
        
        // Try to parse JSON
        const jsonData = JSON.parse(decryptedString);
        console.log('JSON parsing successful!');
        console.log('Top-level keys:', Object.keys(jsonData));
        
        // Test encryption back
        const encrypted = CryptoJS.AES.encrypt(decryptedString, AES_KEY, {
            iv: AES_IV,
            mode: CryptoJS.mode.CBC,
            padding: CryptoJS.pad.Pkcs7
        });
        
        console.log('Re-encryption successful!');
        console.log('Original length:', saveData.length);
        console.log('Re-encrypted length:', encrypted.toString().length);
        
        return true;
    } catch (error) {
        console.error('Test failed:', error);
        return false;
    }
}

if (require.main === module) {
    testDecryption();
}