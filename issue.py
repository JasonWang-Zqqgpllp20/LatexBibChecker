from enum import Enum
from typing import List

from bib_read import BibEntry

class IssueLevel(Enum):
    WARNING = (1, 'WARNING')
    ERROR = (2, 'ERROR')
    
    def __init__(self, code, text):
        self.code = code
        self.text = text
    
class Issue:
    def __init__(self, entry: BibEntry, issue_level: IssueLevel):
        self.entry: BibEntry = entry
        self.issue_level: IssueLevel = issue_level
        self.legend = get_issue_legend(self.__class__.__name__)
    
    @property
    def message(self) -> str:
        return None
    
    def get_issue_type(self) -> str:
        return self.__class__.__name__
    
    def __str__(self) -> str:
        return self.message
    
class IssueNotIncludedKeys(Issue):
    def __init__(self, entry: BibEntry, issue_level: IssueLevel, not_included_keys: List[str]):
        super().__init__(entry, issue_level)
        self.not_included_keys = not_included_keys
    
    @property
    def message(self):
        return f"This {self.entry.entry_type} paper does not have fields: {', '.join(self.not_included_keys)}."

class IssueRedundantKeys(Issue):
    def __init__(self, entry: BibEntry, issue_level: IssueLevel, redundant_keys: List[str]):
        super().__init__(entry, issue_level)
        self.redundant_keys = redundant_keys
    
    @property
    def message(self):
        return f"This {self.entry.entry_type} paper have redundant fields: {', '.join(self.redundant_keys)}."

class IssueMultipleEntryKey(Issue):
    def __init__(self, entry: BibEntry, issue_level: IssueLevel, cit_key: str):
        super().__init__(entry, issue_level)
        self.cit_key = cit_key
    
    @property
    def message(self):
        return f"Multiple papers have the same citation key '{self.cit_key}'."
    
class IssueMultipleTitle(Issue):
    def __init__(self, entry: BibEntry, issue_level: IssueLevel, title: str):
        super().__init__(entry, issue_level)
        self.title = title
    
    @property
    def message(self):
        return f"Multiple papers have the same title '{self.title}'."
    
class IssueBiggerBeginPage(Issue):
    def __init__(self, entry: BibEntry, issue_level: IssueLevel, start_page: int, end_page: int):
        super().__init__(entry, issue_level)
        self.start_page = start_page
        self.end_page = end_page
    
    @property
    def message(self):
        return f"The begin page '{self.start_page}' is bigger than the end page '{self.end_page}'."
    
class IssueOnlyOnePage(Issue):
    def __init__(self, entry: BibEntry, issue_level: IssueLevel, page_num: int):
        super().__init__(entry, issue_level)
        self.page_num = page_num
    
    @property
    def message(self):
        return f"The page number contain only a begin page '{self.page_num}' without an end page."
    
class IssueWrongPageFormat(Issue):
    def __init__(self, entry: BibEntry, issue_level: IssueLevel, pages_str: int):
        super().__init__(entry, issue_level)
        self.pages_str = pages_str
    
    @property
    def message(self):
        return f"Unrecognized page format: '{self.pages_str}', should be like '1--20'."

class IssueTitleContainsYear(Issue):
    def __init__(self, entry: BibEntry, issue_level: IssueLevel, pub_type: str, year_match: List):
        super().__init__(entry, issue_level)
        self.pub_type = pub_type
        self.year_match = year_match
            
    @property
    def message(self):
        return f"Publication name at key '{self.pub_type}' contains year number '{self.year_match.group()}'. Year number should only appear in the 'year' field."

class IssueTitleContainsOrdinal(Issue):
    def __init__(self, entry: BibEntry, issue_level: IssueLevel, pub_type: str, ordinal_match: List):
        super().__init__(entry, issue_level)
        self.pub_type = pub_type
        self.ordinal_match = ordinal_match
            
    @property
    def message(self):
        return f"Publication name at key '{self.pub_type}' contains ordinal number '{self.ordinal_match.group()}'."
    
class IssueArxivPaper(Issue):
    def __init__(self, entry: BibEntry, issue_level: IssueLevel, msg: str):
        super().__init__(entry, issue_level)
        self.msg = msg
    
    @property
    def message(self):
        return self.msg
    
class IssueArxivWithInproceddings(Issue):
    def __init__(self, entry: BibEntry, issue_level: IssueLevel):
        super().__init__(entry, issue_level)
    
    @property
    def message(self):
        return f"arxiv papers should use '@article', rather than '@inproceedings'"
    
