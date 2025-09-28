# Bank Statement PDF Extractor

A Python script that uses Google's Gemini 2.5 Flash model to extract transaction data from bank statement PDFs and convert them to CSV format.

## Features

- Extracts transactions from PDF bank statements using AI
- Uses Google's Gemini 2.5 Flash model with structured output
- Converts data to CSV format with semicolon separators
- Handles credit/debit amounts correctly
- Validates date formats and numeric values

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

```bash
python bank_statement_extractor.py <path_to_pdf_file>
```

Example:
```bash
python bank_statement_extractor.py samples/FNB_FUSION_PRIVATE_CLIENTS_ACC_226.pdf
```

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

