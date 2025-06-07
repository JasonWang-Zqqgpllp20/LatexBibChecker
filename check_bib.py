import re
import datetime
from collections import Counter
from typing import Dict, List, Optional, Tuple

from bib_read import BibEntry, Article, InProceedings, Book, Others
from html_show import search_paper
from error_warning import Issue

# FUNCTION: 条目必须有：article有7个必须条目，inproceedings有5个必须条目
def check_must_keys(entries: List[BibEntry]) -> List[BibEntry]:
    MUST_KEYS = ['title', 'author', 'pages', 'year']
    MUST_KEYS_JOURNAL = MUST_KEYS + ['journal']
    MUST_KEYS_CONFERENCE = MUST_KEYS + ['booktitle']
    SELECTED_KEYS = ['volume', 'number']
    
    def find_redundant_keys(entry: BibEntry, must_fields: List[str]) -> Optional[str]:
        # TODO: similar codes
        fields = entry.get_all_fields()
        redundant_keys_l = []
        for key in fields.keys():
            if key not in must_fields:
                redundant_keys_l.append(key)
        
        if len(redundant_keys_l) > 0:
            error_msg = f"This {entry.entry_type} paper have redundant fields: {redundant_keys_l}"
        else:
            error_msg = None
        return error_msg
    
    def find_not_included_keys(entry: BibEntry, must_fields: List[str]) -> Optional[str]:
        fields = entry.get_all_fields()
        not_included_keys_l = []
        for key in must_fields:
            if key not in fields.keys():
                not_included_keys_l.append(key)
        
        if len(not_included_keys_l) > 0:
            error_msg = f"This {entry.entry_type} paper does not have fields: {not_included_keys_l}"
        else:
            error_msg = None
        return error_msg
    
    for entry in entries:
        ''' not included keys '''
        warning_msg, error_msg = None, None
        if isinstance(entry, Article):
            if entry.journal is not None:
                if 'arxiv' in entry.journal.lower():
                    error_msg = find_not_included_keys(entry, MUST_KEYS_JOURNAL)
                else:
                    warning_msg = find_not_included_keys(entry, SELECTED_KEYS)
                    error_msg = find_not_included_keys(entry, MUST_KEYS_JOURNAL)
            else:
                warning_msg = find_not_included_keys(entry, SELECTED_KEYS)
                error_msg = find_not_included_keys(entry, MUST_KEYS_JOURNAL)
        elif isinstance(entry, InProceedings):
            error_msg = find_not_included_keys(entry, MUST_KEYS_CONFERENCE)
        elif isinstance(entry, Book):
            pass
        elif isinstance(entry, Others):
            pass
        
        if warning_msg is not None:
            entry.add_warnings(warning_msg)
        if error_msg is not None:
            entry.add_errors(error_msg)
        
        ''' redundant keys '''
        # TODO: similar codes
        warning_msg, error_msg = None, None
        if isinstance(entry, Article):
            error_msg = find_redundant_keys(entry, MUST_KEYS_JOURNAL + SELECTED_KEYS)
        elif isinstance(entry, InProceedings):
            error_msg = find_redundant_keys(entry, MUST_KEYS_CONFERENCE + SELECTED_KEYS)
        elif isinstance(entry, Book):
            pass
        elif isinstance(entry, Others):
            pass
        
        if warning_msg is not None:
            entry.add_warnings(warning_msg)
        if error_msg is not None:
            entry.add_errors(error_msg)
    
    return entries

# FUNCTION: .bib文件内部是否有重复的论文？
def check_redundant(entries: List[BibEntry]) -> List[BibEntry]:
    def find_duplicates(lst: List) -> Dict:
        count = Counter(lst)
        duplicate_items = [item for item, cnt in count.items() if cnt > 1]
        
        duplicate_dict = {}
        for idx, title in enumerate(lst):
            if title in duplicate_items:
                duplicate_dict[title] = duplicate_dict.get(title, []) + [idx]
                
        return duplicate_dict
    
    ''' Duplicate citation_key '''
    cit_key_l = [entry.citation_key for entry in entries]
    duplicate_cit_key_dict = find_duplicates(cit_key_l)

    ''' Duplicate Titles '''
    title_l = [entry.title.lower() for entry in entries]
    duplicate_title_dict = find_duplicates(title_l)
    
    for cit_key, v_indices in duplicate_cit_key_dict.items():
        error_msg = f"Multiple papers have the same citation keys '{cit_key}'"
        for idx in v_indices:
            entries[idx].add_errors(error_msg)
            
    for title, v_indices in duplicate_title_dict.items():
        error_msg = f"Multiple papers have the same title of '{title}'"
        for idx in v_indices:
            entries[idx].add_errors(error_msg)
    
    return entries
    
