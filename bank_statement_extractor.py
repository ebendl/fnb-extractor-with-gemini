#!/usr/bin/env python3
"""
Bank Statement PDF Extractor using Google Gemini API

This script extracts transaction data from bank statement PDFs using Google's Gemini 2.5 Flash model
with structured output via Pydantic models.
"""

import os
import sys
import csv
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import re

from google import genai
from google.genai import types
from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv


class Transaction(BaseModel):
    """Pydantic model for bank transaction data."""
    
    date: str = Field(description="Transaction date in YYYY-MM-DD format")
    description: str = Field(description="Transaction description")
    amount: float = Field(description="Transaction amount (positive for credits, negative for debits)")
    balance: float = Field(description="Account balance after transaction")
    
    @field_validator('date')
    @classmethod
    def validate_date(cls, v):
        """Validate date format."""
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('Date must be in YYYY-MM-DD format')
    
    @field_validator('amount', 'balance')
    @classmethod
    def validate_amounts(cls, v):
        """Validate amount format."""
        if not isinstance(v, (int, float)):
            raise ValueError('Amount must be a number')
        return float(v)


class TransactionValidator:
    """Validator for checking transaction balance consistency with smart sign correction."""
    
    @staticmethod
    def validate_transaction_balances(transactions: List[Transaction]) -> bool:
        """
        Validate that transaction balances are mathematically consistent.
        Automatically corrects sign errors in extracted balances.
        
        Args:
            transactions: List of Transaction objects (will be modified in place if corrections are made)
            
        Returns:
            bool: True if balances are consistent, False otherwise
        """
        if not transactions:
            print("No transactions to validate")
            return False
        
        # Sort transactions by date to ensure proper order
        sorted_transactions = sorted(transactions, key=lambda x: x.date)
        
        # Start with the first transaction's balance minus its amount to get the starting balance
        first_transaction = sorted_transactions[0]
        calculated_balance = first_transaction.balance - first_transaction.amount
        
        print(f"Starting balance: {calculated_balance:.2f}")
        print(f"First transaction: {first_transaction.amount:.2f} -> Balance: {first_transaction.balance:.2f}")
        
        # Validate each subsequent transaction
        for i, transaction in enumerate(sorted_transactions):
            # Add the transaction amount to get the new balance
            calculated_balance += transaction.amount
            
            # Check if the calculated balance matches the extracted balance (within 1 cent tolerance)
            balance_difference = abs(calculated_balance - transaction.balance)
            
            if balance_difference > 0.01:  # More than 1 cent difference
                # Check if the issue is just a sign error (same absolute value, different sign)
                if abs(abs(calculated_balance) - abs(transaction.balance)) <= 0.01:
                    # This is likely a sign error - try correcting it
                    corrected_balance = -transaction.balance
                    corrected_difference = abs(calculated_balance - corrected_balance)
                    
                    if corrected_difference <= 0.01:  # Correction works!
                        print(f"🔧 Sign correction applied at transaction {i+1}:")
                        print(f"   Date: {transaction.date}")
                        print(f"   Description: {transaction.description}")
                        print(f"   Amount: {transaction.amount:.2f}")
                        print(f"   Original balance: {transaction.balance:.2f}")
                        print(f"   Corrected balance: {corrected_balance:.2f}")
                        print(f"   Expected balance: {calculated_balance:.2f}")
                        print(f"   Difference after correction: {corrected_difference:.4f}")
                        
                        # Update the transaction with the corrected balance
                        transaction.balance = corrected_balance
                        calculated_balance = corrected_balance
                        print(f"✓ Transaction {i+1}: {transaction.amount:.2f} -> Balance: {transaction.balance:.2f} (corrected)")
                        continue
                
                # If we get here, it's not a simple sign error
                print(f"❌ Balance validation failed at transaction {i+1}:")
                print(f"   Date: {transaction.date}")
                print(f"   Description: {transaction.description}")
                print(f"   Amount: {transaction.amount:.2f}")
                print(f"   Expected balance: {calculated_balance:.2f}")
                print(f"   Extracted balance: {transaction.balance:.2f}")
                print(f"   Difference: {balance_difference:.2f}")
                return False
            else:
                print(f"✓ Transaction {i+1}: {transaction.amount:.2f} -> Balance: {transaction.balance:.2f} (diff: {balance_difference:.4f})")
        
        print(f"✅ All {len(transactions)} transactions validated successfully!")
        print(f"Final balance: {calculated_balance:.2f}")
        return True


