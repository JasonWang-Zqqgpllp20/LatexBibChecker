from typing import Dict, List, Optional


class BibEntry:
    """Abstract base class for all BibTeX entry types."""
    
    def __init__(self, entry_type: str, citation_key: str, fields: Dict[str, str], line_number: int):
        self.entry_type = entry_type
        self.citation_key = citation_key
        self.fields = fields
        self.line_number = line_number
        self.issues: List = []
    
    def __str__(self) -> str:
        """Custom string representation of the entry."""
        lines = [
            f"@{self.entry_type}{{{self.citation_key},",
            *[f"\t{key} = {{{value}}}," for key, value in self.fields.items()],
            "}"
        ]
        return "\n".join(lines)
    
    def get_field(self, field_name: str, default: Optional[str] = None) -> Optional[str]:
        """Safely get a field value with case-insensitive lookup."""
        field_name = field_name.lower()
        for key, value in self.fields.items():
            if key.lower() == field_name:
                return value
        return default
    
    def get_all_fields(self) -> Dict[str, str]:
        """Get all fields as a dictionary."""
        return self.fields
    
    def add_issues(self, issue):
        assert issue.issue_level.code in [0, 1, 2]
        self.issues.append(issue)
        
    def get_num_issues(self):
        return len(self.issues)
    
    def get_pub(self):
        return None
    
    def get_pub_type(self):
        return None

class Article(BibEntry):
    """Class for @article entries."""
    
    def __init__(self, citation_key: str, fields: Dict[str, str], line_number: int):
        super().__init__("article", citation_key, fields, line_number)
        
    def get_pub(self) -> Optional[str]:
        return self.journal
    
    def get_pub_type(self) -> str:
        return 'article'
    
    @property
    def author(self) -> Optional[str]:
        return self.get_field("author")
    
    @property
    def title(self) -> Optional[str]:
        return self.get_field("title")
    
    @property
    def journal(self) -> Optional[str]:
        return self.get_field("journal")
    
    @property
    def year(self) -> Optional[str]:
        return self.get_field("year")
    
    @property
    def pages(self) -> Optional[str]:
        return self.get_field("pages")
    
    @property
    def volume(self) -> Optional[str]:
        return self.get_field("volume")
    
    @property
    def number(self) -> Optional[str]:
        return self.get_field("number")

class InProceedings(BibEntry):
    """Class for @inproceedings entries."""
    
    def __init__(self, citation_key: str, fields: Dict[str, str], line_number: int):
        super().__init__("inproceedings", citation_key, fields, line_number)
        
    def get_pub(self) -> Optional[str]:
        return self.booktitle
    
    def get_pub_type(self) -> str:
        return 'booktitle'
    
    @property
    def author(self) -> Optional[str]:
        return self.get_field("author")
    
    @property
    def title(self) -> Optional[str]:
        return self.get_field("title")
    
    @property
    def booktitle(self) -> Optional[str]:
        return self.get_field("booktitle")
    
    @property
    def year(self) -> Optional[str]:
        return self.get_field("year")
    
    @property
    def pages(self) -> Optional[str]:
        return self.get_field("pages")

class Book(BibEntry):
    """Class for @book entries."""
    
    def __init__(self, citation_key: str, fields: Dict[str, str], line_number: int):
        super().__init__("book", citation_key, fields, line_number)
    
    @property
    def author(self) -> Optional[str]:
        return self.get_field("author")
    
    @property
    def editor(self) -> Optional[str]:
        return self.get_field("editor")
    
    @property
    def title(self) -> Optional[str]:
        return self.get_field("title")
    
    @property
    def publisher(self) -> Optional[str]:
        return self.get_field("publisher")
    
    @property
    def year(self) -> Optional[str]:
        return self.get_field("year")

class Others(BibEntry):
    """Class for all other BibTeX entry types."""
    
    def __init__(self, entry_type: str, citation_key: str, fields: Dict[str, str]):
        super().__init__(entry_type, citation_key, fields)