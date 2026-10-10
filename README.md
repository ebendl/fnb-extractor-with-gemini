# Bank Statement PDF Extractor

A Python script that uses Google's Gemini 2.5 Flash model to extract transaction data from bank statement PDFs and convert them to CSV format.

## Features

- Extracts transactions from PDF bank statements using AI
- Uses Google's Gemini 2.5 Flash model with structured output
- Converts data to CSV format with semicolon separators
- Handles credit/debit amounts correctly
- Validates date formats and numeric values
- Batch processing for entire folders of PDFs
- Transaction balance validation for data integrity
- Token counting for API usage monitoring
- CSV file combination utility for merging multiple transaction files
- Export to the Cashflow Tracker import format

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file with your Gemini API key:
```bash
cp env_template.txt .env
```

3. Edit the `.env` file and add your Gemini API key:
```
GEMINI_API_KEY=your_actual_api_key_here
```

You can get your API key from [Google AI Studio](https://aistudio.google.com/app/apikey).

## Usage

### Extract Transactions from PDFs

```bash
python bank_statement_extractor.py <path_to_pdf_file_or_folder>
```

Examples:
```bash
# Process a single PDF file
python bank_statement_extractor.py samples/FNB_FUSION_PRIVATE_CLIENTS_ACC_226.pdf

# Process all PDFs in a folder (skips files that already have CSV outputs)
python bank_statement_extractor.py /path/to/pdf/folder/
```

### Combine CSV Files

```bash
python combine_csv_files.py <directory_path>
```

Example:
```bash
# Combine all CSV files in a directory into one file
python combine_csv_files.py /path/to/csv/folder/
```

### Convert CSV to Excel

```bash
python csv_to_excel.py <path_to_csv_file_or_folder>
```

Example:
```bash
# Convert all CSVs in a directory to Excel
python csv_to_excel.py /path/to/csv/folder/
```

The Excel output will include specific columns for accounting/budgeting:
- **Date**: Recognized Excel date format
- **Debit amount**: Negative values (expenses)
- **Credit amount**: Positive values (income)
- **Saldo**: The balance column
- **Calculated saldo**: Copy of balance
- **transaction description**: The original description

### Convert for Cashflow Tracker Import

```bash
python to_cashflow_tracker.py <path_to_file_or_folder>
```

Converts this repo's CSV or Excel output into the Excel-format CSV that
[`cashflow_tracker`](https://github.com/ebendl/cashflow_tracker) imports
(`POST /api/v1/import/preview` then `/commit`, or its seed runner).

```bash
# One statement file (.csv or .xlsx) -> FIRST_..._65_cashflow.csv
python to_cashflow_tracker.py /path/to/FIRST_BUSINESS_ZERO_ACCOUNT_65.csv

# A whole folder (one account) -> a single combined <FolderName>_cashflow.csv
python to_cashflow_tracker.py /path/to/statement/folder/

# ...or one output file per statement instead of a combined one
python to_cashflow_tracker.py /path/to/statement/folder/ --per-file
```

Output columns: `Salary Month, Salary, Date, Debit, Credit, Saldo, Calc Saldo,
Bank Note, Split, Category, Booked, Note`

- `Date` is written as `03 Aug`, the format the importer expects
- `Debit` holds negative amounts, `Credit` positive; the unused side gets `-`
- `Saldo` and `Calc Saldo` both carry the statement balance
- `Bank Note` holds the transaction description
- `Split`, `Category`, `Booked` and `Note` are left blank for categorisation in the app

**`Salary Month` is left blank and must be filled in by hand before importing.**
The importer skips rows with a blank salary month, and infers each transaction's
year from it (the `Date` column carries no year).

When given a folder, the script reads one file per statement — preferring the
`.csv` where both a `.csv` and `.xlsx` exist — and skips `combined_transactions.*`
and its own `*_cashflow.csv` output, so re-running it is safe.

## Output Format

The script generates a CSV file with the following columns:
- `date`: Transaction date in YYYY-MM-DD format
- `description`: Transaction description
- `amount`: Transaction amount (positive for credits, negative for debits)
- `balance`: Account balance after transaction

The CSV uses semicolons (`;`) as field separators.

## Sample Files

The `samples/` directory contains example PDF files and their expected CSV outputs for testing.

## Requirements

- Python 3.8+
- Google Gemini API key
- PDF files containing bank statement data

