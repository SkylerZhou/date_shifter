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
    """Read the batch processing results CSV and return both lookup and original data"""
    lookup = {}
    csv_data = []
    try:
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                csv_data.append(row)
                patient_id = row['patient_identifier'].strip()
                lookup[patient_id] = {
                    'original_edf_startdate': row['original_edf_startdate'],
                    'original_edf_starttime': row['original_edf_starttime'],
                    'new_edf_startdate': row['new_edf_startdate'],
                    'new_edf_starttime': row['new_edf_starttime']
                }
        return lookup, csv_data
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

def get_xml_createtime_info(xml_file, lookup):
    """Extract createTime from XML file and calculate original/new values"""
    try:
        # Extract patient ID
        patient_id = extract_patient_id_from_filename(xml_file)
        if not patient_id or patient_id not in lookup:
            return {
                'original_xml_createdate': '',
                'original_xml_createtime': '',
                'new_xml_createdate': '',
                'new_xml_createtime': ''
            }
        
        # Parse the XML file
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        # Find first createTime attribute (any will do since they should be similar)
        first_createtime = None
        for elem in root.iter():
            if 'createTime' in elem.attrib:
                first_createtime = elem.get('createTime')
                break
        
        if not first_createtime:
            return {
                'original_xml_createdate': '',
                'original_xml_createtime': '',
                'new_xml_createdate': '',
                'new_xml_createtime': ''
            }
        
        # Parse the original createTime
        original_dt = parse_createtime(first_createtime)
        if not original_dt:
            return {
                'original_xml_createdate': '',
                'original_xml_createtime': '',
                'new_xml_createdate': '',
                'new_xml_createtime': ''
            }
        
        # Calculate date offset from EDF data
        edf_data = lookup[patient_id]
        date_offset = calculate_date_offset(
            edf_data['original_edf_startdate'], 
            edf_data['new_edf_startdate']
        )
        
        # Calculate new createTime (applying date offset, time unchanged)
        new_dt = original_dt + timedelta(days=date_offset)
        
        return {
            'original_xml_createdate': original_dt.strftime('%Y-%m-%d'),
            'original_xml_createtime': original_dt.strftime('%H:%M:%S'),
            'new_xml_createdate': new_dt.strftime('%Y-%m-%d'),
            'new_xml_createtime': new_dt.strftime('%H:%M:%S')
        }
            
    except Exception as e:
        print(f"Error reading XML file {xml_file}: {e}")
        return {
            'original_xml_createdate': '',
            'original_xml_createtime': '',
            'new_xml_createdate': '',
            'new_xml_createtime': ''
        }

def update_xml_createtimes(xml_file, lookup, output_dir):
    """Update createTime values in XML file based on EDF date modifications while preserving formatting"""
    
    # Extract patient ID from filename
    patient_id = extract_patient_id_from_filename(xml_file)
    if not patient_id:
        return {'status': 'failed', 'error': 'Could not extract patient ID from filename'}
    
    # Check if patient ID exists in lookup
    if patient_id not in lookup:
        return {'status': 'skipped', 'error': f'Patient ID {patient_id} not found in CSV results'}
    
    edf_data = lookup[patient_id]
    
    try:
        # Read the XML file as text to preserve formatting
        with open(xml_file, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        # Also parse with ElementTree to validate and get createTime info
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
        
        # Use regex to find and replace createTime values in the text
        import re
        
        # Pattern to match createTime attributes: createTime="YYYY-MM-DDTHH:MM:SSZ"
        createtime_pattern = r'createTime="(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)"'
        
        def replace_createtime(match):
            old_createtime = match.group(1)
            old_dt = parse_createtime(old_createtime)
            
            if old_dt:
                # Apply the date offset
                new_dt = old_dt + timedelta(days=date_offset)
                new_createtime = format_createtime(new_dt)
                return f'createTime="{new_createtime}"'
            else:
                return match.group(0)  # Return unchanged if parsing fails
        
        # Replace all createTime values
        updated_content = re.sub(createtime_pattern, replace_createtime, xml_content)
        
        # Count how many replacements were made
        updated_count = len(re.findall(createtime_pattern, xml_content))
        
        # Create output filename
        basename = os.path.basename(xml_file)
        output_file = os.path.join(output_dir, basename)
        
        # Write the updated XML content, preserving original formatting
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
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

def write_updated_csv(csv_data, xml_createtime_data, output_csv_file):
    """Write updated CSV with new columns for XML createTime info"""
    fieldnames = [
        'edf_file',
        'patient_identifier',
        'original_edf_startdate',
        'original_edf_starttime',
        'new_edf_startdate',
        'new_edf_starttime',
        'original_xml_createdate',
        'original_xml_createtime',
        'new_xml_createdate',
        'new_xml_createtime'
    ]
    
    # Merge the data
    updated_rows = []
    for row in csv_data:
        patient_id = row['patient_identifier']
        new_row = row.copy()
        
        # Add XML createTime data if available
        if patient_id in xml_createtime_data:
            xml_data = xml_createtime_data[patient_id]
            new_row['original_xml_createdate'] = xml_data['original_xml_createdate']
            new_row['original_xml_createtime'] = xml_data['original_xml_createtime']
            new_row['new_xml_createdate'] = xml_data['new_xml_createdate']
            new_row['new_xml_createtime'] = xml_data['new_xml_createtime']
        else:
            new_row['original_xml_createdate'] = ''
            new_row['original_xml_createtime'] = ''
            new_row['new_xml_createdate'] = ''
            new_row['new_xml_createtime'] = ''
        
        updated_rows.append(new_row)
    
    # Write the updated CSV
    with open(output_csv_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(updated_rows)

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
    
    print()
    print("="*70)
    print("XML CreateTime Updater")
    print(f"Found {len(xml_files)} XML files to process")
    print()
    
    # Read batch processing results
    lookup, csv_data = read_batch_results_csv(csv_file)
    
    # Collect XML createTime data
    xml_createtime_data = {}
    
    # First pass: collect original and new createTime from each XML file
    for xml_file in xml_files:
        basename = os.path.basename(xml_file)
        patient_id = extract_patient_id_from_filename(xml_file)
        
        if patient_id:
            xml_info = get_xml_createtime_info(xml_file, lookup)
            xml_createtime_data[patient_id] = xml_info
    
    print()
    
    # Process each XML file for updates
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
        elif result.get('error'):
            print(f"  {result['error']}")
        print()
    
    # Write updated CSV with XML createTime data
    updated_csv_file = csv_file.replace('.csv', '_xml.csv')
    write_updated_csv(csv_data, xml_createtime_data, updated_csv_file)
    print(f"Updated CSV saved to: {updated_csv_file}")
    
    # Summary
    successful = sum(1 for r in results if r['status'] == 'success')
    skipped = sum(1 for r in results if r['status'] == 'skipped')
    failed = sum(1 for r in results if r['status'] == 'failed')
    
    print("SUMMARY")
    print(f"Total XML files processed: {len(results)}")
    print(f"Successfully updated: {successful}")
    print(f"Skipped: {skipped}")
    print(f"Failed: {failed}")
    print("="*70)
    print()

if __name__ == "__main__":
    main()