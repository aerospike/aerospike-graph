# Money Mule Detection Demo

This project demonstrates money mule detection using a graph database. It includes scripts to generate synthetic data for testing and analysis.

## Prerequisites

- Python 3.x
- pip (Python package installer)

## Installation

1. Clone the repository:
   ```bash
   cd money-mule-demo
   ```

2. Install the required packages:
   ```bash
   pip3 install -r requirements.txt
   ```

## Required Dependencies

The following Python packages will be installed:
- `pandas`: For data manipulation and analysis
- `pydantic`: For data validation
- `gender_guesser`: For gender prediction from names
- `faker`: For generating synthetic data
- `email_validator`: For email validation

## Usage

After installing the dependencies, you can run the main data generation script:

```bash
python3 generate_Data_Main.py
```

The script will prompt you to:
1. Enter the number of customer records to generate
2. Choose a region/locale:
   - 1: Asian
   - 2: Indian
   - 3: European
   - 4: Israel
   - 5: American

## Troubleshooting

If you encounter any dependency-related errors, try the following:

1. Upgrade pip:
   ```bash
   pip3 install --upgrade pip
   ```

2. Install dependencies individually:
   ```bash
   pip3 install pandas
   pip3 install pydantic
   pip3 install gender_guesser
   pip3 install faker
   pip3 install email_validator
   ```

3. If you're still experiencing issues, ensure you're using Python 3:
   ```bash
   python3 --version
   ```

