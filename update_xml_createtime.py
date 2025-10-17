#!/usr/bin/env python3

"""
Script: update_xml_createtime.py
Description: Updates createTime values in XML annotation files based on EDF date modifications
Usage: python update_xml_createtime.py <batch_process_results.csv> <xml_directory> [output_directory]
"""

import sys
import os
import csv
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import glob

def extract_patient_id_from_filename(filename):
    """Extract patient ID from XML filename format PRV-XXX-XXXX-XX-annotations.xml"""
    # Remove path and extension
    basename = os.path.basename(filename)
    
    # Look for pattern PRV-XXX-XXXX-XX in filename
    pattern = r'PRV-\d+-([A-Z0-9]+)-\d+'
    match = re.search(pattern, basename)
    
    if match:
        return match.group(1).strip()
    else:
        print(f"Warning: Could not extract patient ID from filename '{filename}'")
        return None

def parse_createtime(createtime_str):
    """Parse createTime ISO format to datetime object"""
    # Format: "2020-08-20T18:24:35Z"
    try:
        # Remove the 'Z' at the end and parse
        dt_str = createtime_str.rstrip('Z')
        return datetime.fromisoformat(dt_str)
    except Exception as e:
        print(f"Error parsing createTime '{createtime_str}': {e}")
        return None

def format_createtime(dt):
    """Format datetime object back to createTime ISO format"""
    return dt.strftime('%Y-%m-%dT%H:%M:%SZ')

def read_batch_results_csv(csv_file):
    """Read the batch processing results CSV and create lookup dictionary"""
    lookup = {}
    try:
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['status'] == 'success':  # Only process successful modifications
                    patient_id = row['patient_identifier'].strip()
                    lookup[patient_id] = {
                        'original_edf_startdate': row['original_edf_startdate'],
                        'original_edf_starttime': row['original_edf_starttime'],
                        'new_edf_startdate': row['new_edf_startdate'],
                        'new_edf_starttime': row['new_edf_starttime']
                    }
        return lookup
    except FileNotFoundError:
        print(f"Error: CSV file '{csv_file}' not found")
        sys.exit(1)
    except KeyError as e:
        print(f"Error: CSV file missing required column: {e}")
        sys.exit(1)

def calculate_date_offset(original_date_str, new_date_str):
    """Calculate the number of days difference between original and new dates"""
    try:
        original_date = datetime.strptime(original_date_str, '%Y-%m-%d').date()
        new_date = datetime.strptime(new_date_str, '%Y-%m-%d').date()
        return (new_date - original_date).days
    except Exception as e:
        print(f"Error calculating date offset: {e}")
        return 0

def update_xml_createtimes(xml_file, lookup, output_dir):
    """Update createTime values in XML file based on EDF date modifications"""
    
    # Extract patient ID from filename
    patient_id = extract_patient_id_from_filename(xml_file)
    if not patient_id:
        return {'status': 'failed', 'error': 'Could not extract patient ID from filename'}
    
    # Check if patient ID exists in lookup
    if patient_id not in lookup:
        return {'status': 'skipped', 'error': f'Patient ID {patient_id} not found in CSV results'}
    
    edf_data = lookup[patient_id]
    
    try:
        # Parse the XML file
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        # Find all createTime attributes
        createtime_elements = []
        for elem in root.iter():
            if 'createTime' in elem.attrib:
                createtime_elements.append(elem)
        
        if not createtime_elements:
            return {'status': 'skipped', 'error': 'No createTime attributes found in XML'}
        
        # Get the first createTime to check if it matches the EDF start date/time
        first_createtime = createtime_elements[0].get('createTime')
        first_dt = parse_createtime(first_createtime)
        
        if not first_dt:
            return {'status': 'failed', 'error': 'Could not parse first createTime'}
        
        # Check if createTime date matches original EDF start date
        createtime_date = first_dt.strftime('%Y-%m-%d')
        createtime_time = first_dt.strftime('%H:%M:%S')
        
        edf_original_date = edf_data['original_edf_startdate']
        edf_original_time = edf_data['original_edf_starttime']
        
        print(f"  XML createTime: {createtime_date} {createtime_time}")
        print(f"  EDF original: {edf_original_date} {edf_original_time}")
        
        # Check if dates match (times might differ)
        if createtime_date != edf_original_date:
            return {
                'status': 'skipped', 
                'error': f'CreateTime date {createtime_date} does not match EDF start date {edf_original_date}'
            }
        
        # Calculate the date offset
        date_offset = calculate_date_offset(edf_original_date, edf_data['new_edf_startdate'])
        
        if date_offset == 0:
            return {'status': 'skipped', 'error': 'No date offset needed'}
        
        print(f"  Applying date offset: {date_offset} days")
        
        # Update all createTime attributes
        updated_count = 0
        for elem in createtime_elements:
            old_createtime = elem.get('createTime')
            old_dt = parse_createtime(old_createtime)
            
            if old_dt:
                # Apply the date offset
                new_dt = old_dt + timedelta(days=date_offset)
                new_createtime = format_createtime(new_dt)
                elem.set('createTime', new_createtime)
                updated_count += 1
        
        # Create output filename
        basename = os.path.basename(xml_file)
        output_file = os.path.join(output_dir, basename)
        
        # Write the updated XML
        tree.write(output_file, encoding='utf-8', xml_declaration=True)
        
        return {
            'status': 'success',
            'updated_count': updated_count,
            'date_offset': date_offset,
            'output_file': output_file
        }
        
    except ET.ParseError as e:
        return {'status': 'failed', 'error': f'XML parsing error: {e}'}
    except Exception as e:
        return {'status': 'failed', 'error': f'Unexpected error: {e}'}

