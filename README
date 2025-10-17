# Date Shifter

## Overview

This toolkit de-identifies patient data by applying random date shifts to EDF (European Data Format) files and their accompanying XML annotation files. 
- Shifts year, month, and day values while preserving original time (hours, minutes, seconds)
- Maintains synchronization between EDF headers and XML annotations
- Generates a validation csv with original and modified timestamps

## Steps

The de-identification process consists of three sequential steps executed by `main.sh`:

### 1. Random Number Generation  
- **Input:** CSV file containing patient identifiers
- **Process:** Generates random day offsets (±3 years range) for each unique patient
- **Output:** CSV file mapping patient IDs to random day offsets

### 2. EDF File Processing  
- **Input:** EDF files directory and random number mappings
- **Process:** 
  - Extracts original date/time from EDF headers
  - Applies patient-specific date offsets to modify recording dates
- **Output:** 
  - Modified EDF files in designated output directory
  - CSV report with original and new EDF timestamps

### 3. XML Annotation Synchronization  
- **Input:** XML annotation files and EDF processing results
- **Process:**
  - Parses all `createTime` attributes in XML files
  - Applies the same date offsets used for corresponding EDF files
- **Output:**
  - Updated XML files with synchronized timestamps
  - UPdated CSV report to include XML timestamps

## To run
- Preapre a CSV file with patient identifiers 
- Edit main.sh to set your input/output directories and file names
- Run with ./main.sh