# FUNCTION: 假设pages字段存在，检查是否符合规范，必须是"起--止"
def check_pages(entries: List[BibEntry]) -> List[BibEntry]:
    def analyze_pages(pages_str: str) -> Optional[str]:
        pages_str = pages_str.strip() # stripe spaces
        
        # 1. standard begin-end page pair, like 1--10 or 1-10.
        range_match = re.fullmatch(r'(\d+)[-–—]{1,2}(\d+)', pages_str)
        if range_match:
            start = int(range_match.group(1))
            end = int(range_match.group(2))
            if start <= end:
                return None
            else:
                return f"The begin page '{start}' is bigger than the end page '{end}'."
        
        # 2. single number
        if pages_str.isdigit():
            page_num = int(pages_str)
            return f"The page number contain only a begin page '{page_num}' without a end page."
        
        # 3. Other formats
        return f"Unrecognized page format: '{pages_str}', should be like '1--20'."

    pages_l = [entry.pages for entry in entries]
    for idx, pages_str in enumerate(pages_l):
        if pages_str is None: # assume the entry has the key 'page'.
            continue
        error_msg = analyze_pages(pages_str)
        if error_msg is not None:
            entries[idx].add_errors(error_msg)
    
    return entries

# FUNCTION: 年份只能有year这个字段有，article/booktitle就不要带年份了
# FUNCTION: st, th是否要有？ # TODO: 感觉这个要全过一遍，看是否是统一了
def check_year(entries: List[BibEntry]) -> List[BibEntry]:
    """
    Check if publication names (journal/booktitle) contain year numbers or ordinal indicators.
    
    Rules:
    1. No plain year numbers (e.g., 2023, 2015) allowed in journal/booktitle
    2. No ordinal indicators (e.g., 41st, 62nd) allowed in journal/booktitle
    3. Year should only appear in the 'year' field
    
    Args:
        entries: List of BibEntry objects
        
    Returns:
        List of BibEntry objects with error messages added for violations
    """
    def analyze_year_in_pub(pub: str, pub_type: str) -> Optional[str]:
        """
        Analyze publication name for year-related patterns.
        
        Args:
            pub: Journal or booktitle string
            
        Returns:
            Error message if year pattern found, None otherwise
        """
        if not pub:
            return None, None
        
        warning_msg, error_msg = None, None
        # Check for 4-digit years (1900-2099)
        year_match = re.search(r'(?<!\d)(19|20)\d{2}(?!\d)', pub)
        if year_match:
            error_msg = f"Publication name at key '{pub_type}' contains year number '{year_match.group()}'. Year number should only appear in the 'year' field."
            
        # Check for ordinal indicators (41st, 62nd, 3rd etc.)
        ordinal_match = re.search(r'\b\d{1,4}(st|nd|rd|th)\b', pub, re.IGNORECASE)
        if ordinal_match:
            warning_msg = f"Publication name at key '{pub_type}' contains ordinal number '{ordinal_match.group()}'."
            
        return warning_msg, error_msg

    for entry in entries:
        if isinstance(entry, Article):
            pub = entry.journal
            pub_type = "journal"
        elif isinstance(entry, InProceedings):
            pub = entry.booktitle
            pub_type = "booktitle"
        else:
            continue
        
        if pub is None: # assume that the entry has a pub key but may have wrongs
            continue
        if 'arxiv' in pub.lower(): # the journal name of arxiv paper orginally contain year number
            continue
            
        warning_msg, error_msg = analyze_year_in_pub(pub, pub_type)
        if warning_msg is not None:
            entry.add_warnings(warning_msg)
        if error_msg is not None:
            entry.add_errors(error_msg)
    
    return entries

# FUNCTION: 是还没录用的arxiv论文。arxiv论文是否有已经录用的版本？生成一下自动查找的url吧. arxiv必须是article
def check_arxiv(entries: List[BibEntry]) -> List[BibEntry]:
    today_year = datetime.datetime.today().year
    
    for entry in entries:
        if isinstance(entry, Article):
            if entry.journal is not None and 'arxiv' in entry.journal.lower() and entry.year is not None:
                # TODO: msg should not be html. html should be transfered latter.
                msg = search_paper(entry.title)
                # newly arxiv is ok to not be accepted in a journal/conf, old arxiv is not ok
                if int(entry.year) < today_year - 1:
                    entry.add_errors(msg)
                else:
                    entry.add_warnings(msg)
            else: # assume that the entry has a year key
                continue
        elif isinstance(entry, InProceedings):
            if 'arxiv' in entry.booktitle:
                entry.add_errors(f"arxiv papers should use '@article', rather than '@inproceedings'")
        else:
            assert False
        
    return entries
        
    