def find_xml_files(directory):
    """Find all XML annotation files in the specified directory"""
    xml_pattern = os.path.join(directory, "*-annotations.xml")
    return glob.glob(xml_pattern)

def main():
    if len(sys.argv) < 3:
        print("Usage: python update_xml_createtime.py <batch_results.csv> <xml_directory> [output_directory]")
        print("\nExample:")
        print("  python update_xml_createtime.py results.csv . modified_xml")
        print("  python update_xml_createtime.py results.csv /path/to/xml/files")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    xml_directory = sys.argv[2]
    output_directory = sys.argv[3] if len(sys.argv) > 3 else os.path.join(xml_directory, 'modified_xml')
    
    # Validate inputs
    if not os.path.exists(csv_file):
        print(f"Error: CSV file '{csv_file}' not found")
        sys.exit(1)
    
    if not os.path.isdir(xml_directory):
        print(f"Error: Directory '{xml_directory}' not found")
        sys.exit(1)
    
    # Create output directory
    os.makedirs(output_directory, exist_ok=True)
    
    # Find all XML files
    xml_files = find_xml_files(xml_directory)
    
    if not xml_files:
        print(f"No XML annotation files found in directory '{xml_directory}'")
        sys.exit(1)
    
    print("="*70)
    print("XML CreateTime Updater")
    print("="*70)
    print(f"CSV file: {csv_file}")
    print(f"XML directory: {xml_directory}")
    print(f"Output directory: {output_directory}")
    print(f"Found {len(xml_files)} XML files to process")
    print("="*70)
    print()
    
    # Read batch processing results
    lookup = read_batch_results_csv(csv_file)
    print(f"Loaded {len(lookup)} successful EDF modifications from CSV")
    print()
    
    # Process each XML file
    results = []
    
    for i, xml_file in enumerate(xml_files, 1):
        basename = os.path.basename(xml_file)
        print(f"Processing {i}/{len(xml_files)}: {basename}")
        
        result = update_xml_createtimes(xml_file, lookup, output_directory)
        result['xml_file'] = basename
        results.append(result)
        
        print(f"  Status: {result['status']}")
        if result['status'] == 'success':
            print(f"  Updated {result['updated_count']} createTime entries")
            print(f"  Date offset: {result['date_offset']} days")
        elif result.get('error'):
            print(f"  {result['error']}")
        print()
    
    # Summary
    successful = sum(1 for r in results if r['status'] == 'success')
    skipped = sum(1 for r in results if r['status'] == 'skipped')
    failed = sum(1 for r in results if r['status'] == 'failed')
    
    print("="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Total XML files processed: {len(results)}")
    print(f"Successfully updated: {successful}")
    print(f"Skipped: {skipped}")
    print(f"Failed: {failed}")
    print(f"Modified XML files saved to: {output_directory}")
    print("="*70)

if __name__ == "__main__":
    main()