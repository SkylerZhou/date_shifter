# Date Shifter

## Overview

This toolkit de-identifies patient data by applying random date shifts to EDF (European Data Format) files and their accompanying XML annotation files. 
- Shifts year, month, and day values while preserving original time (hours, minutes, seconds)
- Maintains synchronization between EDF headers and XML annotations
- Generates a validation csv with original and modified timestamps

## Steps

The de-identification process consists of three sequential steps executed by `main.sh`:

### 1. `random_number_generator.sh`
- **Input:** CSV file containing patient identifiers
- **Process:** Generates random day offsets (±3 years range) for each unique patient
- **Output:** CSV file mapping patient IDs to random day offsets

### 2. `batch_process_edf.py`
- **Input:** EDF files directory and random number mappings
- **Process:** 
  - Extracts original date/time from EDF headers
  - Applies patient-specific date offsets to modify recording dates
- **Output:** 
  - Modified EDF files in designated output directory
  - CSV report with original and new EDF timestamps
`
### 3. `update_xml_createtime.py`
- **Input:** XML annotation files and EDF processing results
- **Process:**
  - Parses all `createTime` attributes in XML files
  - Applies the same date offsets used for corresponding EDF files
- **Output:**
  - Updated XML files with synchronized timestamps
  - UPdated CSV report to include XML timestamps

## To run
- Preapre a CSV file with the patient identifier in the first column
- Edit main.sh to set your input/output directories and file names
- Run with ./main.sh




## Overview

**For EDF Files**: 
- This toolkit de-identifies patient data by applying random date-shift to year, month, and day. 
- The EDF start time (hours, minutes, seconds) will be shifted backwards by the startOffsetUsecs (in microseconds) of the "Start Recording" annotations recorded in its accompanying XML file. 
  - We assume that when recording EEG signal, there would be time elapse bewteen the time that the machine started and the time that signal from the scalp was actually captured by the machine.
  - We assume that the "startOffsetUsecs" under the "Start Recording" in the EDF's accompanying XML gives the time elapse that the signal take to transit from the scalp to the machine.
  - We assume that the start time in the EDF header is the time when the machine capture the scalp signal. 
  - However, we want the EDF header start time to give info about the time when the machine was started. Therefore, we will shift the start time in the EDF header backward by the time elapse listed in the XML. 
- A CSV file will be generated listing the edf_file, patient_identifier, original_edf_startdate, original_edf_starttime, random_days, xml_elapse_usec, new_edf_startdate, new_edf_starttime. This CSV is for validation purpose.
**For XML Files**: 
- We assume the createTime tag in the XLM file gives information on when the annotations was actually created (not when the EEG recording was created). The toolkit de-identifies patient data by removing the createTime item in the annotations. 
- The annotator, creatorId, and channels will also be removed for simplicity. 
- Patient ID with more than 1 layers of annotations will be noted in a separate CSV file for later processing. 


## Steps

Three sequential steps will be executed by `main.sh`:

### 1. `random_number_generator.sh`
- **Input:** CSV file containing patient identifiers
- **Process:** Generates random day offsets (±3 years range) for each unique patient
- **Output:** CSV file mapping patient IDs to random day offsets

### 2. `xml_elapse_fetcher.py`
- **Input:** CSV file containing patient identifiers and XML files directory
- **Process:** Fetches the startOffsetUsecs 
- **Output:** 
Questions: 
1) The XML elapses recorded in mircoseconds whereas edf header recorded in seconds. Becuase most elapses will be smaller than 0.5 sec, shifting time on the edf header by less than 0.5 sec will return the same timestamp
2) Some patient XML file does not have a "Start Recording" annotations. 

### 2. `batch_process_edf.py`
- **Input:** EDF files directory and random number mappings
- **Process:** 
  - Extracts original date/time from EDF headers
  - Applies patient-specific date offsets to modify recording dates
- **Output:** 
  - Modified EDF files in designated output directory
  - CSV report with original and new EDF timestamps
`
### 3. `update_xml_createtime.py`
- **Input:** XML annotation files and EDF processing results
- **Process:**
  - Parses all `createTime` attributes in XML files
  - Applies the same date offsets used for corresponding EDF files
- **Output:**
  - Updated XML files with synchronized timestamps
  - UPdated CSV report to include XML timestamps

## To run
- Preapre a CSV file with the patient identifier in the first column
- Edit main.sh to set your input/output directories and file names
- Run with ./main.sh