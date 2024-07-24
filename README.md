# Dataset curation case study

This project aims to explore solutions around dataset quality and curations, allowing mostly to:
- spot quality defaults in a dataset
- fix values when possible
- display quality metrics in a dashboard

The files of the `data-curation` module ensure those features : 
- `checks.py`: classes for the various quality checks and fixes.
- `variable_checks.py`: instances of checks considering only one value for a specific purpose (e.g., ensuring the correct format for a date).
- `entry_check.py`: instances of checks considering a whole entry (e.g., ensure that a date of exam happens before the patient's date of birth).
- `curation.py`: adds to check's potential fixing function for a value (e.g. removing accidental double forward slashes in a date).
- `assessment.py`: contains two functions 
	- `make_assessment` to link a dataset with a descriptor of the checks to use for the columns of the dataset to provide a quality assessment of the dataset containing all the errors spotted by the checks for the given columns.
	- `curate_from_assessment` to curate a dataset based on a quality assessment. It will read the errors and go through the known fixes of the check that spotted the error, if possible. The output dataset will contain only the entries (rows) without non-compliant values after the correction.
- `display.py`: contains the function `display_assessment` to show a dashboard from a quality assessment (from function `make_assessment`) with various information allowing to monitor the quality of the dataset