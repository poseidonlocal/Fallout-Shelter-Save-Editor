#!/usr/bin/env python3
"""
Fallout Shelter Save Editor
A comprehensive tool for editing Fallout Shelter save files.
"""

import base64
import json
import zlib
import gzip
import struct
import os
import shutil
from datetime import datetime
from typing import Dict, Any, Optional, List
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


class FalloutShelterSave:
    """Handles Fallout Shelter save file operations."""
    
    # Fallout Shelter encryption constants (from JavaScript code)
    AES_KEY = bytes([
        (2815074099 >> 24) & 0xFF, (2815074099 >> 16) & 0xFF, (2815074099 >> 8) & 0xFF, 2815074099 & 0xFF,
        (1725469378 >> 24) & 0xFF, (1725469378 >> 16) & 0xFF, (1725469378 >> 8) & 0xFF, 1725469378 & 0xFF,
        (4039046167 >> 24) & 0xFF, (4039046167 >> 16) & 0xFF, (4039046167 >> 8) & 0xFF, 4039046167 & 0xFF,
        (874293617 >> 24) & 0xFF, (874293617 >> 16) & 0xFF, (874293617 >> 8) & 0xFF, 874293617 & 0xFF,
        (3063605751 >> 24) & 0xFF, (3063605751 >> 16) & 0xFF, (3063605751 >> 8) & 0xFF, 3063605751 & 0xFF,
        (3133984764 >> 24) & 0xFF, (3133984764 >> 16) & 0xFF, (3133984764 >> 8) & 0xFF, 3133984764 & 0xFF,
        (4097598161 >> 24) & 0xFF, (4097598161 >> 16) & 0xFF, (4097598161 >> 8) & 0xFF, 4097598161 & 0xFF,
        (3620741625 >> 24) & 0xFF, (3620741625 >> 16) & 0xFF, (3620741625 >> 8) & 0xFF, 3620741625 & 0xFF
    ])
    AES_IV = bytes.fromhex("7475383967656A693334307438397532")
    
    def __init__(self, filepath: str = None):
        self.filepath = filepath
        self.raw_data = None
        self.decoded_data = None
        self.save_data = None
        self.is_loaded = False
        
    def load_save(self, filepath: str = None) -> bool:
        """Load and decode a Fallout Shelter save file."""
        if filepath:
            self.filepath = filepath
            
        if not self.filepath or not os.path.exists(self.filepath):
            return False
            
        try:
            with open(self.filepath, 'rb') as f:
                self.raw_data = f.read()
            
            # Decode base64
            self.decoded_data = base64.b64decode(self.raw_data)
            
            # Try to decompress and parse
            self.save_data = self._parse_save_data()
            self.is_loaded = True
            return True
            
        except Exception as e:
            print(f"Error loading save: {e}")
            return False
    
    def _parse_save_data(self) -> Dict[str, Any]:
        """Parse the decoded save data using AES-CBC decryption."""
        try:
            # Decrypt using AES-CBC
            cipher = AES.new(self.AES_KEY, AES.MODE_CBC, self.AES_IV)
            decrypted_data = cipher.decrypt(self.decoded_data)
            
            # Remove PKCS7 padding
            try:
                unpadded_data = unpad(decrypted_data, AES.block_size)
            except ValueError:
                # If unpadding fails, try without unpadding (some implementations don't pad)
                unpadded_data = decrypted_data.rstrip(b'\x00')
            
            # Convert to string and parse JSON
            json_str = unpadded_data.decode('utf-8')
            return json.loads(json_str)
            
        except Exception as e:
            print(f"AES decryption failed: {e}")
            # Fallback to old methods if AES fails
            return self._try_fallback_methods()
    
    def _try_fallback_methods(self) -> Dict[str, Any]:
        """Fallback methods if AES decryption fails."""
        decompression_methods = [
            self._try_raw_json,
            self._try_zlib_decompress,
            self._try_gzip_decompress,
            self._try_custom_decompress,
        ]
        
        for method in decompression_methods:
            try:
                result = method(self.decoded_data)
                if result:
                    return result
            except Exception as e:
                continue
                
        # If all methods fail, return raw data info
        return {
            "error": "Could not parse save data",
            "raw_size": len(self.decoded_data),
            "raw_preview": self.decoded_data[:100].hex()
        }
    
    def _try_raw_json(self, data: bytes) -> Optional[Dict]:
        """Try to parse as raw JSON."""
        try:
            text = data.decode('utf-8')
            return json.loads(text)
        except:
            return None
    
    def _try_zlib_decompress(self, data: bytes) -> Optional[Dict]:
        """Try zlib decompression then JSON parse."""
        try:
            decompressed = zlib.decompress(data)
            text = decompressed.decode('utf-8')
            return json.loads(text)
        except:
            return None
    
    def _try_gzip_decompress(self, data: bytes) -> Optional[Dict]:
        """Try gzip decompression then JSON parse."""
        try:
            decompressed = gzip.decompress(data)
            text = decompressed.decode('utf-8')
            return json.loads(text)
        except:
            return None
    
    def _try_custom_decompress(self, data: bytes) -> Optional[Dict]:
        """Try custom Fallout Shelter decompression."""
        # Some Fallout Shelter saves use a custom format
        # This is a placeholder for reverse-engineered decompression
        try:
            # Check for common patterns in Fallout Shelter saves
            if len(data) > 4:
                # Try reading as little-endian uint32 header
                header = struct.unpack('<I', data[:4])[0]
                if header < len(data):  # Reasonable size check
                    # Try decompressing the rest
                    compressed_data = data[4:]
                    decompressed = zlib.decompress(compressed_data)
                    text = decompressed.decode('utf-8')
                    return json.loads(text)
        except:
            pass
        return None
    
    def backup_save(self) -> str:
        """Create a backup of the current save file."""
        if not self.filepath:
            return ""
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{self.filepath}.backup_{timestamp}"
        shutil.copy2(self.filepath, backup_path)
        return backup_path
    
    def save_file(self, filepath: str = None) -> bool:
        """Save the modified data back to file."""
        if not self.save_data or not self.is_loaded:
            return False
            
        save_path = filepath or self.filepath
        if not save_path:
            return False
            
        try:
            # Convert back to JSON (compact format)
            json_data = json.dumps(self.save_data, separators=(',', ':'))
            json_bytes = json_data.encode('utf-8')
            
            # Pad data for AES encryption
            padded_data = pad(json_bytes, AES.block_size)
            
            # Encrypt using AES-CBC
            cipher = AES.new(self.AES_KEY, AES.MODE_CBC, self.AES_IV)
            encrypted_data = cipher.encrypt(padded_data)
            
            # Encode to base64
            encoded = base64.b64encode(encrypted_data)
            
            # Write to file
            with open(save_path, 'wb') as f:
                f.write(encoded)
                
            return True
            
        except Exception as e:
            print(f"Error saving file: {e}")
            return False