# FUNCTION: 期刊会议名称，是否是首字母大写的
def check_pub_captialization(entries: List[BibEntry]) -> List[BibEntry]:
    def find_improperly_capitalized_words(sentence: str) -> Optional[List[Tuple[str, int]]]:
        """
        Find words that violate title capitalization rules (excluding prepositions and allowed patterns)
        
        Args:
            sentence: Input sentence to check
            
        Returns:
            - None if all words are properly capitalized
            - List of tuples (word, index) for words violating rules
            
        Rules:
            1. First word of sentence must be capitalized
            2. Non-preposition words must be capitalized
            3. Preposition words can be lowercase
            4. Allowed patterns:
            - Numbers (23, 45.6)
            - Ordinal numbers (23rd, 33rd)
            - arXiv (standalone or with numbers: arXiv:2312.15478)
        """
        # Common English prepositions and articles
        prepositions = {
            'a', 'an', 'the', 'and', 'but', 'or', 'for', 'nor', 'as', 'at', 'by', 
            'for', 'from', 'in', 'into', 'of', 'on', 'onto', 'to', 'with', 'is',
            'are', 'was', 'were', 'am', 'be', 'been', 'being', 'have', 'has', 'had',
            'do', 'does', 'did', 'will', 'would', 'shall', 'should', 'can', 'could',
            'may', 'might', 'must', 'not',
            # permited words:
            'preprint'
        }
        
        ignored_words = prepositions
        
        # Patterns to allow (ordinals, arXiv with numbers)
        ordinal_pattern = re.compile(r'^\d+(st|nd|rd|th)$', re.IGNORECASE)
        arxiv_pattern = re.compile(r'^arxiv(:\d{4}\.\d{4,5})?$', re.IGNORECASE)
        number_pattern = re.compile(r'^[\d.,]+$')
        
        violations = []
        words = sentence.split()
        
        for i, word in enumerate(words):
            if not word:  # Skip empty strings
                continue
                
            # Skip allowed patterns
            if (arxiv_pattern.fullmatch(word) or 
                ordinal_pattern.fullmatch(word) or 
                number_pattern.fullmatch(word)):
                continue
                
            # Find first alphabetic character (skip leading non-letters)
            first_letter = None
            for char in word:
                if char.isalpha():
                    first_letter = char
                    break
                    
            # Skip if no letters found (all numbers/punctuation)
            if first_letter is None:
                continue
                
            # Check capitalization rules
            if i == 0:  # First word must be capitalized
                if not first_letter.isupper():
                    violations.append((word, i))
            else:  # Non-first words
                lower_word = word.lower()
                if lower_word not in ignored_words and not first_letter.isupper():
                    violations.append((word, i))
                    
        return violations if violations else None
    
    for entry in entries:
        pub = entry.get_pub()
        if pub is None:
            continue
        
        non_cap_words = find_improperly_capitalized_words(pub)
        if non_cap_words is not None:
            non_cap_words_str = ', '.join([word for word, _ in non_cap_words])
            entry.add_warnings(f"The journal/conference name is not properly capitalized: {non_cap_words_str}")

    return entries

