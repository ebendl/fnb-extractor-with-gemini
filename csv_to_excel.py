#!/usr/bin/env python3
"""
CSV to Excel Converter

This script converts standardized CSV bank statements (date, description, amount, balance)
into a specifically formatted Excel (.xlsx) file.
"""

import os
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime

def convert_csv_to_excel(csv_path: str):
    """
    Converts a single CSV file to Excel with specific formatting.
    """
    try:
        path = Path(csv_path)
        if not path.exists():
            print(f"Error: File '{csv_path}' not found.")
            return False

        print(f"📄 Processing: {path.name}")
        
        # Read CSV with semicolon delimiter
        df = pd.read_csv(csv_path, sep=';')
        
        # Ensure required columns exist
        required_cols = ['date', 'description', 'amount', 'balance']
        for col in required_cols:
            if col not in df.columns:
                print(f"Error: Column '{col}' not found in {path.name}. Is this a standardized CSV?")
                return False

        # 1. Date in ISO format, recognized as Excel date
        df['Date'] = pd.to_datetime(df['date'])
        
        # 2. Debit amount: negative -> value, else 0
        df['Debit amount'] = df['amount'].apply(lambda x: x if x < 0 else 0.0)
        
        # 3. Credit amount: positive -> value, else 0
        df['Credit amount'] = df['amount'].apply(lambda x: x if x > 0 else 0.0)
        
        # 4. Saldo: same as existing 'balance'
        df['Saldo'] = df['balance']
        
        # 5. Calculated saldo: same as 'saldo'
        df['Calculated saldo'] = df['balance']
        
        # 6. transaction description: same as 'description'
        df['transaction description'] = df['description']
        
        # Select and order the requested columns
        output_df = df[['Date', 'Debit amount', 'Credit amount', 'Saldo', 'Calculated saldo', 'transaction description']]
        
        # Output filename: same as input but .xlsx
        output_path = path.with_suffix('.xlsx')
        
        # Save to Excel
        # Using xlsxwriter if available, otherwise default
        output_df.to_excel(output_path, index=False, sheet_name='Transactions')
        
        # Auto-format column widths (optional but nice for premium feel)
        # We can't easily do this without xlsxwriter/openpyxl engine access, 
        # but the basic export works fine.
        
        print(f"✅ Saved to: {output_path.name}")
        return True

    except Exception as e:
        print(f"❌ Error converting {csv_path}: {e}")
        return False

def main():
    if len(sys.argv) != 2:
        print("Usage: python csv_to_excel.py <csv_file_or_directory>")
        sys.exit(1)
        
    input_path = sys.argv[1]
    path = Path(input_path)
    
    if path.is_file():
        if path.suffix.lower() == '.csv':
            convert_csv_to_excel(str(path))
        else:
            print(f"Error: '{input_path}' is not a CSV file.")
    elif path.is_dir():
        csv_files = list(path.glob("*.csv"))
        if not csv_files:
            print(f"No CSV files found in directory: {input_path}")
            return
            
        print(f"🔍 Found {len(csv_files)} CSV files in {input_path}")
        success_count = 0
        for csv_file in csv_files:
            # Skip combined files or intermediate files if needed, 
            # but usually we want to convert everything in the folder.
            if convert_csv_to_excel(str(csv_file)):
                success_count += 1
        
        print(f"\n✨ Successfully converted {success_count} out of {len(csv_files)} files.")
    else:
        print(f"Error: Path '{input_path}' not found.")
        sys.exit(1)

if __name__ == "__main__":
    main()
