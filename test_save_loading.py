#!/usr/bin/env python3
"""
Test script to verify save file loading functionality
"""

import base64
import json
import zlib
import os

def test_save_loading(filepath="Vault1.sav"):
    """Test loading the save file with different methods."""
    
    print(f"Testing save file: {filepath}")
    print("=" * 50)
    
    if not os.path.exists(filepath):
        print(f"Error: File {filepath} not found")
        return False
    
    try:
        # Read raw file
        with open(filepath, 'rb') as f:
            raw_data = f.read()
        
        print(f"Raw file size: {len(raw_data)} bytes")
        
        # Decode base64
        try:
            decoded_data = base64.b64decode(raw_data)
            print(f"Base64 decoded size: {len(decoded_data)} bytes")
            print(f"First 20 bytes: {decoded_data[:20].hex()}")
        except Exception as e:
            print(f"Base64 decode failed: {e}")
            return False
        
        # Try decompression methods
        methods = [
            ("Raw JSON", lambda d: json.loads(d.decode('utf-8'))),
            ("Zlib", lambda d: json.loads(zlib.decompress(d).decode('utf-8'))),
            ("Zlib with header", lambda d: json.loads(zlib.decompress(d[4:]).decode('utf-8'))),
        ]
        
        for name, method in methods:
            try:
                result = method(decoded_data)
                print(f"\n✓ SUCCESS with {name}")
                print(f"Data type: {type(result)}")
                if isinstance(result, dict):
                    print(f"Keys: {list(result.keys())[:10]}")  # First 10 keys
                    
                    # Look for common Fallout Shelter fields
                    common_fields = ['vault', 'dwellers', 'resources', 'rooms', 'gameStats']
                    found_fields = [field for field in common_fields if field in result]
                    if found_fields:
                        print(f"Found common fields: {found_fields}")
                
                return True
                
            except Exception as e:
                print(f"✗ Failed with {name}: {str(e)[:100]}")
        
        print("\nAll decompression methods failed")
        return False
        
    except Exception as e:
        print(f"Error reading file: {e}")
        return False

def main():
    """Main test function."""
    print("Fallout Shelter Save File Test")
    print("=" * 40)
    
    # Test with default save file
    success = test_save_loading("Vault1.sav")
    
    if success:
        print("\n🎉 Save file can be loaded successfully!")
        print("The PyQt editor should be able to handle this file.")
    else:
        print("\n❌ Could not load save file with current methods.")
        print("The save file might use a different encryption/compression method.")
    
    # Test if backup exists
    if os.path.exists("Vault1.sav.bkp"):
        print("\nTesting backup file...")
        test_save_loading("Vault1.sav.bkp")

if __name__ == "__main__":
    main()