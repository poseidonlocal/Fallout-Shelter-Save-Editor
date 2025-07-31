#!/usr/bin/env python3
"""
Fallout Shelter Save Editor - PyQt GUI
A comprehensive PyQt-based tool for editing Fallout Shelter save files.
"""

import sys
import os
import json
import base64
import zlib
import gzip
import struct
import shutil
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
import traceback

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QTextEdit, QLabel, QLineEdit, QPushButton, QFileDialog,
    QMessageBox, QGroupBox, QGridLayout, QSpinBox, QDoubleSpinBox,
    QScrollArea, QFrame, QSplitter, QTreeWidget, QTreeWidgetItem,
    QHeaderView, QComboBox, QCheckBox, QProgressBar, QStatusBar,
    QMenuBar, QAction, QToolBar, QTableWidget, QTableWidgetItem
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon, QPixmap


class SaveDecryptionWorker(QThread):
    """Worker thread for save file decryption/analysis."""
    
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    finished_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)
    
    def __init__(self, filepath: str):
        super().__init__()
        self.filepath = filepath
        
    def run(self):
        """Run the decryption process."""
        try:
            self.status_updated.emit("Loading save file...")
            self.progress_updated.emit(10)
            
            with open(self.filepath, 'rb') as f:
                raw_data = f.read()
            
            self.status_updated.emit("Decoding base64...")
            self.progress_updated.emit(20)
            
            decoded_data = base64.b64decode(raw_data)
            
            self.status_updated.emit("Attempting decompression...")
            self.progress_updated.emit(40)
            
            # Try various decompression methods
            result = self.try_decompress(decoded_data)
            
            if result:
                self.status_updated.emit("Save file loaded successfully!")
                self.progress_updated.emit(100)
                self.finished_signal.emit(result)
            else:
                self.status_updated.emit("Could not decrypt save file")
                self.error_signal.emit("Unable to decrypt or decompress save file")
                
        except Exception as e:
            self.error_signal.emit(f"Error loading save: {str(e)}")
    
    def try_decompress(self, data: bytes) -> Optional[Dict]:
        """Try various decompression methods."""
        methods = [
            ("Raw JSON", self.try_raw_json),
            ("Zlib", self.try_zlib),
            ("Gzip", self.try_gzip),
            ("Custom Format", self.try_custom_format),
        ]
        
        for i, (name, method) in enumerate(methods):
            self.status_updated.emit(f"Trying {name}...")
            self.progress_updated.emit(40 + (i * 15))
            
            try:
                result = method(data)
                if result:
                    return {
                        "method": name,
                        "data": result,
                        "raw_size": len(data)
                    }
            except Exception as e:
                continue
        
        return None
    
    def try_raw_json(self, data: bytes) -> Optional[Dict]:
        """Try parsing as raw JSON."""
        text = data.decode('utf-8')
        return json.loads(text)
    
    def try_zlib(self, data: bytes) -> Optional[Dict]:
        """Try zlib decompression."""
        decompressed = zlib.decompress(data)
        text = decompressed.decode('utf-8')
        return json.loads(text)
    
    def try_gzip(self, data: bytes) -> Optional[Dict]:
        """Try gzip decompression."""
        decompressed = gzip.decompress(data)
        text = decompressed.decode('utf-8')
        return json.loads(text)
    
    def try_custom_format(self, data: bytes) -> Optional[Dict]:
        """Try custom Fallout Shelter format."""
        # Try with header
        if len(data) > 4:
            header = struct.unpack('<I', data[:4])[0]
            if 4 < header < len(data):
                compressed_data = data[4:]
                decompressed = zlib.decompress(compressed_data)
                text = decompressed.decode('utf-8')
                return json.loads(text)
        return None