class IssueTitleCapitalization(Issue):
    def __init__(self, entry: BibEntry, issue_level: IssueLevel, non_cap_words_str: str):
        super().__init__(entry, issue_level)
        self.non_cap_words_str = non_cap_words_str
    
    @property
    def message(self):
        return f"The journal/conference name is not correctly capitalized: {self.non_cap_words_str}."

class IssueArticleWithProceddingsOf(Issue):
    def __init__(self, entry: BibEntry, issue_level: IssueLevel):
        super().__init__(entry, issue_level)
    
    @property
    def message(self):
        return f"The journal begins with 'Proceedings of' or 'Advanced in', you may change '@article' to '@inproceddings' and change keys for this bib entry."

class IssueProceedingsOfAdvancedIn(Issue):
    def __init__(self, entry: BibEntry, issue_level: IssueLevel, starts_with_proceedings: bool, starts_with_advanced: bool, num_proceeding: int, num_advanced: int):
        super().__init__(entry, issue_level)
        self.compare_proceeding_advanced = num_proceeding > num_advanced
        self.starts_with_proceedings = starts_with_proceedings
        self.starts_with_advanced = starts_with_advanced
        self.num_proceeding = num_proceeding
        self.num_advanced = num_advanced
    
    @property
    def message(self):
        if self.compare_proceeding_advanced and self.starts_with_advanced: # proceeding > advanced
            msg = f"The booktitle should start with 'Proceedings of' ({self.num_proceeding} papers start with 'Proceedings of' and {self.num_advanced} papers start with 'Advanced in'.)"
        elif not self.compare_proceeding_advanced and self.starts_with_proceedings: # proceeding <= advanced
            msg = f"The booktitle should start with 'Advanced in' ({self.num_advanced} papers start with 'Advanced in' and {self.num_proceeding} papers start with 'Proceedings of'.)"
        elif not self.starts_with_proceedings and not self.starts_with_advanced:
            # TODO: not sure.
            msg = f"The booktitle of this conference paper should start with 'Proceedings of' or 'Advanced in'."
        else:
            assert False
            
        return msg

class IssueAbbreviation(Issue):
    def __init__(self, entry: BibEntry, issue_level: IssueLevel, abbrs: List[str]):
        super().__init__(entry, issue_level)
        self.abbrs = abbrs
    
    @property
    def message(self):
        # TODO: not sure
        return f"The journal/conference of the paper contain abberiviations: {self.abbrs}"

def get_issue_legend(issue_name: str):
    if issue_name == 'IssueNotIncludedKeys':
        issue_legend = 'Not included keys'
    elif issue_name == 'IssueRedundantKeys':
        issue_legend = 'Include redundant keys'
    elif issue_name == 'IssueMultipleEntryKey':
        issue_legend = 'Mulitple entry key'
    elif issue_name == 'IssueMultipleTitle':
        issue_legend = 'Mulitple paper title'
    elif issue_name == 'IssueBiggerBeginPage':
        issue_legend = 'Bigger begin page'
    elif issue_name == 'IssueOnlyOnePage':
        issue_legend = 'Only one page'
    elif issue_name == 'IssueWrongPageFormat':
        issue_legend = 'Wrong page format'
    elif issue_name == 'IssueTitleContainsYear':
        issue_legend = 'Title contains year'
    elif issue_name == 'IssueTitleContainsOrdinal':
        issue_legend = 'Title contains ordinal number'
    elif issue_name == 'IssueArxivPaper':
        issue_legend = 'Arxiv papers'
    elif issue_name == 'IssueArxivWithInproceddings':
        issue_legend = 'Arxiv as conf paper'
    elif issue_name == 'IssueTitleCapitalization':
        issue_legend = 'Title not capitalized'
    elif issue_name == 'IssueArticleWithProceddingsOf':
        issue_legend = 'Acticle has "Proceedings of"'
    elif issue_name == 'IssueProceedingsOfAdvancedIn':
        issue_legend = 'Inconsistency of "Proceedings of" and "Advanced in"'
    elif issue_name == 'IssueAbbreviation':
        issue_legend = 'Journal/Booktitle contains abbreviations'
    else:
        assert False
        
    return issue_legend

if __name__ == '__main__':
    issue = IssueLevel(1)
    print(issue)