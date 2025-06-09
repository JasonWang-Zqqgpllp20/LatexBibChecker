import re
import os
import sys
import argparse
from typing import List

from html_show import html_open
from bib_read import BibEntry, Article, InProceedings, Book
from check_bib import check

class BibParser:
    """Parser for BibTeX files with line number tracking."""

    @staticmethod
    def parse_file(file_path: str = "input.bib") -> List[BibEntry]:
        """
        Parse a BibTeX file and return a list of BibEntry objects.

        Args:
            file_path: Path to the BibTeX file (default: "input.bib")

        Returns:
            List of BibEntry objects with line number metadata
        """
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        # Normalize line endings
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        if not content.endswith('\n'):
            content += '\n'

        # Precompute line start positions in the ORIGINAL content
        line_starts = [0]
        for match in re.finditer('\n', content):
            line_starts.append(match.end())

        def get_line_number(pos: int) -> int:
            """Return line number (1-based) for a character offset."""
            for i in range(len(line_starts) - 1):
                if line_starts[i] <= pos < line_starts[i + 1]:
                    return i + 1
            return len(line_starts)

        # Pattern to match BibTeX entries
        entry_pattern = re.compile(
            r'@(?P<entry_type>\w+)\s*\{(?P<citation_key>[^,]+),\s*'
            r'(?P<fields>.*?)'
            r'(?=\n@|\n\s*\Z|\Z)',
            re.DOTALL
        )

        # Pattern to match fields
        field_pattern = re.compile(
            r'(?P<key>\w+)\s*=\s*'
            r'(?P<value>\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\}|"[^"]*"|\d+),?',
            re.DOTALL
        )

        entries = []

        for match in entry_pattern.finditer(content):
            entry_type = match.group('entry_type').lower()
            citation_key = match.group('citation_key').strip()
            fields_str = match.group('fields').strip()

            start_index = match.start()
            line_number = get_line_number(start_index)

            fields = {}
            for field_match in field_pattern.finditer(fields_str):
                key = field_match.group('key').strip().lower()
                value = field_match.group('value').strip().replace("\n", "")
                if (value.startswith('{') and value.endswith('}')) or \
                    (value.startswith('"') and value.endswith('"')):
                    value = value[1:-1]
                fields[key] = value

            # Create appropriate entry object with line number
            if entry_type == "article":
                entries.append(Article(citation_key, fields, line_number))
            elif entry_type == "inproceedings":
                entries.append(InProceedings(citation_key, fields, line_number))
            elif entry_type == "book":
                entries.append(Book(citation_key, fields, line_number))
            else:
                # You can add more BibEntry types here if needed
                pass

        return entries

def main():
    parser = argparse.ArgumentParser(description="Validate and format a BibTeX file.")
    parser.add_argument(
        "--input", "-i",
        default="input.bib",
        help="Path to input .bib file (default: input.bib)"
    )
    parser.add_argument(
        "--output", "-o",
        default="output.html",
        help="Path to output .html report (default: output.html)"
    )

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: File '{args.input}' does not exist.")
        sys.exit(1)

    entries = BibParser.parse_file(args.input)
    entries = check(entries=entries)
    html_open(entries=entries, file_name=args.output)

if __name__ == "__main__":
    main()