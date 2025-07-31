#!/usr/bin/env python3
"""
Fallout Shelter Save File Analyzer
Analyzes the structure and format of Fallout Shelter save files.
"""

import base64
import json
import zlib
import gzip
import struct
import binascii
from typing import Optional, Dict, Any


def analyze_save_file(filepath: str) -> Dict[str, Any]:
    """Comprehensive analysis of a Fallout Shelter save file."""
    
    results = {
        "file_path": filepath,
        "analysis": {},
        "errors": []
    }
    
    try:
        # Read raw file
        with open(filepath, 'rb') as f:
            raw_data = f.read()
        
        results["analysis"]["raw_size"] = len(raw_data)
        results["analysis"]["raw_preview"] = raw_data[:100].hex()
        
        # Check if it's base64
        try:
            decoded_data = base64.b64decode(raw_data)
            results["analysis"]["base64_decoded"] = True
            results["analysis"]["decoded_size"] = len(decoded_data)
            results["analysis"]["decoded_preview"] = decoded_data[:50].hex()
            
            # Analyze decoded data
            analyze_decoded_data(decoded_data, results)
            
        except Exception as e:
            results["errors"].append(f"Base64 decode failed: {e}")
            results["analysis"]["base64_decoded"] = False
            
    except Exception as e:
        results["errors"].append(f"File read failed: {e}")
        
    return results


def analyze_decoded_data(data: bytes, results: Dict[str, Any]) -> None:
    """Analyze the decoded binary data."""
    
    # Check for common compression signatures
    compression_tests = [
        ("zlib", lambda d: zlib.decompress(d)),
        ("gzip", lambda d: gzip.decompress(d)),
        ("zlib_raw", lambda d: zlib.decompress(d, -15)),  # Raw deflate
    ]
    
    for name, decompress_func in compression_tests:
        try:
            decompressed = decompress_func(data)
            results["analysis"][f"{name}_success"] = True
            results["analysis"][f"{name}_size"] = len(decompressed)
            
            # Try to parse as JSON
            try:
                text = decompressed.decode('utf-8')
                json_data = json.loads(text)
                results["analysis"][f"{name}_json_success"] = True
                results["analysis"][f"{name}_json_keys"] = list(json_data.keys()) if isinstance(json_data, dict) else "not_dict"
                results["analysis"]["parsed_data"] = json_data
                return  # Success! Stop here
            except Exception as json_e:
                results["analysis"][f"{name}_json_error"] = str(json_e)
                
        except Exception as e:
            results["analysis"][f"{name}_error"] = str(e)
    
    # If no standard compression worked, try custom analysis
    analyze_custom_format(data, results)


def analyze_custom_format(data: bytes, results: Dict[str, Any]) -> None:
    """Analyze for custom Fallout Shelter format."""
    
    # Check for common patterns
    if len(data) >= 4:
        # Try reading first 4 bytes as various integer formats
        results["analysis"]["first_4_bytes_le"] = struct.unpack('<I', data[:4])[0]
        results["analysis"]["first_4_bytes_be"] = struct.unpack('>I', data[:4])[0]
        
        # Check if first 4 bytes could be a length field
        length_le = struct.unpack('<I', data[:4])[0]
        length_be = struct.unpack('>I', data[:4])[0]
        
        if 4 < length_le < len(data):
            results["analysis"]["possible_length_field_le"] = length_le
            try_decompress_with_header(data[4:], results, "le_header")
            
        if 4 < length_be < len(data):
            results["analysis"]["possible_length_field_be"] = length_be
            try_decompress_with_header(data[4:], results, "be_header")
    
    # Look for JSON-like patterns in raw data
    text_preview = data.decode('utf-8', errors='ignore')[:500]
    if '{' in text_preview or '"' in text_preview:
        results["analysis"]["possible_json_content"] = text_preview
    
    # Check for encryption patterns (high entropy)
    entropy = calculate_entropy(data)
    results["analysis"]["entropy"] = entropy
    
    if entropy > 7.5:
        results["analysis"]["likely_encrypted"] = True
    else:
        results["analysis"]["likely_encrypted"] = False


