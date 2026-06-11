import urllib.request
import json
import re
import os

URL = "https://raw.githubusercontent.com/XiaomiFirmwareUpdater/xiaomi_devices/refs/heads/names/names.json"
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "devices.json")
DEVICES_DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "devices_data.txt")
PAD_DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pad_data.txt")

# Common region/carrier suffixes to ignore when extracting the main key
IGNORE_SUFFIXES = {
    'global', 'eea', 'in', 'ru', 'tr', 'tw', 'id', 'jp', 'cn', 'sg', 'alpha',
    'cl', 'en', 'by', 'hg', 'or', 'sf', 'tf', 'ti', 'vf', 'lm', 'cr', 'mx',
    'at', 'tc', 'za', 'vc', 'rf', 'gt', 'tg', 'factory', 'kd', 'p70', 'mt',
    'ms', 'wom', 'telcel', 'as', 'sb', 'dpp', 'gpp', 'dck', 'dc'
}

def get_main_key(key):
    # If the key is related to _global, resolve it to its main key
    if "_global" in key.lower():
        parts = key.split('_')
        main_parts = []
        for part in parts:
            if part.lower() in IGNORE_SUFFIXES:
                break
            main_parts.append(part)
        return '_'.join(main_parts)
    return key

def clean_device_name(name):
    # Replace '/' with '|'
    name = name.replace('/', '|')
    
    # Filter out 'china' and 'global' (case-insensitive) as whole words
    name = re.sub(r'\s*\b(china|global)\b\s*', ' ', name, flags=re.IGNORECASE)
    name = re.sub(r'\(\s*\)', '', name)  # Remove empty parentheses if any
    
    # Normalize spaces around '|' and general spacing
    name = re.sub(r'\s*\|\s*', '|', name)
    name = re.sub(r'\s+', ' ', name)
    
    # Strip whitespace, pipe, and dash characters
    name = name.strip('-| ')
    
    return name

def strip_country_suffixes(name):
    # Strip common country and region names from the end of the string
    strip_pattern = re.compile(
        r'\s+\b(eea|indonesia|india|russia|turkey|taiwan|japan|singapore|vietnam|europe|korea|thailand|malaysia|philippines|brazil|mexico|colombia|peru|chile|spain|italy|france|germany|ukraine|poland|south korea|eea-by|eea-or|eea-sf|eea-tf|eea-ti|eea-vf|nfc)\b\s*$',
        re.IGNORECASE
    )
    while True:
        new_name, count = strip_pattern.subn('', name)
        if count == 0:
            break
        name = new_name
    return name.strip('-| ')

def main():
    print(f"Fetching online data from: {URL}")
    try:
        req = urllib.request.Request(
            URL, 
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req) as response:
            online_data = json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Error fetching online data: {e}")
        return

    print(f"Successfully fetched {len(online_data)} items. Processing...")
    
    devices = {}
    for key, value in online_data.items():
        if not key or not value:
            continue
            
        main_key = get_main_key(key)
        cleaned = clean_device_name(value)
        
        if cleaned:
            # Split variants by '|'
            variants = [v.strip() for v in cleaned.split('|') if v.strip()]
            
            # Clean each variant from country suffixes
            cleaned_variants = []
            for var in variants:
                cleaned_var = strip_country_suffixes(var)
                if cleaned_var and cleaned_var not in cleaned_variants:
                    cleaned_variants.append(cleaned_var)
            
            # Skip TV, Projector, Stick, Box, Watch, Monitor, XM- engineering names and placeholders
            valid_variants = []
            for var in cleaned_variants:
                val_lower = var.lower()
                if (
                    val_lower.startswith("xm-") or
                    val_lower == "na" or
                    val_lower == "tbd" or
                    val_lower == "-" or
                    val_lower == "unknown" or
                    "tv" in val_lower or 
                    "projector" in val_lower or 
                    "stick" in val_lower or 
                    "box" in val_lower or 
                    "watch" in val_lower or 
                    "monitor" in val_lower or
                    "手表" in val_lower or
                    "电视" in val_lower or
                    "投影" in val_lower or
                    "盒子" in val_lower or
                    val_lower == "china"
                ):
                    continue
                valid_variants.append(var)
                
            if not valid_variants:
                continue
                
            if main_key not in devices:
                devices[main_key] = []
                
            for var in valid_variants:
                if var not in devices[main_key]:
                    devices[main_key].append(var)

    # Re-assemble the devices dictionary and categorize phone vs pad
    output_data = {}
    phone_keys = []
    pad_keys = []

    for main_key in sorted(devices.keys()):
        if devices[main_key]:
            val = '|'.join(devices[main_key])
            output_data[main_key] = val
            
            # If the device name contains "pad", classify it as a Pad (tablet)
            if "pad" in val.lower():
                pad_keys.append(main_key)
            else:
                phone_keys.append(main_key)

    # Write to devices.json
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=4)
        print(f"Successfully wrote {len(output_data)} devices to {OUTPUT_FILE}")
    except Exception as e:
        print(f"Error writing devices.json: {e}")

    # Write to devices_data.txt (phones only)
    try:
        with open(DEVICES_DATA_FILE, 'w', encoding='utf-8') as f:
            for key in sorted(phone_keys):
                f.write(f"{key}\n")
        print(f"Successfully wrote {len(phone_keys)} phone codenames to {DEVICES_DATA_FILE}")
    except Exception as e:
        print(f"Error writing devices_data.txt: {e}")

    # Write to pad_data.txt (pads only)
    try:
        with open(PAD_DATA_FILE, 'w', encoding='utf-8') as f:
            for key in sorted(pad_keys):
                f.write(f"{key}\n")
        print(f"Successfully wrote {len(pad_keys)} pad codenames to {PAD_DATA_FILE}")
    except Exception as e:
        print(f"Error writing pad_data.txt: {e}")

if __name__ == '__main__':
    main()
