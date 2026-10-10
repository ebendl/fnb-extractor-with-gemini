#!/usr/bin/env python3
"""
FNB Cheque Account CSV Converter

This script converts FNB's emailed cheque account CSV files 
into a standardized CSV format (ISO date, description, amount, balance)
using semicolons as delimiters.
"""

import os
import sys
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

def parse_fnb_csv(file_path: str) -> List[Dict[str, Any]]:
    """
    Parses an FNB emailed CSV file and extracts transactions.
    """
    transactions = []
    
    from_date_str = None
    to_date_str = None
    
    with open(file_path, 'r', encoding='utf-8') as f:
        # FNB CSVs often have mixed quotes, single quotes for some fields, double for others.
        # We can just read rows and strip single quotes from specific fields.
        reader = csv.reader(f, delimiter=',')
        
        from_date = None
        to_date = None
        current_year = None
        last_month = None
        
        for row in reader:
            if not row:
                continue
                
            row_type = row[0].strip("' ")
            
            # Row type 3 has from and to dates in the second row (after headers)
            if row_type == '3' and len(row) >= 5:
                # Check if it's the data row by checking if second col is a statement number
                if row[1].strip("' ").isdigit():
                    from_date_str = row[2].strip("' ")
                    to_date_str = row[3].strip("' ")
                    
                    try:
                        from_date = datetime.strptime(from_date_str, '%d %B %Y')
                        to_date = datetime.strptime(to_date_str, '%d %B %Y')
                        current_year = from_date.year
                        last_month = from_date.month
                    except ValueError as e:
                        print(f"Warning: Could not parse dates in row 3: {e}")
            
            # Row type 5 contains transactions
            elif row_type == '5' and len(row) >= 8:
                # Check if it's a data row and not the header
                num_col = row[1].strip("' ")
                if num_col.isdigit():
                    date_val = row[2].strip("' ")
                    desc1 = row[3].strip("' ")
                    desc2 = row[4].strip("' ") if len(row) > 4 else ""
                    
                    amount_val = row[6].strip("' ")
                    balance_val = row[7].strip("' ")
                    
                    # Combine descriptions
                    description = desc1
                    if desc2:
                        description += " " + desc2
                        
                    # Parse date and determine year
                    try:
                        # expected format: '02 Oct'
                        dt = datetime.strptime(date_val, '%d %b')
                        
                        # Handle year transition
                        if last_month is not None:
                            # if we go from Dec (12) to Jan (1), increment year
                            if last_month == 12 and dt.month == 1:
                                current_year += 1
                            # if we go from Jan (1) to Dec (12), which shouldn't normally happen
                            # in chronological order, but just in case
                            elif last_month == 1 and dt.month == 12:
                                current_year -= 1
                                
                        last_month = dt.month
                        iso_date = dt.replace(year=current_year).strftime('%Y-%m-%d')
                    except ValueError:
                        print(f"Warning: Could not parse transaction date '{date_val}', keeping as is.")
                        iso_date = date_val
                        
                    # Clean up amount and balance
                    try:
                        amount = float(amount_val)
                        balance = float(balance_val)
                    except ValueError:
                        print(f"Warning: Could not parse amount or balance: {amount_val}, {balance_val}")
                        amount = 0.0
                        balance = 0.0
                        
                    transactions.append({
                        'date': iso_date,
                        'description': description,
                        'amount': amount,
                        'balance': balance
                    })
                    
    return transactions

def process_file(file_path: str) -> bool:
    try:
        input_path = Path(file_path)
        
        # Explicitly skip already converted files or backup files
        if input_path.name.endswith('_emailed.csv') or input_path.name.endswith('_converted.csv'):
            return False
            
        # Quick check for the expected FNB CSV format (starts with 2,...)
        with open(file_path, 'r', encoding='utf-8') as f:
            first_line = f.readline()
            if not first_line.startswith('2,'):
                # We can silently skip non-FNB CSVs rather than printing an error for every CSV
                return False
                
        print(f"\nProcessing: {input_path.name}")
        transactions = parse_fnb_csv(file_path)
        
        if not transactions:
            print("No transactions found.")
            return False
            
        # Rename original file to _emailed.csv
        backup_path = input_path.parent / (input_path.stem + "_emailed.csv")
        os.rename(input_path, backup_path)
        
        # Output converted data to the original filename
        output_path = input_path
        
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile, delimiter=';')
            writer.writerow(['date', 'description', 'amount', 'balance'])
            
            for t in transactions:
                # Format without thousands separators, decimal period
                amt_str = f"{t['amount']:.2f}"
                bal_str = f"{t['balance']:.2f}"
                writer.writerow([t['date'], t['description'], amt_str, bal_str])
                
        print(f"Saved {len(transactions)} transactions to {output_path.name} (original backed up as {backup_path.name})")
        return True
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    if len(sys.argv) != 2:
        print("Usage: python fnb_cheque_csv_converter.py <folder_path_or_file>")
        sys.exit(1)
        
    input_path = sys.argv[1]
    
    if os.path.isfile(input_path):
        process_file(input_path)
    elif os.path.isdir(input_path):
        folder = Path(input_path)
        files = list(folder.glob("*.csv"))
        if not files:
            print(f"No CSV files found in {folder}")
            sys.exit(0)
            
        success = 0
        for f in files:
            if process_file(str(f)):
                success += 1
                
        print(f"\nSuccessfully processed {success} files.")
    else:
        print(f"Error: Path '{input_path}' not found.")
        sys.exit(1)

if __name__ == "__main__":
    main()
