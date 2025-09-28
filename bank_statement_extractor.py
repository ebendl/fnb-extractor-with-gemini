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
              - If the balance has "Kt" or "Cr" it's a credit (positive value)
              - Otherwise it's a debit (negative value)
            
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
        print("Usage: python bank_statement_extractor.py <pdf_file_path>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    # Validate PDF file exists
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file '{pdf_path}' not found.")
        sys.exit(1)
    
    # Create extractor instance
    extractor = BankStatementExtractor(api_key)
    
    # Extract transactions
    print(f"Extracting transactions from {pdf_path}...")
    transactions = extractor.extract_transactions_from_pdf(pdf_path)
    
    if not transactions:
        print("No transactions found or extraction failed.")
        sys.exit(1)
    
    # Generate output filename
    pdf_file = Path(pdf_path)
    output_path = pdf_file.with_suffix('.csv')
    
    # Save to CSV
    extractor.save_transactions_to_csv(transactions, str(output_path))
    
    print(f"Extraction complete! Found {len(transactions)} transactions.")
    print(f"Output saved to: {output_path}")


if __name__ == "__main__":
    main()