class BankStatementExtractor:
    """Main class for extracting bank statement data from PDFs."""
    
    def __init__(self, api_key: str):
        """Initialize the extractor with Gemini API key."""
        self.client = genai.Client(api_key=api_key)
    
    def extract_transactions_from_pdf(self, pdf_path: str) -> List[Transaction]:
        """
        Extract transactions from a PDF bank statement.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of Transaction objects
        """
        try:
            # Create the prompt for Gemini
            prompt = """
            Extract all bank transactions from this PDF bank statement. 
            
            For each transaction, extract:
            - Date (convert to YYYY-MM-DD format)
            - Description (full transaction description)
            - Amount (convert to decimal format with period as decimal separator, no thousands separator)
              - If the amount has "Kt" or "Cr" it's a credit (positive value)
              - Otherwise it's a debit (negative value)
            - Balance (convert to decimal format with period as decimal separator, no thousands separator)
              - CRITICAL: Account balances can be negative (overdrawn)
              - If the balance has "Kt" or "Cr" it's a credit (positive value)
              - If the balance appears without "Kt" or "Cr", or in parentheses () or with a minus sign, it's negative
              - If the account is overdrawn (negative balance), the balance should be negative
              - Consider the mathematical relationship: previous_balance + transaction_amount = new_balance
            
            Only extract actual transaction rows, not headers or summary information.
            Ignore any metadata, account information, or non-transaction data.
            """
            
            # Count tokens before making the request
            contents = [
                types.Part.from_bytes(
                    data=Path(pdf_path).read_bytes(),
                    mime_type='application/pdf',
                ),
                prompt
            ]
            
            # Count tokens before making the request
            token_count = self.client.models.count_tokens(
                model="gemini-2.5-flash",
                contents=contents
            )
            print(f"Request will use approximately {token_count.total_tokens} tokens")
            
            # Generate content using Gemini with structured output
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=contents,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": list[Transaction],
                },
            )
            
            # Parse the structured response
            transactions = response.parsed
            
            # Validate transaction balances
            print("\n🔍 Validating transaction balances...")
            is_valid = TransactionValidator.validate_transaction_balances(transactions)
            
            if is_valid:
                print("✅ Data extraction validation: SUCCESS - All balances are mathematically consistent")
            else:
                print("❌ Data extraction validation: FAILED - Balance inconsistencies detected")
            
            return transactions
            
        except Exception as e:
            print(f"Error extracting transactions from {pdf_path}: {str(e)}")
            return []
    
    def save_transactions_to_csv(self, transactions: List[Transaction], output_path: str):
        """
        Save transactions to CSV file with semicolon separators.
        
        Args:
            transactions: List of Transaction objects
            output_path: Path for the output CSV file
        """
        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile, delimiter=';')
                
                # Write header
                writer.writerow(['date', 'description', 'amount', 'balance'])
                
                # Write transactions
                for transaction in transactions:
                    writer.writerow([
                        transaction.date,
                        transaction.description,
                        transaction.amount,
                        transaction.balance
                    ])
            
            print(f"Successfully saved {len(transactions)} transactions to {output_path}")
            
        except Exception as e:
            print(f"Error saving transactions to CSV: {str(e)}")


