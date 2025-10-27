# Date Shifter

## Overview

**For EDF Files**: 
- This toolkit de-identifies patient data by applying random date-shift to year, month, and day. 
- A CSV file will be generated listing the edf_file, patient_identifier, original_edf_startdate, random_days, new_edf_startdate. This CSV is for validation purpose.
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

### 2. `modify_edf_dates.py`
- **Input:** EDF files directory and random number mappings
- **Process:** 
  - Extracts original year:month:date from EDF headers
  - Applies patient-specific random date offsets to modify the original year:month:date in the EDF headers
- **Output:** 
  - Date-shifted EDF files in designated output directory
  - CSV report the original and new EDF start date for validation
`
### 3. `update_xml.py`
- **Input:** XML annotation files 
- **Process:**
  - Remove all the "createTime", "annotator", "creatorId", and "channels" from all of the annotations. 
- **Output:**
  - Updated XML files in the same output directory 
  - CSV file documenting the PRV-id (PRV-<site>-<ptid>-<age>), and the annotator and its creatorID for future references (take the first set of annotator and creatorID as we know they are the same across the file). The CSV file should also have a extra column "more_than_one_layer", it shoule print yes if inside the same annotations file, more than one layer value is found. 

## To run
- Preapre a CSV file with the patient identifier in the first column
- Edit main.sh to set your input/output directories and file names
- Run with ./main.sh