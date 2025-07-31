#!/usr/bin/env python3
"""
Test script to verify Fallout Shelter save decryption
"""

import base64
import json
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

def test_decryption():
    """Test the decryption with the Vault1.sav file."""
    
    # Fallout Shelter encryption constants
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
    
    try:
        # Read the save file
        with open("Vault1.sav", "rb") as f:
            raw_data = f.read()
        
        print(f"Raw file size: {len(raw_data)} bytes")
        print(f"First 50 bytes (hex): {raw_data[:50].hex()}")
        
        # Decode base64
        try:
            decoded_data = base64.b64decode(raw_data)
            print(f"Decoded size: {len(decoded_data)} bytes")
            print(f"First 50 bytes of decoded (hex): {decoded_data[:50].hex()}")
        except Exception as e:
            print(f"Base64 decode failed: {e}")
            return
        
        # Decrypt using AES-CBC
        try:
            cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
            decrypted_data = cipher.decrypt(decoded_data)
            print(f"Decrypted size: {len(decrypted_data)} bytes")
            
            # Try to remove padding
            try:
                unpadded_data = unpad(decrypted_data, AES.block_size)
                print(f"Unpadded size: {len(unpadded_data)} bytes")
            except ValueError as e:
                print(f"Unpadding failed: {e}")
                # Try without unpadding
                unpadded_data = decrypted_data.rstrip(b'\x00')
                print(f"Manual padding removal size: {len(unpadded_data)} bytes")
            
            # Try to decode as UTF-8
            try:
                json_str = unpadded_data.decode('utf-8')
                print(f"UTF-8 decode successful, length: {len(json_str)}")
                print(f"First 200 characters: {json_str[:200]}")
                
                # Try to parse as JSON
                try:
                    save_data = json.loads(json_str)
                    print("JSON parsing successful!")
                    print(f"Top-level keys: {list(save_data.keys()) if isinstance(save_data, dict) else 'Not a dict'}")
                    
                    # Save pretty-printed JSON for inspection
                    with open("decrypted_save.json", "w") as f:
                        json.dump(save_data, f, indent=2)
                    print("Decrypted save written to decrypted_save.json")
                    
                except json.JSONDecodeError as e:
                    print(f"JSON parsing failed: {e}")
                    print("Saving raw decrypted text for inspection...")
                    with open("decrypted_raw.txt", "w", encoding='utf-8', errors='ignore') as f:
                        f.write(json_str)
                    
            except UnicodeDecodeError as e:
                print(f"UTF-8 decode failed: {e}")
                print("Saving raw decrypted bytes for inspection...")
                with open("decrypted_raw.bin", "wb") as f:
                    f.write(unpadded_data)
                
        except Exception as e:
            print(f"AES decryption failed: {e}")
            
    except FileNotFoundError:
        print("Vault1.sav not found in current directory")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    test_decryption()