def process_single_pdf(extractor: BankStatementExtractor, pdf_path: str) -> bool:
    """
    Process a single PDF file and extract transactions.
    
    Args:
        extractor: BankStatementExtractor instance
        pdf_path: Path to the PDF file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        print(f"\n📄 Processing: {Path(pdf_path).name}")
        print("=" * 60)
        
        # Extract transactions
        transactions = extractor.extract_transactions_from_pdf(pdf_path)
        
        if not transactions:
            print("❌ No transactions found or extraction failed.")
            return False
        
        # Generate output filename
        pdf_file = Path(pdf_path)
        output_path = pdf_file.with_suffix('.csv')
        
        # Save to CSV
        extractor.save_transactions_to_csv(transactions, str(output_path))
        
        print(f"\n📊 Extraction Summary:")
        print(f"   Transactions found: {len(transactions)}")
        print(f"   Output saved to: {output_path}")
        print(f"   Data validation: {'✅ PASSED' if TransactionValidator.validate_transaction_balances(transactions) else '❌ FAILED'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error processing {pdf_path}: {str(e)}")
        return False


def find_pdfs_to_process(folder_path: str) -> List[str]:
    """
    Find all PDF files in a folder that don't have corresponding CSV outputs.
    
    Args:
        folder_path: Path to the folder to scan
        
    Returns:
        List of PDF file paths that need processing
    """
    folder = Path(folder_path)
    
    if not folder.exists():
        print(f"Error: Folder '{folder_path}' not found.")
        return []
    
    if not folder.is_dir():
        print(f"Error: '{folder_path}' is not a directory.")
        return []
    
    pdf_files = list(folder.glob("*.pdf"))
    pdfs_to_process = []
    
    print(f"🔍 Scanning folder: {folder_path}")
    print(f"   Found {len(pdf_files)} PDF files")
    
    for pdf_file in pdf_files:
        csv_file = pdf_file.with_suffix('.csv')
        
        if csv_file.exists():
            print(f"   ⏭️  Skipping {pdf_file.name} (CSV already exists)")
        else:
            print(f"   📋 Queueing {pdf_file.name} for processing")
            pdfs_to_process.append(str(pdf_file))
    
    return pdfs_to_process


def main():
    """Main function to run the bank statement extractor."""
    
    # Load environment variables
    load_dotenv()
    
    # Get API key from environment
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not found.")
        print("Please create a .env file with your Gemini API key.")
        sys.exit(1)
    
    # Check command line arguments
    if len(sys.argv) != 2:
        print("Usage: python bank_statement_extractor.py <folder_path_or_pdf_file>")
        print("       - If folder: processes all PDFs without existing CSV outputs")
        print("       - If file: processes single PDF file")
        sys.exit(1)
    
    input_path = sys.argv[1]
    
    # Validate input path exists
    if not os.path.exists(input_path):
        print(f"Error: Path '{input_path}' not found.")
        sys.exit(1)
    
    # Create extractor instance
    extractor = BankStatementExtractor(api_key)
    
    # Determine if input is a file or folder
    if os.path.isfile(input_path):
        # Single file processing
        if not input_path.lower().endswith('.pdf'):
            print("Error: File must be a PDF.")
            sys.exit(1)
        
        success = process_single_pdf(extractor, input_path)
        sys.exit(0 if success else 1)
    
    else:
        # Folder processing
        pdfs_to_process = find_pdfs_to_process(input_path)
        
        if not pdfs_to_process:
            print("\n✅ No PDFs need processing - all have corresponding CSV files!")
            sys.exit(0)
        
        print(f"\n🚀 Processing {len(pdfs_to_process)} PDF files...")
        
        successful = 0
        failed = 0
        
        for pdf_path in pdfs_to_process:
            if process_single_pdf(extractor, pdf_path):
                successful += 1
            else:
                failed += 1
        
        print(f"\n🎯 Batch Processing Complete:")
        print(f"   ✅ Successful: {successful}")
        print(f"   ❌ Failed: {failed}")
        print(f"   📊 Total: {len(pdfs_to_process)}")
        
        sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
