#!/usr/bin/env python3
"""
CSV File Combiner

This script combines all CSV files in a directory into a single combined CSV file.
It reads all CSV files with semicolon separators and merges them into one file.
"""

import os
import sys
import csv
from pathlib import Path
from typing import List


def find_csv_files(directory_path: str) -> List[Path]:
    """
    Find all CSV files in a directory.
    
    Args:
        directory_path: Path to the directory to scan
        
    Returns:
        List of CSV file paths
    """
    directory = Path(directory_path)
    
    if not directory.exists():
        print(f"Error: Directory '{directory_path}' not found.")
        return []
    
    if not directory.is_dir():
        print(f"Error: '{directory_path}' is not a directory.")
        return []
    
    csv_files = list(directory.glob("*.csv"))
    
    # Exclude the output file if it already exists
    output_file = directory / "combined_transactions.csv"
    csv_files = [f for f in csv_files if f != output_file]
    
    # Sort CSV files by filename to ensure chronological order
    csv_files.sort(key=lambda x: x.name)
    
    return csv_files


def combine_csv_files(csv_files: List[Path], output_path: str) -> bool:
    """
    Combine multiple CSV files into a single CSV file.
    
    Args:
        csv_files: List of CSV file paths to combine
        output_path: Path for the output combined CSV file
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not csv_files:
        print("No CSV files found to combine.")
        return False
    
    try:
        combined_data = []
        total_rows = 0
        
        print(f"📊 Combining {len(csv_files)} CSV files...")
        
        for i, csv_file in enumerate(csv_files, 1):
            print(f"   📄 Reading {csv_file.name}...")
            
            try:
                # Read CSV with semicolon separator
                with open(csv_file, 'r', encoding='utf-8') as file:
                    reader = csv.reader(file, delimiter=';')
                    rows = list(reader)
                    
                    # Skip header for all files except the first one
                    if i == 1:
                        # First file: include header and all data
                        combined_data.extend(rows)
                        total_rows += len(rows)
                        print(f"      ✅ Added {len(rows)} rows (including header)")
                    else:
                        # Subsequent files: skip header, add only data
                        if len(rows) > 1:  # Has header + data
                            data_rows = rows[1:]  # Skip header
                            combined_data.extend(data_rows)
                            total_rows += len(data_rows)
                            print(f"      ✅ Added {len(data_rows)} rows (skipped header)")
                        elif len(rows) == 1:  # Only header
                            print(f"      ⚠️  File has only header, no data")
                        else:  # Empty file
                            print(f"      ⚠️  File is empty")
                            
            except Exception as e:
                print(f"      ❌ Error reading {csv_file.name}: {str(e)}")
                continue
        
        if not combined_data:
            print("❌ No data to write - all files were empty or had errors.")
            return False
        
        # Write combined data to output file
        print(f"\n💾 Writing combined data to {output_path}...")
        with open(output_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file, delimiter=';')
            writer.writerows(combined_data)
        
        print(f"✅ Successfully combined {len(csv_files)} CSV files")
        print(f"   📊 Total rows: {len(combined_data)}")
        print(f"   📄 Output file: {output_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error combining CSV files: {str(e)}")
        return False


def main():
    """Main function to run the CSV combiner."""
    
    # Check command line arguments
    if len(sys.argv) != 2:
        print("Usage: python combine_csv_files.py <directory_path>")
        print("       Combines all CSV files in the directory into 'combined_transactions.csv'")
        sys.exit(1)
    
    directory_path = sys.argv[1]
    
    # Validate directory exists
    if not os.path.exists(directory_path):
        print(f"Error: Directory '{directory_path}' not found.")
        sys.exit(1)
    
    if not os.path.isdir(directory_path):
        print(f"Error: '{directory_path}' is not a directory.")
        sys.exit(1)
    
    # Find CSV files
    print(f"🔍 Scanning directory: {directory_path}")
    csv_files = find_csv_files(directory_path)
    
    if not csv_files:
        print("❌ No CSV files found in the directory.")
        sys.exit(1)
    
    print(f"   Found {len(csv_files)} CSV files:")
    for csv_file in csv_files:
        print(f"   📄 {csv_file.name}")
    
    # Generate output filename
    output_path = Path(directory_path) / "combined_transactions.csv"
    
    # Combine CSV files
    success = combine_csv_files(csv_files, str(output_path))
    
    if success:
        print(f"\n🎯 CSV Combination Complete!")
        print(f"   📁 Directory: {directory_path}")
        print(f"   📊 Files combined: {len(csv_files)}")
        print(f"   📄 Output file: {output_path}")
    else:
        print(f"\n❌ CSV combination failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
