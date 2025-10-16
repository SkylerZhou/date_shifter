#!/usr/bin/env python3

"""
Script: modify_edf_dates.py
Description: Modifies EDF file start dates based on random day offsets from CSV
Run the script using: python modify_edf_dates.py <random_number_output.csv> <input.edf> [modified_output.edf]
    random_number_output.csv is the CSV file with patient identifiers and random day offsets.
    input.edf is the EDF file to be modified.
    output.edf is optional; if not provided, a default name will be used.
"""

import sys
import csv
from datetime import datetime, timedelta
import os

def parse_edf_date(date_str):
    """Parse EDF date format (dd.mm.yy) to datetime object."""
    date_str = date_str.strip()
    day, month, year = date_str.split('.')
    
    # Handle 2-digit year (EDF uses yy format)
    year_int = int(year)
    if year_int >= 85:  # Assume 1985-1999
        full_year = 1900 + year_int
    else:  # Assume 2000-2084
        full_year = 2000 + year_int
    
    return datetime(full_year, int(month), int(day))

def parse_edf_time(time_str):
    """Parse EDF time format (hh.mm.ss) to time components."""
    time_str = time_str.strip()
    hour, minute, second = time_str.split('.')
    return int(hour), int(minute), int(second)

def parse_edf_datetime(date_str, time_str):
    """Parse EDF date and time to datetime object."""
    date_obj = parse_edf_date(date_str)
    hour, minute, second = parse_edf_time(time_str)
    return datetime(date_obj.year, date_obj.month, date_obj.day, hour, minute, second)

def format_edf_date(date_obj):
    """Format datetime object to EDF date format (dd.mm.yy)."""
    # EDF uses 2-digit year
    year_2digit = date_obj.year % 100
    return f"{date_obj.day:02d}.{date_obj.month:02d}.{year_2digit:02d}"

def format_edf_time(datetime_obj):
    """Format datetime object to EDF time format (hh.mm.ss)."""
    return f"{datetime_obj.hour:02d}.{datetime_obj.minute:02d}.{datetime_obj.second:02d}"

def read_csv_lookup(csv_file):
    """Read CSV and create lookup dictionary."""
    lookup = {}
    try:
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                patient_id = row['patient_identifier'].strip()
                random_days = int(row['random_number'])
                lookup[patient_id] = random_days
        return lookup
    except FileNotFoundError:
        print(f"Error: CSV file '{csv_file}' not found")
        sys.exit(1)
    except KeyError as e:
        print(f"Error: CSV file missing required column: {e}")
        sys.exit(1)

def extract_patient_id_from_edf_header(patient_id_raw):
    """Extract patient ID from EDF header format PRV-XXX-XXXX-XX to get XXXX part."""
    import re
    
    # Look for pattern PRV-XXX-XXXX-XX within the patient identification field
    pattern = r'PRV-\d+-([A-Z0-9]+)-\d+'
    match = re.search(pattern, patient_id_raw)
    
    if match:
        # Return the part between 2nd and 3rd hyphen (group 1)
        return match.group(1).strip()
    else:
        # If pattern doesn't match, look for any sequence that looks like our IDs
        # Try to find alphanumeric sequences that might be patient IDs
        words = patient_id_raw.split()
        for word in words:
            # Look for words that are 4 characters long and alphanumeric (typical of our IDs)
            if len(word) == 4 and word.isalnum():
                return word.strip()
        
        # If still no match, return the original stripped
        print(f"Warning: Could not extract patient ID from '{patient_id_raw}'")
        return patient_id_raw.strip()

