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
- **Input Format:**
  - CSV file with patient identifiers in the **first column**
  - Example:
    ```
    screening_id
    5WPR
    5Y4Z
    13UL
    54NA
    ```
  - File name configured in [main.sh:5](main.sh#L5) as `random_number_input.csv`

- **Process:** Generates random day offsets (±3 years range) for each unique patient

- **Output:**
  - CSV file mapping patient IDs to random day offsets
  - File name configured in [main.sh:5](main.sh#L5) as `random_number_output.csv`

### 2. `modify_edf_dates.py`
- **Input Format:**
  - `--input-dir`: Directory containing `.edf` files to be processed
    - Configured in [main.sh:9](main.sh#L9) as `input/`
  - `--random-csv`: CSV output from Step 1 (patient ID to random offset mapping)
    - Configured in [main.sh:9](main.sh#L9) as `random_number_output.csv`
  - `--output-dir`: Directory where date-shifted EDF files will be saved
    - Configured in [main.sh:10](main.sh#L10) as `output/`
  - `--output-csv`: Name for validation CSV file
    - Configured in [main.sh:10](main.sh#L10) as `validation_edf.csv`

- **Process:**
  - Extracts original year:month:date from EDF headers
  - Applies patient-specific random date offsets to modify the original year:month:date in the EDF headers

- **Output:**
  - Date-shifted EDF files in the specified output directory
  - CSV report with columns: edf_file, patient_identifier, original_edf_startdate, random_days, new_edf_startdate

### 3. `update_xml.py`
- **Input Format:**
  - `--input-dir`: Directory containing `.xml` annotation files
    - Configured in [main.sh:14](main.sh#L14) as `input/`
  - `--edf-csv`: CSV output from Step 2 (validation_edf.csv)
    - Configured in [main.sh:14](main.sh#L14) as `validation_edf.csv`
  - `--output-dir`: Directory where updated XML files will be saved
    - Configured in [main.sh:15](main.sh#L15) as `output/`
  - `--output-csv`: Name for XML validation CSV file
    - Configured in [main.sh:15](main.sh#L15) as `validation_edf_xml.csv`

- **Process:**
  - Remove all "createTime", "annotator", "creatorId", and "channels" from all annotations

- **Output:**
  - Updated XML files in the output directory
  - CSV file documenting: PRV-id (PRV-<site>-<ptid>-<age>), annotator, creatorID, and more_than_one_layer flag (indicates if multiple annotation layers found)

## To run
1. **Prepare input CSV**: Create a CSV file with patient identifiers in the first column 
   - Example filename: `random_number_input.csv`
2. **Place your files**: Put EDF and XML files in the input directory (default: `input/`)
3. **Edit main.sh**: Update the following paths/filenames as needed:
   - Line 5: Input CSV name and output CSV name for random number generator
   - Line 9-10: Input directory, output directory, and CSV filenames for EDF processing
   - Line 14-15: Input directory, output directory, and CSV filenames for XML processing
4. **Run**: Execute `./main.sh`