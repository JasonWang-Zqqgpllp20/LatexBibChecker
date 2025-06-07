import re
import os
import sys
from typing import List

from html_show import html_open
from bib_read import BibEntry, Article, InProceedings, Book
from check_bib import check

class BibParser:
    """Parser for BibTeX files."""
    
    @staticmethod
    def parse_file(file_path: str = "input.bib") -> List[BibEntry]:
        """
        Parse a BibTeX file and return a list of BibEntry objects.
        
        Args:
            file_path: Path to the BibTeX file (default: "input.bib")
            
        Returns:
            List of BibEntry objects
        """
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Remove comments
        content = re.sub(r'%.*?$', '', content, flags=re.MULTILINE)
        
        # Normalize line endings and ensure content ends with a newline
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        if not content.endswith('\n'):
            content += '\n'
        
        # Pattern to match BibTeX entries
        entry_pattern = re.compile(
            r'@(?P<entry_type>\w+)\{(?P<citation_key>[^,]+),\s*'
            r'(?P<fields>.*?)'
            r'(?=\n@|\n\s*\Z|\Z)',  # Modified to handle end of file
            re.DOTALL
        )
        
        # Pattern to match fields
        field_pattern = re.compile(
            r'(?P<key>\w+)\s*=\s*'
            r'(?P<value>\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\}|"[^"]*"|\d+),?',
            re.DOTALL
        )
        
        entries = []
        
        for entry_match in entry_pattern.finditer(content):
            entry_type = entry_match.group('entry_type').lower()
            citation_key = entry_match.group('citation_key').strip()
            fields_str = entry_match.group('fields').strip()
            
            fields = {}
            
            for field_match in field_pattern.finditer(fields_str):
                key = field_match.group('key').strip().lower()
                value = field_match.group('value').strip().replace("\n", "")
                
                # Remove surrounding braces or quotes
                if (value.startswith('{') and value.endswith('}')) or \
                    (value.startswith('"') and value.endswith('"')):
                    value = value[1:-1]
                
                fields[key] = value
            
            # Create appropriate entry class based on type
            if entry_type == "article":
                entries.append(Article(citation_key, fields))
            elif entry_type == "inproceedings":
                entries.append(InProceedings(citation_key, fields))
            elif entry_type == "book":
                entries.append(Book(citation_key, fields))
            else:
                ...
                # entries.append(Others(entry_type, citation_key, fields))
        
        return entries

if __name__ == "__main__":
    # input args
    input_bib_file = "input.bib"
    
    if not os.path.exists(input_bib_file):
        print(f"Error: File '{input_bib_file}' does not exist.")
        sys.exit()
    
    entries = BibParser.parse_file(input_bib_file)
    entries = check(entries=entries)
    html_open(entries=entries)