# TODO: 会议以Proceedings of还是Advanced in。article里的journal里必须是期刊名(不能是Proceedings of或者Advanced in)，inproceedings里的booktitle必须是会议. 
def check_pre_pf_conf(entries: List[BibEntry]) -> List[BibEntry]:
    def check_pub_title(title: str) -> dict:
        """
        检查期刊/会议标题是否符合规范
        
        Args:
            title: 要检查的标题字符串
            
        Returns:
            包含检查结果的字典，例如：
            {
                'starts_with_proceedings': bool,
                'starts_with_advanced': bool,
                'is_valid': bool
            }
        """
        if not title:
            return {
                'starts_with_proceedings': False,
                'starts_with_advanced': False,
                'is_valid': False
            }
        
        # 去除首尾空格并转换为小写比较
        lower_title = title.strip().lower()
        
        starts_with_proceedings = lower_title.startswith('proceedings of')
        starts_with_advanced = lower_title.startswith('advanced in')
        
        return {
            'starts_with_proceedings': starts_with_proceedings,
            'starts_with_advanced': starts_with_advanced,
        }
    
    pub_info_l = [check_pub_title(entry.get_pub()) for entry in entries]
    starts_with_proceedings_l = [pub_info['starts_with_proceedings'] for pub_info in pub_info_l]
    starts_with_advanced_l = [pub_info['starts_with_advanced'] for pub_info in pub_info_l]
    
    # Compare the number of starts_with_proceedings and starts_with_advanced
    num_proceeding = sum(starts_with_proceedings_l)
    num_advanced = sum(starts_with_advanced_l)
    compare_proceeding_advanced = num_proceeding > num_advanced
    
    for entry, starts_with_proceedings, starts_with_advanced, in zip(entries, starts_with_proceedings_l, starts_with_advanced_l):
        if isinstance(entry, Article):
            if starts_with_proceedings or starts_with_advanced:
                entry.add_errors(f"The journal begins with 'Proceedings of' or 'Advanced in', you may change '@article' to '@inproceddings' and change keys for this bib entry.")
            else:
                continue
        elif isinstance(entry, InProceedings):
            if num_proceeding == 0 and num_advanced == 0:
                continue
            elif compare_proceeding_advanced and starts_with_advanced: # proceeding > advanced
                entry.add_warnings(f"The booktitle should start with 'Proceedings of' ({num_proceeding} papers start with 'Proceedings of' and {num_advanced} papers start with 'Advanced in'.)")
            elif not compare_proceeding_advanced and starts_with_proceedings: # proceeding <= advanced
                entry.add_warnings(f"The booktitle should start with 'Advanced in' ({num_advanced} papers start with 'Advanced in' and {num_proceeding} papers start with 'Proceedings of'.)")
            elif not starts_with_proceedings and not starts_with_advanced:
                # TODO: not sure.
                entry.add_warnings(f"The booktitle of this conference paper should start with 'Proceedings of' or 'Advanced in'.")
                
    return entries
    
# TODO: 会议名、期刊名是都缩写还是都全称
def check_pub_abbreviation(entries: List[BibEntry]) -> List[BibEntry]:
    def detect_conference_abbreviations(pub: str) -> Optional[List[str]]:
        """
        检测字符串中的会议/期刊缩写词（多个大写字母组成的单词）
        跳过ACM、IEEE等更大的词汇
        
        参数:
            text (str): 要检查的文本
            
        返回:
            tuple: (bool是否包含目标缩写词, list找到的所有目标缩写词)
        """
        # 定义要检测的目标缩写模式（3个或更多连续大写字母）
        target_pattern = r'\b(?:[A-Z]{2,}|[A-Za-z]*[A-Z]{2,}[A-Za-z]*)\b'
        
        # 定义要排除的通用缩写（如ACM、IEEE等）
        excluded_abbrs = {'ACM', 'IEEE', 'SIAM', 'MIT'} # TODO
        
        # 找到所有匹配的缩写词
        all_abbrs = re.findall(target_pattern, pub)
        
        # 过滤出目标缩写词（排除通用缩写）
        target_abbrs = [abbr for abbr in all_abbrs if abbr not in excluded_abbrs]
        
        # 返回结果
        if len(target_abbrs) == 0:
            target_abbrs = None
        return target_abbrs
    
    for entry in entries:
        pub = entry.get_pub()
        if pub is None:
            continue # assume the paper has a pub (journal/conf) key
        abbrs = detect_conference_abbreviations(pub)
        if abbrs is not None:
            entry.add_warnings(f"The journal/conference of the paper contain abberiviations: {abbrs}") # TODO: not sure
        
    return entries

# TODO: .tex中，未引用的，和引用不存在的

# TODO: generating modified .bib file!
        
def check(entries: List[BibEntry]):
    # filter unneeded entries
    entries = [entry for entry in entries if not isinstance(entry, Others) and not isinstance(entry, Book)]
    
    init_entries_len = len(entries)
    
    entries = check_must_keys(entries)

    entries = check_redundant(entries)
    
    entries = check_pages(entries)
    
    entries = check_year(entries)
    
    entries = check_arxiv(entries)
    
    entries = check_pub_captialization(entries)
    
    entries = check_pre_pf_conf(entries)
    
    entries = check_pub_abbreviation(entries)
    
    assert entries is not None and init_entries_len == len(entries) # no entries are ignored or not returned
    
    return entries

if __name__ == '__main__':
    ...