class FalloutShelterSaveEditor(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.save_data = None
        self.save_filepath = None
        self.save_method = None
        self.is_modified = False
        
        self.init_ui()
        self.setup_connections()
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Fallout Shelter Save Editor")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create toolbar
        self.create_toolbar()
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Progress bar for status bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # File info section
        self.create_file_info_section(main_layout)
        
        # Main content area with tabs
        self.create_main_content(main_layout)
        
        # Update UI state
        self.update_ui_state()
        
    def create_menu_bar(self):
        """Create the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        open_action = QAction('Open Save File', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_save_file)
        file_menu.addAction(open_action)
        
        save_action = QAction('Save', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        
        save_as_action = QAction('Save As...', self)
        save_as_action.setShortcut('Ctrl+Shift+S')
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        backup_action = QAction('Create Backup', self)
        backup_action.triggered.connect(self.create_backup)
        file_menu.addAction(backup_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu('Edit')
        
        refresh_action = QAction('Refresh Data', self)
        refresh_action.setShortcut('F5')
        refresh_action.triggered.connect(self.refresh_data)
        edit_menu.addAction(refresh_action)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def create_toolbar(self):
        """Create the toolbar."""
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        # Open button
        open_btn = QPushButton("Open Save")
        open_btn.clicked.connect(self.open_save_file)
        toolbar.addWidget(open_btn)
        
        # Save button
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_file)
        self.save_btn.setEnabled(False)
        toolbar.addWidget(self.save_btn)
        
        # Backup button
        self.backup_btn = QPushButton("Backup")
        self.backup_btn.clicked.connect(self.create_backup)
        self.backup_btn.setEnabled(False)
        toolbar.addWidget(self.backup_btn)
        
    def create_file_info_section(self, parent_layout):
        """Create the file information section."""
        info_group = QGroupBox("Save File Information")
        info_layout = QGridLayout(info_group)
        
        # File path
        info_layout.addWidget(QLabel("File:"), 0, 0)
        self.file_path_label = QLabel("No file loaded")
        self.file_path_label.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(self.file_path_label, 0, 1)
        
        # File size
        info_layout.addWidget(QLabel("Size:"), 1, 0)
        self.file_size_label = QLabel("-")
        info_layout.addWidget(self.file_size_label, 1, 1)
        
        # Decryption method
        info_layout.addWidget(QLabel("Method:"), 2, 0)
        self.method_label = QLabel("-")
        info_layout.addWidget(self.method_label, 2, 1)
        
        # Modified status
        info_layout.addWidget(QLabel("Status:"), 3, 0)
        self.status_label = QLabel("Not modified")
        info_layout.addWidget(self.status_label, 3, 1)
        
        parent_layout.addWidget(info_group)
        
    def create_main_content(self, parent_layout):
        """Create the main content area with tabs."""
        self.tab_widget = QTabWidget()
        
        # Raw Data tab
        self.create_raw_data_tab()
        
        # Vault Info tab
        self.create_vault_info_tab()
        
        # Resources tab
        self.create_resources_tab()
        
        # Dwellers tab
        self.create_dwellers_tab()
        
        # Rooms tab
        self.create_rooms_tab()
        
        parent_layout.addWidget(self.tab_widget)
        
    def create_raw_data_tab(self):
        """Create the raw data viewing/editing tab."""
        raw_widget = QWidget()
        layout = QVBoxLayout(raw_widget)
        
        # JSON editor
        self.json_editor = QTextEdit()
        self.json_editor.setFont(QFont("Consolas", 10))
        self.json_editor.textChanged.connect(self.on_data_modified)
        layout.addWidget(self.json_editor)
        
        # Format button
        format_btn = QPushButton("Format JSON")
        format_btn.clicked.connect(self.format_json)
        layout.addWidget(format_btn)
        
        self.tab_widget.addTab(raw_widget, "Raw Data")
        
    def create_vault_info_tab(self):
        """Create the vault information tab."""
        vault_widget = QWidget()
        layout = QVBoxLayout(vault_widget)
        
        # Scroll area for vault info
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QGridLayout(scroll_widget)
        
        # Vault basic info
        basic_group = QGroupBox("Basic Information")
        basic_layout = QGridLayout(basic_group)
        
        # Vault name
        basic_layout.addWidget(QLabel("Vault Name:"), 0, 0)
        self.vault_name_edit = QLineEdit()
        self.vault_name_edit.textChanged.connect(self.on_data_modified)
        basic_layout.addWidget(self.vault_name_edit, 0, 1)
        
        # Vault number
        basic_layout.addWidget(QLabel("Vault Number:"), 1, 0)
        self.vault_number_spin = QSpinBox()
        self.vault_number_spin.setRange(1, 999)
        self.vault_number_spin.valueChanged.connect(self.on_data_modified)
        basic_layout.addWidget(self.vault_number_spin, 1, 1)
        
        # Experience
        basic_layout.addWidget(QLabel("Experience:"), 2, 0)
        self.experience_spin = QSpinBox()
        self.experience_spin.setRange(0, 999999999)
        self.experience_spin.valueChanged.connect(self.on_data_modified)
        basic_layout.addWidget(self.experience_spin, 2, 1)
        
        scroll_layout.addWidget(basic_group, 0, 0)
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        self.tab_widget.addTab(vault_widget, "Vault Info")
        
    def create_resources_tab(self):
        """Create the resources editing tab."""
        resources_widget = QWidget()
        layout = QVBoxLayout(resources_widget)
        
        # Resources group
        resources_group = QGroupBox("Vault Resources")
        resources_layout = QGridLayout(resources_group)
        
        # Common resources
        self.resource_spins = {}
        resources = [
            ("Caps", "caps", 0, 999999999),
            ("Food", "food", 0, 999999),
            ("Water", "water", 0, 999999),
            ("Power", "power", 0, 999999),
            ("Stimpaks", "stimpaks", 0, 999999),
            ("RadAway", "radaway", 0, 999999),
            ("Nuka Cola Quantum", "nuka_quantum", 0, 999999),
        ]
        
        for i, (display_name, key, min_val, max_val) in enumerate(resources):
            resources_layout.addWidget(QLabel(f"{display_name}:"), i, 0)
            
            spin = QSpinBox()
            spin.setRange(min_val, max_val)
            spin.valueChanged.connect(self.on_data_modified)
            self.resource_spins[key] = spin
            resources_layout.addWidget(spin, i, 1)
            
        layout.addWidget(resources_group)
        layout.addStretch()
        
        self.tab_widget.addTab(resources_widget, "Resources")
        
    def create_dwellers_tab(self):
        """Create the dwellers management tab."""
        dwellers_widget = QWidget()
        layout = QVBoxLayout(dwellers_widget)
        
        # Dwellers table
        self.dwellers_table = QTableWidget()
        self.dwellers_table.setColumnCount(8)
        self.dwellers_table.setHorizontalHeaderLabels([
            "Name", "Level", "Health", "Happiness", "Strength", "Perception", "Endurance", "Charisma"
        ])
        
        # Make table stretch
        header = self.dwellers_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addWidget(self.dwellers_table)
        
        # Dwellers controls
        controls_layout = QHBoxLayout()
        
        refresh_dwellers_btn = QPushButton("Refresh Dwellers")
        refresh_dwellers_btn.clicked.connect(self.refresh_dwellers)
        controls_layout.addWidget(refresh_dwellers_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        self.tab_widget.addTab(dwellers_widget, "Dwellers")
        
    def create_rooms_tab(self):
        """Create the rooms management tab."""
        rooms_widget = QWidget()
        layout = QVBoxLayout(rooms_widget)
        
        # Rooms tree
        self.rooms_tree = QTreeWidget()
        self.rooms_tree.setHeaderLabels(["Room Type", "Level", "Position", "Status"])
        layout.addWidget(self.rooms_tree)
        
        # Rooms controls
        controls_layout = QHBoxLayout()
        
        refresh_rooms_btn = QPushButton("Refresh Rooms")
        refresh_rooms_btn.clicked.connect(self.refresh_rooms)
        controls_layout.addWidget(refresh_rooms_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        self.tab_widget.addTab(rooms_widget, "Rooms")
        
    def setup_connections(self):
        """Set up signal connections."""
        pass
        
    def open_save_file(self):
        """Open a save file."""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Open Fallout Shelter Save File",
            "",
            "Save Files (*.sav);;All Files (*)"
        )
        
        if filepath:
            self.load_save_file(filepath)
            
    def load_save_file(self, filepath: str):
        """Load a save file using worker thread."""
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Create and start worker thread
        self.worker = SaveDecryptionWorker(filepath)
        self.worker.progress_updated.connect(self.progress_bar.setValue)
        self.worker.status_updated.connect(self.status_bar.showMessage)
        self.worker.finished_signal.connect(self.on_save_loaded)
        self.worker.error_signal.connect(self.on_load_error)
        self.worker.start()
        
    def on_save_loaded(self, result: Dict):
        """Handle successful save file loading."""
        self.save_data = result["data"]
        self.save_filepath = self.worker.filepath
        self.save_method = result["method"]
        self.is_modified = False
        
        # Update UI
        self.update_file_info()
        self.populate_data()
        self.update_ui_state()
        
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage("Save file loaded successfully", 3000)
        
    def on_load_error(self, error_msg: str):
        """Handle save file loading error."""
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage("Failed to load save file", 3000)
        
        QMessageBox.critical(self, "Error", f"Failed to load save file:\n{error_msg}")
        
    def update_file_info(self):
        """Update the file information display."""
        if self.save_filepath:
            filename = os.path.basename(self.save_filepath)
            self.file_path_label.setText(filename)
            
            file_size = os.path.getsize(self.save_filepath)
            self.file_size_label.setText(f"{file_size:,} bytes")
            
            self.method_label.setText(self.save_method or "Unknown")
            
        self.update_status_label()
        
    def update_status_label(self):
        """Update the modification status label."""
        if self.is_modified:
            self.status_label.setText("Modified")
            self.status_label.setStyleSheet("color: orange; font-weight: bold;")
        else:
            self.status_label.setText("Not modified")
            self.status_label.setStyleSheet("color: green;")
            
    def populate_data(self):
        """Populate all tabs with save data."""
        if not self.save_data:
            return
            
        # Raw data tab
        json_text = json.dumps(self.save_data, indent=2)
        self.json_editor.setPlainText(json_text)
        
        # Vault info tab
        self.populate_vault_info()
        
        # Resources tab
        self.populate_resources()
        
        # Dwellers tab
        self.refresh_dwellers()
        
        # Rooms tab
        self.refresh_rooms()
        
    def populate_vault_info(self):
        """Populate vault information."""
        if not self.save_data:
            return
            
        # Try to find vault info in common locations
        vault_info = self.save_data
        
        # Vault name
        name_fields = ["vaultName", "name", "VaultName"]
        for field in name_fields:
            if field in vault_info:
                self.vault_name_edit.setText(str(vault_info[field]))
                break
                
        # Vault number
        number_fields = ["vaultNumber", "number", "VaultNumber"]
        for field in number_fields:
            if field in vault_info:
                self.vault_number_spin.setValue(int(vault_info[field]))
                break
                
        # Experience
        exp_fields = ["experience", "exp", "Experience"]
        for field in exp_fields:
            if field in vault_info:
                self.experience_spin.setValue(int(vault_info[field]))
                break
                
    def populate_resources(self):
        """Populate resource information."""
        if not self.save_data:
            return
            
        # Try to find resources in common locations
        resources_data = self.save_data.get("resources", self.save_data)
        
        # Map of UI keys to possible data keys
        resource_mappings = {
            "caps": ["caps", "money", "Caps"],
            "food": ["food", "Food"],
            "water": ["water", "Water"],
            "power": ["power", "electricity", "Power"],
            "stimpaks": ["stimpaks", "stimpak", "Stimpaks"],
            "radaway": ["radaway", "RadAway", "radAway"],
            "nuka_quantum": ["nuka_quantum", "quantum", "NukaQuantum"],
        }
        
        for ui_key, data_keys in resource_mappings.items():
            if ui_key in self.resource_spins:
                for data_key in data_keys:
                    if data_key in resources_data:
                        self.resource_spins[ui_key].setValue(int(resources_data[data_key]))
                        break
                        
    def refresh_dwellers(self):
        """Refresh the dwellers table."""
        if not self.save_data:
            return
            
        # Try to find dwellers data
        dwellers_data = self.save_data.get("dwellers", [])
        if not isinstance(dwellers_data, list):
            dwellers_data = []
            
        self.dwellers_table.setRowCount(len(dwellers_data))
        
        for i, dweller in enumerate(dwellers_data):
            if isinstance(dweller, dict):
                # Name
                name = dweller.get("name", f"Dweller {i+1}")
                self.dwellers_table.setItem(i, 0, QTableWidgetItem(str(name)))
                
                # Level
                level = dweller.get("level", 1)
                self.dwellers_table.setItem(i, 1, QTableWidgetItem(str(level)))
                
                # Health
                health = dweller.get("health", 100)
                self.dwellers_table.setItem(i, 2, QTableWidgetItem(str(health)))
                
                # Happiness
                happiness = dweller.get("happiness", 100)
                self.dwellers_table.setItem(i, 3, QTableWidgetItem(str(happiness)))
                
                # SPECIAL stats
                special = dweller.get("special", {})
                stats = ["strength", "perception", "endurance", "charisma"]
                for j, stat in enumerate(stats):
                    value = special.get(stat, 1)
                    self.dwellers_table.setItem(i, 4+j, QTableWidgetItem(str(value)))
                    
    def refresh_rooms(self):
        """Refresh the rooms tree."""
        self.rooms_tree.clear()
        
        if not self.save_data:
            return
            
        # Try to find rooms data
        rooms_data = self.save_data.get("rooms", [])
        if not isinstance(rooms_data, list):
            rooms_data = []
            
        for i, room in enumerate(rooms_data):
            if isinstance(room, dict):
                room_type = room.get("type", "Unknown")
                level = room.get("level", 1)
                position = f"({room.get('x', 0)}, {room.get('y', 0)})"
                status = room.get("status", "Active")
                
                item = QTreeWidgetItem([room_type, str(level), position, status])
                self.rooms_tree.addTopLevelItem(item)
                
    def on_data_modified(self):
        """Handle data modification."""
        if not self.is_modified:
            self.is_modified = True
            self.update_status_label()
            self.update_ui_state()
            
    def format_json(self):
        """Format the JSON in the raw data tab."""
        try:
            text = self.json_editor.toPlainText()
            data = json.loads(text)
            formatted = json.dumps(data, indent=2)
            self.json_editor.setPlainText(formatted)
        except json.JSONDecodeError as e:
            QMessageBox.warning(self, "JSON Error", f"Invalid JSON: {e}")
            
    def save_file(self):
        """Save the current file."""
        if not self.save_filepath:
            self.save_file_as()
            return
            
        if self.write_save_file(self.save_filepath):
            self.is_modified = False
            self.update_status_label()
            self.update_ui_state()
            self.status_bar.showMessage("File saved successfully", 3000)
        else:
            QMessageBox.critical(self, "Error", "Failed to save file")
            
    def save_file_as(self):
        """Save as a new file."""
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Save Fallout Shelter Save File",
            "",
            "Save Files (*.sav);;All Files (*)"
        )
        
        if filepath:
            if self.write_save_file(filepath):
                self.save_filepath = filepath
                self.is_modified = False
                self.update_file_info()
                self.update_ui_state()
                self.status_bar.showMessage("File saved successfully", 3000)
            else:
                QMessageBox.critical(self, "Error", "Failed to save file")
                
    def write_save_file(self, filepath: str) -> bool:
        """Write the save data to file."""
        try:
            # Get current data from JSON editor
            json_text = self.json_editor.toPlainText()
            data = json.loads(json_text)
            
            # Convert to JSON string
            json_string = json.dumps(data, separators=(',', ':'))
            
            # Compress (try to match original method)
            if self.save_method == "Zlib":
                compressed = zlib.compress(json_string.encode('utf-8'))
            else:
                # Default to zlib
                compressed = zlib.compress(json_string.encode('utf-8'))
                
            # Encode to base64
            encoded = base64.b64encode(compressed)
            
            # Write to file
            with open(filepath, 'wb') as f:
                f.write(encoded)
                
            return True
            
        except Exception as e:
            print(f"Error writing save file: {e}")
            traceback.print_exc()
            return False
            
    def create_backup(self):
        """Create a backup of the current save file."""
        if not self.save_filepath:
            QMessageBox.warning(self, "Warning", "No save file loaded")
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{self.save_filepath}.backup_{timestamp}"
        
        try:
            shutil.copy2(self.save_filepath, backup_path)
            QMessageBox.information(self, "Success", f"Backup created:\n{os.path.basename(backup_path)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create backup:\n{e}")
            
    def refresh_data(self):
        """Refresh all data displays."""
        self.populate_data()
        
    def update_ui_state(self):
        """Update UI element states based on current state."""
        has_save = self.save_data is not None
        
        self.save_btn.setEnabled(has_save and self.is_modified)
        self.backup_btn.setEnabled(has_save)
        
        # Update window title
        title = "Fallout Shelter Save Editor"
        if self.save_filepath:
            filename = os.path.basename(self.save_filepath)
            title += f" - {filename}"
            if self.is_modified:
                title += " *"
        self.setWindowTitle(title)
        
    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Fallout Shelter Save Editor",
            "Fallout Shelter Save Editor v1.0\n\n"
            "A PyQt-based tool for editing Fallout Shelter save files.\n\n"
            "Features:\n"
            "• Load and save encrypted save files\n"
            "• Edit vault information and resources\n"
            "• View and manage dwellers\n"
            "• Raw JSON editing\n"
            "• Automatic backups"
        )
        
    def closeEvent(self, event):
        """Handle window close event."""
        if self.is_modified:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save before closing?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )
            
            if reply == QMessageBox.Save:
                self.save_file()
                event.accept()
            elif reply == QMessageBox.Discard:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def main():
    """Main function."""
    app = QApplication(sys.argv)
    app.setApplicationName("Fallout Shelter Save Editor")
    app.setApplicationVersion("1.0")
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show main window
    window = FalloutShelterSaveEditor()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()