class SaveEditorGUI:
    """GUI for the Fallout Shelter Save Editor."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Fallout Shelter Save Editor")
        self.root.geometry("800x600")
        
        self.save_handler = FalloutShelterSave()
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the user interface."""
        # Menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Save", command=self.open_save)
        file_menu.add_command(label="Save", command=self.save_file)
        file_menu.add_command(label="Save As", command=self.save_as)
        file_menu.add_separator()
        file_menu.add_command(label="Create Backup", command=self.create_backup)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # File info frame
        info_frame = ttk.LabelFrame(main_frame, text="Save File Info", padding="5")
        info_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.file_label = ttk.Label(info_frame, text="No file loaded")
        self.file_label.grid(row=0, column=0, sticky=tk.W)
        
        # Notebook for different edit categories
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Raw data tab
        self.setup_raw_tab()
        
        # Vault stats tab (placeholder for when we can parse the data)
        self.setup_vault_tab()
        
        # Resources tab
        self.setup_resources_tab()
        
        # Dwellers tab
        self.setup_dwellers_tab()
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
    def setup_raw_tab(self):
        """Set up the raw data viewing tab."""
        raw_frame = ttk.Frame(self.notebook)
        self.notebook.add(raw_frame, text="Raw Data")
        
        # Text area for raw data
        self.raw_text = scrolledtext.ScrolledText(raw_frame, wrap=tk.WORD, height=20)
        self.raw_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    def setup_vault_tab(self):
        """Set up the vault statistics tab."""
        vault_frame = ttk.Frame(self.notebook)
        self.notebook.add(vault_frame, text="Vault Stats")
        
        # Vault info
        ttk.Label(vault_frame, text="Vault Name:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.vault_name = ttk.Entry(vault_frame, width=30)
        self.vault_name.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(vault_frame, text="Vault Mode:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.vault_number = ttk.Entry(vault_frame, width=30)
        self.vault_number.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
    def setup_resources_tab(self):
        """Set up the resources editing tab."""
        resources_frame = ttk.Frame(self.notebook)
        self.notebook.add(resources_frame, text="Resources")
        
        # Common resources
        resources = ["Caps", "Food", "Water", "Power", "Stimpaks", "RadAway", "Nuka Cola Quantum"]
        self.resource_entries = {}
        
        for i, resource in enumerate(resources):
            ttk.Label(resources_frame, text=f"{resource}:").grid(row=i, column=0, sticky=tk.W, padx=5, pady=2)
            entry = ttk.Entry(resources_frame, width=20)
            entry.grid(row=i, column=1, sticky=tk.W, padx=5, pady=2)
            self.resource_entries[resource.lower().replace(" ", "_")] = entry
            
        # Add buttons for resource modification
        button_frame = ttk.Frame(resources_frame)
        button_frame.grid(row=len(resources), column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="Apply Changes", command=self.apply_resource_changes).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Max All Resources", command=self.max_all_resources).pack(side=tk.LEFT, padx=5)
            
    def setup_dwellers_tab(self):
        """Set up the dwellers editing tab."""
        dwellers_frame = ttk.Frame(self.notebook)
        self.notebook.add(dwellers_frame, text="Dwellers")
        
        # Dwellers list (placeholder)
        ttk.Label(dwellers_frame, text="Dwellers management will be available when save format is decoded").pack(pady=20)
        
    def open_save(self):
        """Open a save file."""
        filepath = filedialog.askopenfilename(
            title="Select Fallout Shelter Save File",
            filetypes=[("Save files", "*.sav"), ("All files", "*.*")]
        )
        
        if filepath:
            if self.save_handler.load_save(filepath):
                self.file_label.config(text=f"Loaded: {os.path.basename(filepath)}")
                self.update_display()
                messagebox.showinfo("Success", "Save file loaded successfully!")
            else:
                messagebox.showerror("Error", "Failed to load save file")
                
    def update_display(self):
        """Update the display with loaded save data."""
        if not self.save_handler.is_loaded:
            return
            
        # Update raw data tab
        if self.save_handler.save_data:
            raw_text = json.dumps(self.save_handler.save_data, indent=2)
            self.raw_text.delete(1.0, tk.END)
            self.raw_text.insert(1.0, raw_text)
            
            # Try to populate other tabs if data structure is known
            self.populate_vault_info()
            self.populate_resources()
            
    def populate_vault_info(self):
        """Populate vault information if available."""
        if not self.save_handler.save_data:
            return
            
        data = self.save_handler.save_data
        
        # Get vault information from the correct location
        if "vault" in data and isinstance(data["vault"], dict):
            vault = data["vault"]
            
            # Vault name
            if "VaultName" in vault:
                self.vault_name.delete(0, tk.END)
                self.vault_name.insert(0, str(vault["VaultName"]))
            
            # Vault mode (instead of number, Fallout Shelter has mode)
            if "VaultMode" in vault:
                self.vault_number.delete(0, tk.END)
                self.vault_number.insert(0, str(vault["VaultMode"]))
                
    def populate_resources(self):
        """Populate resource information if available."""
        if not self.save_handler.save_data:
            return
            
        data = self.save_handler.save_data
        
        # Fallout Shelter resource field mappings (based on actual save structure)
        resource_mappings = {
            "caps": ["Nuka"],  # Caps are stored as "Nuka" in the save
            "food": ["Food"],
            "water": ["Water"],
            "power": ["Energy"],  # Power is stored as "Energy"
            "stimpaks": ["StimPack"],
            "radaway": ["RadAway"],
            "nuka_cola_quantum": ["NukaColaQuantum"]
        }
        
        # Try to find and populate resource values
        # Look specifically in vault.storage.resources
        vault_storage = self._get_vault_storage(data)
        if vault_storage and "resources" in vault_storage:
            resources = vault_storage["resources"]
            
            for resource_key, entry in self.resource_entries.items():
                possible_fields = resource_mappings.get(resource_key, [resource_key])
                
                for field in possible_fields:
                    if field in resources:
                        entry.delete(0, tk.END)
                        entry.insert(0, str(int(resources[field])))
                        break
    
    def _find_nested_value(self, data, key):
        """Recursively search for a key in nested dictionaries."""
        if isinstance(data, dict):
            if key in data:
                return data[key]
            for value in data.values():
                result = self._find_nested_value(value, key)
                if result is not None:
                    return result
        elif isinstance(data, list):
            for item in data:
                result = self._find_nested_value(item, key)
                if result is not None:
                    return result
        return None
        
    def save_file(self):
        """Save the current file."""
        if self.save_handler.save_file():
            messagebox.showinfo("Success", "Save file updated successfully!")
        else:
            messagebox.showerror("Error", "Failed to save file")
            
    def save_as(self):
        """Save as a new file."""
        filepath = filedialog.asksaveasfilename(
            title="Save As",
            defaultextension=".sav",
            filetypes=[("Save files", "*.sav"), ("All files", "*.*")]
        )
        
        if filepath:
            if self.save_handler.save_file(filepath):
                messagebox.showinfo("Success", f"Save file created: {os.path.basename(filepath)}")
            else:
                messagebox.showerror("Error", "Failed to create save file")
                
    def create_backup(self):
        """Create a backup of the current save."""
        if not self.save_handler.filepath:
            messagebox.showwarning("Warning", "No save file loaded")
            return
            
        backup_path = self.save_handler.backup_save()
        if backup_path:
            messagebox.showinfo("Success", f"Backup created: {os.path.basename(backup_path)}")
        else:
            messagebox.showerror("Error", "Failed to create backup")
    
    def apply_resource_changes(self):
        """Apply resource changes to the save data."""
        if not self.save_handler.save_data:
            messagebox.showwarning("Warning", "No save data loaded")
            return
            
        try:
            # Fallout Shelter resource field mappings
            resource_mappings = {
                "caps": ["Nuka"],
                "food": ["Food"],
                "water": ["Water"],
                "power": ["Energy"],
                "stimpaks": ["StimPack"],
                "radaway": ["RadAway"],
                "nuka_cola_quantum": ["NukaColaQuantum"]
            }
            
            # Get vault storage
            vault_storage = self._get_vault_storage(self.save_handler.save_data)
            if not vault_storage or "resources" not in vault_storage:
                messagebox.showerror("Error", "Could not find vault storage in save data")
                return
            
            resources = vault_storage["resources"]
            changes_made = 0
            
            for resource_key, entry in self.resource_entries.items():
                value_str = entry.get().strip()
                if value_str:
                    try:
                        value = float(value_str)  # Fallout Shelter uses floats for resources
                        possible_fields = resource_mappings.get(resource_key, [resource_key])
                        
                        for field in possible_fields:
                            if field in resources:
                                resources[field] = value
                                changes_made += 1
                                break
                    except ValueError:
                        messagebox.showerror("Error", f"Invalid value for {resource_key}: {value_str}")
                        return
            
            if changes_made > 0:
                messagebox.showinfo("Success", f"Applied {changes_made} resource changes")
            else:
                messagebox.showinfo("Info", "No changes were applied")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply changes: {e}")
    
    def max_all_resources(self):
        """Set all resources to maximum values."""
        max_values = {
            "caps": 999999,
            "food": 999999,
            "water": 999999,
            "power": 999999,
            "stimpaks": 999,
            "radaway": 999,
            "nuka_cola_quantum": 999
        }
        
        for resource_key, entry in self.resource_entries.items():
            if resource_key in max_values:
                entry.delete(0, tk.END)
                entry.insert(0, str(max_values[resource_key]))
        
        self.apply_resource_changes()
    
    def _get_vault_storage(self, data):
        """Get the vault storage section from save data."""
        if isinstance(data, dict) and "vault" in data:
            vault = data["vault"]
            if isinstance(vault, dict) and "storage" in vault:
                return vault["storage"]
        return None
    
    def _set_nested_value(self, data, key, value):
        """Recursively search for a key and set its value."""
        if isinstance(data, dict):
            if key in data:
                data[key] = value
                return True
            for nested_data in data.values():
                if self._set_nested_value(nested_data, key, value):
                    return True
        elif isinstance(data, list):
            for item in data:
                if self._set_nested_value(item, key, value):
                    return True
        return False
            
    def run(self):
        """Start the GUI."""
        self.root.mainloop()


def main():
    """Main function."""
    print("Fallout Shelter Save Editor")
    print("=" * 30)
    
    # Check if GUI is available
    try:
        app = SaveEditorGUI()
        app.run()
    except ImportError:
        print("GUI not available, running in console mode")
        console_mode()


def console_mode():
    """Console-based interface."""
    print("\nConsole Mode")
    print("1. Analyze save file")
    print("2. Create backup")
    print("3. Exit")
    
    while True:
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == "1":
            filepath = input("Enter save file path: ").strip()
            if os.path.exists(filepath):
                save = FalloutShelterSave(filepath)
                if save.load_save():
                    print(f"Save loaded successfully!")
                    print(f"Data preview: {str(save.save_data)[:200]}...")
                else:
                    print("Failed to load save file")
            else:
                print("File not found")
                
        elif choice == "2":
            filepath = input("Enter save file path: ").strip()
            if os.path.exists(filepath):
                save = FalloutShelterSave(filepath)
                backup_path = save.backup_save()
                if backup_path:
                    print(f"Backup created: {backup_path}")
                else:
                    print("Failed to create backup")
            else:
                print("File not found")
                
        elif choice == "3":
            break
        else:
            print("Invalid choice")


if __name__ == "__main__":
    main()