def modify_edf_header(edf_file, lookup, max_date, output_file=None):
    """Modify EDF header with new start date and time. Returns info dict for CSV output."""
    
    if not os.path.exists(edf_file):
        print(f"Error: EDF file '{edf_file}' not found")
        return None
    
    # Read the entire file
    with open(edf_file, 'rb') as f:
        content = bytearray(f.read())
    
    # EDF header structure (first 256 bytes minimum)
    # Bytes 0-7: Version
    # Bytes 8-87: Local patient identification (80 bytes)
    # Bytes 88-167: Local recording identification (80 bytes)
    # Bytes 168-175: Startdate (dd.mm.yy) (8 bytes)
    # Bytes 176-183: Starttime (hh.mm.ss) (8 bytes)
    
    if len(content) < 256:
        print(f"Error: EDF file '{edf_file}' is too small (< 256 bytes)")
        return None
    
    # Extract patient identifier
    patient_id_raw = content[8:88].decode('ascii', errors='ignore').strip()
    print(f"Patient identifier in EDF: '{patient_id_raw}'")
    
    # Extract the relevant part (between 2nd and 3rd hyphen)
    patient_id = extract_patient_id_from_edf_header(patient_id_raw)
    print(f"Extracted patient ID for lookup: '{patient_id}'")
    
    # Check if patient ID exists in lookup
    if patient_id not in lookup:
        print(f"Warning: Patient identifier '{patient_id}' not found in CSV")
        print("Available identifiers in CSV:", list(lookup.keys()))
        return None
    
    random_days = lookup[patient_id]
    print(f"Random day offset: {random_days} days")
    
    # Extract current start date and time
    start_date_str = content[168:176].decode('ascii', errors='ignore')
    start_time_str = content[176:184].decode('ascii', errors='ignore')
    print(f"Original start date: {start_date_str}")
    print(f"Original start time: {start_time_str}")
    
    try:
        original_datetime = parse_edf_datetime(start_date_str, start_time_str)
        print(f"Parsed original datetime: {original_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as e:
        print(f"Error parsing datetime '{start_date_str} {start_time_str}': {e}")
        return None
    
    # Calculate new datetime
    new_datetime = original_datetime + timedelta(days=random_days)
    print(f"New calculated datetime: {new_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check if new date exceeds maximum allowed date
    if new_datetime.date() > max_date.date():
        print(f"WARNING: New date {new_datetime.strftime('%Y-%m-%d')} exceeds maximum allowed date {max_date.strftime('%Y-%m-%d')}")
        print("Modification aborted for this file.")
        return None
    
    # Format new date and time for EDF
    new_date_str = format_edf_date(new_datetime)
    new_time_str = format_edf_time(new_datetime)
    print(f"New start date (EDF format): {new_date_str}")
    print(f"New start time (EDF format): {new_time_str}")
    
    # Modify the header
    # Ensure date is exactly 8 bytes (padded with spaces if needed)
    new_date_bytes = new_date_str.ljust(8).encode('ascii')
    content[168:176] = new_date_bytes
    
    # Modify the time field as well
    new_time_bytes = new_time_str.ljust(8).encode('ascii')
    content[176:184] = new_time_bytes
    
    # Write to output file
    if output_file is None:
        output_file = edf_file.replace('.edf', '_modified.edf')
        if output_file == edf_file:
            output_file = edf_file + '_modified.edf'
    
    with open(output_file, 'wb') as f:
        f.write(content)
    
    print(f"✓ Successfully modified EDF file: {output_file}")
    
    # Return information for CSV output
    return {
        'patient_identifier': patient_id,
        'original_edf_startdate': original_datetime.strftime('%Y-%m-%d'),
        'original_edf_starttime': original_datetime.strftime('%H:%M:%S'),
        'new_edf_startdate': new_datetime.strftime('%Y-%m-%d'),
        'new_edf_starttime': new_datetime.strftime('%H:%M:%S'),
        'random_days_offset': random_days,
        'output_file': output_file
    }



def main():
    if len(sys.argv) < 3:
        print("Usage: python modify_edf_dates.py <output.csv> <intput.edf> [modified_output.edf]")
        print("\nExample:")
        print("  python modify_edf_dates.py output.csv input.edf")
        print("  or python modify_edf_dates.py output.csv input.edf modified_output.edf")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    edf_file = sys.argv[2]
    output_file = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Maximum allowed date
    max_date = datetime(2025, 1, 1)
    
    print("="*60)
    print("EDF Date Modifier")
    print("="*60)
    print(f"CSV file: {csv_file}")
    print(f"EDF file: {edf_file}")
    print(f"Maximum date: {max_date.strftime('%Y-%m-%d')}")
    print("="*60)
    print()
    
    # Read CSV lookup table
    lookup = read_csv_lookup(csv_file)
    print(f"Loaded {len(lookup)} entries from CSV")
    print()
    
    # Modify EDF header
    result = modify_edf_header(edf_file, lookup, max_date, output_file)
    
    if result:
        print("\n✓ Process completed successfully!")
        print(f"Patient ID: {result['patient_identifier']}")
        print(f"Original date/time: {result['original_edf_startdate']} {result['original_edf_starttime']}")
        print(f"New date/time: {result['new_edf_startdate']} {result['new_edf_starttime']}")
    else:
        print("\n✗ Process failed or aborted")
        sys.exit(1)

if __name__ == "__main__":
    main()