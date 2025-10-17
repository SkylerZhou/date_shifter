#!/usr/bin/env python3

"""
Script: batch_process_edf.py
Description: Batch process all EDF files in a directory using modify_edf_dates.py
Creates a CSV file documenting the results of all processed files.
Usage: python batch_process_edf.py <csv_file> <edf_directory> [output_csv]
"""

import sys
import os
import glob
import csv
import subprocess
import json
from datetime import datetime

def find_edf_files(directory):
    """Find all EDF files in the specified directory."""
    edf_pattern = os.path.join(directory, "*.edf")
    edf_files = glob.glob(edf_pattern)
    return [f for f in edf_files if not f.endswith('_modified.edf')]

def run_modify_edf_script(csv_file, edf_file, output_dir):
    """Run modify_edf_dates.py on a single EDF file and parse the output."""
    # Create output filename - keep original name, just put in modified_files folder
    basename = os.path.basename(edf_file)
    output_file = os.path.join(output_dir, basename)
    
    # Run the modify_edf_dates.py script
    script_path = os.path.join(os.path.dirname(__file__), 'modify_edf_dates.py')
    
    try:
        cmd = ['python', script_path, csv_file, edf_file, output_file]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        # Parse the output to extract information
        output_lines = result.stdout.split('\n')
        
        info = {
            'edf_file': basename,
            'patient_identifier': '',
            'original_edf_startdate': '',
            'original_edf_starttime': '',
            'new_edf_startdate': '',
            'new_edf_starttime': '',
            'random_days_offset': '',
            'status': 'failed',
            'error_message': ''
        }
        
        # Extract information from output
        for line in output_lines:
            if 'Patient ID:' in line:
                info['patient_identifier'] = line.split(':', 1)[1].strip()
            elif 'Original date/time:' in line:
                datetime_str = line.split(':', 1)[1].strip()
                try:
                    parts = datetime_str.split(' ')
                    if len(parts) >= 2:
                        info['original_edf_startdate'] = parts[0]
                        info['original_edf_starttime'] = parts[1]
                except:
                    pass
            elif 'New date/time:' in line:
                datetime_str = line.split(':', 1)[1].strip()
                try:
                    parts = datetime_str.split(' ')
                    if len(parts) >= 2:
                        info['new_edf_startdate'] = parts[0]
                        info['new_edf_starttime'] = parts[1]
                except:
                    pass
            elif 'New calculated date:' in line:
                # Extract the random days offset if we can find it elsewhere
                # This line format: "New calculated date: 2018-11-13 (time unchanged: 13:33:45)"
                try:
                    date_part = line.split(':', 1)[1].strip().split(' ')[0]
                    info['new_edf_startdate'] = date_part
                except:
                    pass
            elif '✓ Successfully modified EDF file:' in line or 'Successfully modified EDF file:' in line:
                info['status'] = 'success'
            elif 'WARNING:' in line or 'Error:' in line:
                info['error_message'] = line.strip()
        
        # Check exit code to determine success since success message might not be printed
        if result.returncode == 0 and not info['error_message']:
            info['status'] = 'success'
        elif result.returncode != 0:
            info['status'] = 'failed'
            if not info['error_message']:
                info['error_message'] = result.stderr.strip() or 'Unknown error'
        
        return info
        
    except subprocess.TimeoutExpired:
        return {
            'edf_file': basename,
            'patient_identifier': '',
            'original_edf_startdate': '',
            'original_edf_starttime': '',
            'new_edf_startdate': '',
            'new_edf_starttime': '',
            'random_days_offset': '',
            'status': 'timeout',
            'error_message': 'Process timed out after 60 seconds'
        }
    except Exception as e:
        return {
            'edf_file': basename,
            'patient_identifier': '',
            'original_edf_startdate': '',
            'original_edf_starttime': '',
            'new_edf_startdate': '',
            'new_edf_starttime': '',
            'random_days_offset': '',
            'status': 'error',
            'error_message': str(e)
        }

def write_results_csv(results, output_csv):
    """Write results to CSV file."""
    fieldnames = [
        'edf_file',
        'patient_identifier', 
        'original_edf_startdate',
        'original_edf_starttime',
        'new_edf_startdate',
        'new_edf_starttime',
        'random_days_offset',
        'status',
        'error_message'
    ]
    
    with open(output_csv, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

def main():
    if len(sys.argv) < 3:
        print("Usage: python batch_process_edf.py <csv_file> <edf_directory> [output_csv]")
        print("\nExample:")
        print("  python batch_process_edf.py random_number_output.csv . results.csv")
        print("  python batch_process_edf.py random_number_output.csv /path/to/edf/files")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    edf_directory = sys.argv[2]
    output_csv = sys.argv[3] if len(sys.argv) > 3 else 'batch_processing_results.csv'
    
    # Validate inputs
    if not os.path.exists(csv_file):
        print(f"Error: CSV file '{csv_file}' not found")
        sys.exit(1)
    
    if not os.path.isdir(edf_directory):
        print(f"Error: Directory '{edf_directory}' not found")
        sys.exit(1)
    
    # Create output directory for modified files
    output_dir = os.path.join(edf_directory, 'modified_files')
    os.makedirs(output_dir, exist_ok=True)
    
    # Find all EDF files
    edf_files = find_edf_files(edf_directory)
    
    if not edf_files:
        print(f"No EDF files found in directory '{edf_directory}'")
        sys.exit(1)
    
    print("="*70)
    print("EDF Batch Processor")
    print("="*70)
    print(f"CSV file: {csv_file}")
    print(f"EDF directory: {edf_directory}")
    print(f"Output CSV: {output_csv}")
    print(f"Modified files directory: {output_dir}")
    print(f"Found {len(edf_files)} EDF files to process")
    print("="*70)
    print()
    
    results = []
    
    for i, edf_file in enumerate(edf_files, 1):
        print(f"Processing {i}/{len(edf_files)}: {os.path.basename(edf_file)}")
        
        result = run_modify_edf_script(csv_file, edf_file, output_dir)
        results.append(result)
        
        print(f"  Status: {result['status']}")
        if result['patient_identifier']:
            print(f"  Patient ID: {result['patient_identifier']}")
        if result['error_message']:
            print(f"  Error: {result['error_message']}")
        print()
    
    # Write results to CSV
    write_results_csv(results, output_csv)
    
    # Summary
    successful = sum(1 for r in results if r['status'] == 'success')
    failed = len(results) - successful
    
    print("="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Total files processed: {len(results)}")
    print(f"Successfully processed: {successful}")
    print(f"Failed: {failed}")
    print(f"Results saved to: {output_csv}")
    print(f"Modified EDF files saved to: {output_dir}")
    print("="*70)

if __name__ == "__main__":
    main()