def try_decompress_with_header(data: bytes, results: Dict[str, Any], prefix: str) -> None:
    """Try decompressing data after removing header."""
    
    compression_methods = [
        ("zlib", lambda d: zlib.decompress(d)),
        ("gzip", lambda d: gzip.decompress(d)),
        ("zlib_raw", lambda d: zlib.decompress(d, -15)),
    ]
    
    for name, decompress_func in compression_methods:
        try:
            decompressed = decompress_func(data)
            results["analysis"][f"{prefix}_{name}_success"] = True
            results["analysis"][f"{prefix}_{name}_size"] = len(decompressed)
            
            # Try JSON parse
            try:
                text = decompressed.decode('utf-8')
                json_data = json.loads(text)
                results["analysis"][f"{prefix}_{name}_json_success"] = True
                results["analysis"]["parsed_data"] = json_data
                return
            except:
                pass
                
        except Exception as e:
            results["analysis"][f"{prefix}_{name}_error"] = str(e)


def calculate_entropy(data: bytes) -> float:
    """Calculate Shannon entropy of data."""
    if not data:
        return 0
    
    import math
    
    # Count byte frequencies
    frequencies = [0] * 256
    for byte in data:
        frequencies[byte] += 1
    
    # Calculate entropy
    entropy = 0
    data_len = len(data)
    for freq in frequencies:
        if freq > 0:
            p = freq / data_len
            entropy -= p * math.log2(p)
    
    return entropy


def print_analysis_results(results: Dict[str, Any]) -> None:
    """Print analysis results in a readable format."""
    
    print(f"Analysis Results for: {results['file_path']}")
    print("=" * 50)
    
    if results["errors"]:
        print("ERRORS:")
        for error in results["errors"]:
            print(f"  - {error}")
        print()
    
    analysis = results["analysis"]
    
    print("FILE INFO:")
    print(f"  Raw size: {analysis.get('raw_size', 'unknown')} bytes")
    print(f"  Base64 decoded: {analysis.get('base64_decoded', False)}")
    if analysis.get('decoded_size'):
        print(f"  Decoded size: {analysis['decoded_size']} bytes")
    print()
    
    print("COMPRESSION ANALYSIS:")
    compression_methods = ['zlib', 'gzip', 'zlib_raw']
    for method in compression_methods:
        if f"{method}_success" in analysis:
            print(f"  {method}: SUCCESS (size: {analysis[f'{method}_size']})")
            if f"{method}_json_success" in analysis:
                print(f"    JSON parse: SUCCESS")
                if "parsed_data" in analysis:
                    data = analysis["parsed_data"]
                    if isinstance(data, dict):
                        print(f"    Keys: {list(data.keys())[:10]}")  # First 10 keys
            else:
                print(f"    JSON parse: FAILED")
        elif f"{method}_error" in analysis:
            print(f"  {method}: FAILED ({analysis[f'{method}_error']})")
    print()
    
    if "entropy" in analysis:
        print(f"DATA CHARACTERISTICS:")
        print(f"  Entropy: {analysis['entropy']:.2f}")
        print(f"  Likely encrypted: {analysis.get('likely_encrypted', 'unknown')}")
        print()
    
    if "parsed_data" in analysis:
        print("PARSED DATA PREVIEW:")
        data = analysis["parsed_data"]
        if isinstance(data, dict):
            for key, value in list(data.items())[:5]:  # First 5 items
                print(f"  {key}: {str(value)[:100]}")
        else:
            print(f"  {str(data)[:200]}")


def main():
    """Main function."""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python analyze_save.py <save_file_path>")
        print("Example: python analyze_save.py Vault1.sav")
        return
    
    filepath = sys.argv[1]
    results = analyze_save_file(filepath)
    print_analysis_results(results)
    
    # Save detailed results to JSON
    output_file = f"{filepath}_analysis.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nDetailed analysis saved to: {output_file}")


if __name__ == "__main__":
    main()