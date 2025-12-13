#!/usr/bin/env python3
"""
TaxCut .T03 File Converter
Converts TaxCut .T03 binary files to readable text format
"""

import struct
import re
import sys
from pathlib import Path

class T03Converter:
    def __init__(self, filename):
        self.filename = filename
        self.data = None
        self.parsed_data = []
        
        # 2003 Form 1040 line mappings
        self.form_1040_lines = {
            '7': 'Wages, salaries, tips, etc.',
            '8a': 'Taxable interest',
            '8b': 'Tax-exempt interest',
            '9a': 'Ordinary dividends',
            '9b': 'Qualified dividends',
            '10': 'Taxable refunds, credits, or offsets of state and local income taxes',
            '11': 'Alimony received',
            '12': 'Business income or (loss)',
            '13a': 'Capital gain or (loss)',
            '13b': 'Post-May 5 capital gain distributions',
            '14': 'Other gains or (losses)',
            '15a': 'IRA distributions',
            '15b': 'IRA distributions - taxable amount',
            '16a': 'Pensions and annuities',
            '16b': 'Pensions and annuities - taxable amount',
            '17': 'Rental real estate, royalties, partnerships, S corporations, trusts, etc.',
            '18': 'Farm income or (loss)',
            '19': 'Unemployment compensation',
            '20a': 'Social security benefits',
            '20b': 'Social security benefits - taxable amount',
            '21': 'Other income',
            '22': 'Total income',
            '23': 'Educator expenses',
            '24': 'IRA deduction',
            '25': 'Student loan interest deduction',
            '26': 'Tuition and fees deduction',
            '27': 'Moving expenses',
            '28': 'One-half of self-employment tax',
            '29': 'Self-employed health insurance deduction',
            '30': 'Self-employed SEP, SIMPLE, and qualified plans',
            '31': 'Penalty on early withdrawal of savings',
            '32a': 'Alimony paid',
            '33': 'Total adjustments',
            '34': 'Adjusted gross income',
            '35': 'Amount from line 34 (adjusted gross income)',
            '36a': 'Standard deduction or itemized deductions',
            '37': 'Subtract line 37 from line 35',
            '38': 'Exemptions',
            '39': 'Exemption amount',
            '40': 'Taxable income',
            '41': 'Tax',
            '42': 'Alternative minimum tax',
            '43': 'Add lines 41 and 42',
            '44': 'Foreign tax credit',
            '45': 'Credit for child and dependent care expenses',
            '46': 'Credit for the elderly or the disabled',
            '47': 'Education credits',
            '48': 'Retirement savings contributions credit',
            '49': 'Child tax credit',
            '50': 'Adoption credit',
            '51': 'Credits from other forms',
            '52': 'Other credits',
            '53': 'Total credits',
            '54': 'Subtract line 53 from line 43',
            '55': 'Self-employment tax',
            '56': 'Social security and Medicare tax on tip income',
            '57': 'Tax on qualified plans',
            '58': 'Advance earned income credit payments',
            '59': 'Household employment taxes',
            '60': 'Total tax',
            '61': 'Federal income tax withheld',
            '62': '2003 estimated tax payments',
            '63': 'Earned income credit (EIC)',
            '64': 'Excess social security and tier 1 RRTA tax withheld',
            '65': 'Additional child tax credit',
            '66': 'Amount paid with request for extension to file',
            '67': 'Other payments',
            '68': 'Total payments',
            '69': 'Amount overpaid',
            '70a': 'Amount to be refunded',
            '71': 'Amount applied to 2004 estimated tax',
            '72': 'Amount you owe',
            '73': 'Estimated tax penalty'
        }
        
    def read_file(self):
        """Read the binary .T03 file"""
        try:
            with open(self.filename, 'rb') as f:
                self.data = f.read()
            print(f"Successfully read {len(self.data)} bytes from {self.filename}")
            return True
        except FileNotFoundError:
            print(f"Error: File '{self.filename}' not found")
            return False
        except Exception as e:
            print(f"Error reading file: {e}")
            return False
    
    def extract_strings(self):
        """Extract readable strings from the binary data"""
        strings = []
        
        # Extract printable ASCII strings (minimum length 3)
        ascii_pattern = re.compile(b'[ -~]{3,}')
        matches = ascii_pattern.findall(self.data)
        
        for match in matches:
            try:
                decoded = match.decode('ascii').strip()
                if decoded and not decoded.isspace():
                    strings.append(decoded)
            except UnicodeDecodeError:
                continue
                
        return strings
    
    def extract_numbers_with_context(self):
        """Extract numeric values with their byte positions and surrounding context"""
        numbers_with_context = []
        
        # Look for patterns that might be monetary amounts with context
        number_pattern = re.compile(rb'\s+(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*\x00')
        
        for match in number_pattern.finditer(self.data):
            try:
                number_str = match.group(1).decode('ascii')
                byte_pos = match.start()
                
                # Look for context before and after the number (wider range)
                context_start = max(0, byte_pos - 200)
                context_end = min(len(self.data), match.end() + 200)
                context_bytes = self.data[context_start:context_end]
                
                # Extract readable strings from context
                context_strings = []
                form_references = []
                
                ascii_pattern = re.compile(b'[ -~]{3,}')
                context_matches = ascii_pattern.findall(context_bytes)
                
                for ctx_match in context_matches:
                    try:
                        decoded = ctx_match.decode('ascii').strip()
                        if decoded and not decoded.isspace() and decoded != number_str:
                            # Look for form line numbers or descriptions
                            if (re.match(r'\d{1,4}[A-Z]*$', decoded) or 
                                'FORM' in decoded.upper() or 
                                'LINE' in decoded.upper() or
                                'SCHEDULE' in decoded.upper() or
                                any(keyword in decoded.upper() for keyword in 
                                    ['WAGES', 'INTEREST', 'DIVIDEND', 'INCOME', 'TAX', 'DEDUCTION', 
                                     'CREDIT', 'REFUND', 'FEDERAL', 'STATE', 'WITHHOLDING'])):
                                form_references.append(decoded)
                            else:
                                context_strings.append(decoded)
                    except UnicodeDecodeError:
                        continue
                
                # Prioritize form references, then other context
                best_context = form_references[:3] + context_strings[:2]
                
                numbers_with_context.append({
                    'amount': number_str,
                    'byte_position': byte_pos,
                    'context': best_context[:5],  # Limit to 5 total context items
                    'form_refs': form_references[:3]  # Keep separate form references
                })
                
            except UnicodeDecodeError:
                continue
                
        return numbers_with_context
    
    def categorize_data(self, strings):
        """Categorize extracted strings by type"""
        categories = {
            'personal_info': [],
            'addresses': [],
            'tax_amounts': [],
            'form_fields': [],
            'dates': [],
            'other': []
        }
        
        for s in strings:
            # SSN pattern
            if re.match(r'\d{3}-\d{2}-\d{4}', s):
                categories['personal_info'].append(f"SSN: {s}")
            # Phone number pattern
            elif re.match(r'\d{3}-\d{3}-\d{4}', s):
                categories['personal_info'].append(f"Phone: {s}")
            # Date patterns
            elif re.match(r'\d{2}/\d{2}/\d{4}', s):
                categories['dates'].append(f"Date: {s}")
            # Monetary amounts
            elif re.match(r'^\s*\d{1,3}(,\d{3})*(\.\d{2})?\s*$', s):
                categories['tax_amounts'].append(f"Amount: ${s.strip()}")
            # Address-like strings
            elif any(word in s.upper() for word in ['WAY', 'LANE', 'STREET', 'ST', 'AVE', 'DRIVE', 'DR']):
                categories['addresses'].append(f"Address: {s}")
            # Names (capitalized words)
            elif s.istitle() and len(s.split()) <= 3:
                categories['personal_info'].append(f"Name: {s}")
            # Form-related strings
            elif any(word in s.upper() for word in ['FORM', 'SCHEDULE', 'LINE', 'WORKSHEET']):
                categories['form_fields'].append(f"Form Info: {s}")
            else:
                categories['other'].append(s)
                
        return categories
    
    def convert_to_text(self, output_filename=None):
        """Main conversion method"""
        if not self.read_file():
            return False
            
        if output_filename is None:
            base_name = Path(self.filename).stem
            output_filename = f"{base_name}_converted.txt"
        
        strings = self.extract_strings()
        numbers_with_context = self.extract_numbers_with_context()
        categories = self.categorize_data(strings)
        
        try:
            with open(output_filename, 'w', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write(f"TaxCut .T03 File Conversion Report\n")
                f.write(f"Source File: {self.filename}\n")
                f.write(f"File Size: {len(self.data)} bytes\n")
                f.write("=" * 60 + "\n\n")
                
                # Personal Information
                if categories['personal_info']:
                    f.write("PERSONAL INFORMATION:\n")
                    f.write("-" * 25 + "\n")
                    for item in categories['personal_info']:
                        f.write(f"  {item}\n")
                    f.write("\n")
                
                # Addresses
                if categories['addresses']:
                    f.write("ADDRESSES:\n")
                    f.write("-" * 10 + "\n")
                    for item in categories['addresses']:
                        f.write(f"  {item}\n")
                    f.write("\n")
                
                # Dates
                if categories['dates']:
                    f.write("DATES:\n")
                    f.write("-" * 6 + "\n")
                    for item in categories['dates']:
                        f.write(f"  {item}\n")
                    f.write("\n")
                
                # Tax Amounts with Context
                if categories['tax_amounts'] or numbers_with_context:
                    f.write("MONETARY AMOUNTS WITH CONTEXT:\n")
                    f.write("-" * 31 + "\n")
                    
                    # Show amounts from categories first
                    for item in categories['tax_amounts']:
                        f.write(f"  {item}\n")
                    
                    # Show detailed amounts with context and positions
                    f.write("\nDETAILED AMOUNTS (with byte positions and context):\n")
                    f.write("-" * 52 + "\n")
                    
                    for i, num_data in enumerate(numbers_with_context, 1):
                        f.write(f"  {i:2d}. Amount: ${num_data['amount']:<12} (Byte: {num_data['byte_position']:>5})\n")
                        
                        if num_data['form_refs']:
                            f.write(f"      Form/Line: {', '.join(num_data['form_refs'])}\n")
                            
                            # Check if any form references match known 1040 lines
                            for ref in num_data['form_refs']:
                                # Extract potential line numbers
                                line_match = re.search(r'\b(\d{1,3}[a-zA-Z]?)\b', ref)
                                if line_match:
                                    line_num = line_match.group(1)
                                    if line_num in self.form_1040_lines:
                                        f.write(f"      → Line {line_num}: {self.form_1040_lines[line_num]}\n")
                        
                        if num_data['context']:
                            f.write(f"      Context: {', '.join(num_data['context'])}\n")
                        else:
                            f.write(f"      Context: [No readable context found]\n")
                        f.write("\n")
                    
                    f.write("\n")
                
                # Summary of amounts by line number
                f.write("SUMMARY BY FORM LINE:\n")
                f.write("-" * 20 + "\n")
                
                line_amounts = {}
                for num_data in numbers_with_context:
                    if num_data['form_refs']:
                        for ref in num_data['form_refs']:
                            line_match = re.search(r'\b(\d{1,4}[a-zA-Z]?)\b', ref)
                            if line_match:
                                line_num = line_match.group(1)
                                if line_num not in line_amounts:
                                    line_amounts[line_num] = []
                                line_amounts[line_num].append(num_data['amount'])
                
                for line_num in sorted(line_amounts.keys(), key=lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else 0):
                    amounts = line_amounts[line_num]
                    f.write(f"  Line {line_num}: {', '.join([f'${amt}' for amt in amounts])}")
                    if line_num in self.form_1040_lines:
                        f.write(f" - {self.form_1040_lines[line_num]}")
                    else:
                        f.write(f" - [Unknown line - possibly from Schedule or other form]")
                    f.write(f" ({len(amounts)} amount{'s' if len(amounts) != 1 else ''})\n")
                f.write("\n")
                
                # Form Fields
                if categories['form_fields']:
                    f.write("FORM INFORMATION:\n")
                    f.write("-" * 16 + "\n")
                    for item in categories['form_fields']:
                        f.write(f"  {item}\n")
                    f.write("\n")
                
                # Other Data
                if categories['other']:
                    f.write("OTHER DATA:\n")
                    f.write("-" * 11 + "\n")
                    for item in categories['other']:
                        if len(item) > 2:  # Filter out very short strings
                            f.write(f"  {item}\n")
                    f.write("\n")
                
                # Raw strings section for reference
                f.write("RAW EXTRACTED STRINGS:\n")
                f.write("-" * 22 + "\n")
                for i, string in enumerate(strings[:50], 1):  # Limit to first 50 strings
                    f.write(f"  {i:2d}. {string}\n")
                if len(strings) > 50:
                    f.write(f"  ... and {len(strings) - 50} more strings\n")
                
            print(f"Conversion completed! Output saved to: {output_filename}")
            return True
            
        except Exception as e:
            print(f"Error writing output file: {e}")
            return False

def main():
    if len(sys.argv) != 2:
        print("Usage: python tax_formater.py <filename.T03>")
        sys.exit(1)
    
    filename = sys.argv[1]
    converter = T03Converter(filename)
    
    if converter.convert_to_text():
        print("Conversion successful!")
    else:
        print("Conversion failed!")
        sys.exit(1)

if __name__ == "__main__":
    # If run directly, check for command line arguments
    if len(sys.argv) > 1:
        main()
    else:
        # Default to the known file in the directory
        filename = "Andrew Hopkins's Taxes.T03"
        if Path(filename).exists():
            converter = T03Converter(filename)
            converter.convert_to_text()
        else:
            print(f"File '{filename}' not found. Please provide a filename as an argument.")