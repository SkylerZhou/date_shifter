#!/usr/bin/env python3

"""
Script: modify_edf_dates.py
Description: Modifies EDF file start dates based on random day offsets from CSV
Run the script using: python modify_edf_dates.py <output.csv> <input.edf> [modified_output.edf]
    output.csv is the CSV file with patient identifiers and random day offsets.
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

def format_edf_date(date_obj):
    """Format datetime object to EDF date format (dd.mm.yy)."""
    # EDF uses 2-digit year
    year_2digit = date_obj.year % 100
    return f"{date_obj.day:02d}.{date_obj.month:02d}.{year_2digit:02d}"

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

def modify_edf_header(edf_file, lookup, max_date, output_file=None):
    """Modify EDF header with new start date."""
    
    if not os.path.exists(edf_file):
        print(f"Error: EDF file '{edf_file}' not found")
        return False
    
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
        return False
    
    # Extract patient identifier
    patient_id_raw = content[8:88].decode('ascii', errors='ignore').strip()
    print(f"Patient identifier in EDF: '{patient_id_raw}'")
    
    # Check if patient ID exists in lookup
    if patient_id_raw not in lookup:
        print(f"Warning: Patient identifier '{patient_id_raw}' not found in CSV")
        print("Available identifiers in CSV:", list(lookup.keys()))
        return False
    
    random_days = lookup[patient_id_raw]
    print(f"Random day offset: {random_days} days")
    
    # Extract current start date
    start_date_str = content[168:176].decode('ascii', errors='ignore')
    print(f"Original start date: {start_date_str}")
    
    try:
        original_date = parse_edf_date(start_date_str)
        print(f"Parsed original date: {original_date.strftime('%Y-%m-%d')}")
    except Exception as e:
        print(f"Error parsing date '{start_date_str}': {e}")
        return False
    
    # Calculate new date
    new_date = original_date + timedelta(days=random_days)
    print(f"New calculated date: {new_date.strftime('%Y-%m-%d')}")
    
    # Check if new date exceeds maximum allowed date
    if new_date > max_date:
        print(f"WARNING: New date {new_date.strftime('%Y-%m-%d')} exceeds maximum allowed date {max_date.strftime('%Y-%m-%d')}")
        print("Modification aborted for this file.")
        return False
    
    # Format new date for EDF
    new_date_str = format_edf_date(new_date)
    print(f"New start date (EDF format): {new_date_str}")
    
    # Modify the header
    # Ensure it's exactly 8 bytes (padded with spaces if needed)
    new_date_bytes = new_date_str.ljust(8).encode('ascii')
    content[168:176] = new_date_bytes
    
    # Write to output file
    if output_file is None:
        output_file = edf_file.replace('.edf', '_modified.edf')
        if output_file == edf_file:
            output_file = edf_file + '_modified.edf'
    
    with open(output_file, 'wb') as f:
        f.write(content)
    
    print(f"✓ Successfully modified EDF file: {output_file}")
    return True

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
    max_date = datetime(2085, 1, 1)
    
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
    success = modify_edf_header(edf_file, lookup, max_date, output_file)
    
    if success:
        print("\n✓ Process completed successfully!")
    else:
        print("\n✗ Process failed or aborted")
        sys.exit(1)

if __name__ == "__main__":
    main()