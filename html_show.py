import webbrowser
from pathlib import Path
from typing import List
from enum import Enum

from issue import IssueLevel, get_issue_legend

class Color(Enum):
    BLOCK = '#f6f6f6'
    NOTICE = '#F2D0A7'
    WARNING = '#FF7A48'
    ERROR = '#FF0000'
    HYPERLINK = '#88A3E2'

def add_html_settings(content: str, entries: List) -> str:
    """生成一个简单的 HTML 文件，包含自定义内容"""
    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Bib File Checker</title>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 20px; }}
            .content {{ background: {Color.BLOCK.value}; padding: 15px; border-radius: 5px; }}
        </style>
    </head>
    {control_html(entries)}
    {content}
    </html>
    """
    return html_template

def issue_html_div(header: str, entry_title: str, content: str, entry_id: int) -> str:
    html_content = f"""
    <div class="bib-entry" data-entry-id="{entry_id}">
        <h1>{header}</h1>
        {search_paper(entry_title)}
        <div class="content">
            {content}
        </div>
    </div>
    """
    return html_content

def control_html(entries: List) -> str:
    issues = [issue.get_issue_type() for entry in entries for issue in entry.issues]
    problems = set(issues)
    problems = [(p, get_issue_legend(p)) for p in problems]
    problem_str = [f'''
        <div>
            <input type="checkbox" class="type-filter" data-type="{value}" checked> <b>[{text}]</b>
        </div>
    ''' for value, text in problems]
    problems = "".join(problem_str)
    
    control_str = f'''
    <!-- Filter -->
    <div id="filter-panel">
        <h3>Filtering Errors or Warnings</h3>
        
        <div class="filter-group">
            <div>
                <input type="checkbox" class="level-filter" data-level="error" checked> <font color={Color.ERROR.value} class="error">[Error]</font>
            </div>
            <div>
                <input type="checkbox" class="level-filter" data-level="warning" checked> <font color={Color.WARNING.value} class="warning">[Warning]</font>
            </div>
            <div>
                <input type="checkbox" class="level-filter" data-level="notice" checked> <font color={Color.NOTICE.value} class="notice">[Notice]</font>
            </div>
        </div>
        
        <h3>Filtering by Problems</h3>
        <div class="filter-group">
            {problems}
        </div>
    </div>

    <script>
    // 过滤功能实现
    document.querySelectorAll('.level-filter, .type-filter').forEach(filter => {{
        filter.addEventListener('change', updateDisplay);
    }});

    function updateDisplay() {{
        // 获取选中的过滤条件
        const showErrors = document.querySelector('.level-filter[data-level="error"]').checked;
        const showWarnings = document.querySelector('.level-filter[data-level="warning"]').checked;
        const showNotices = document.querySelector('.level-filter[data-level="notice"]').checked;
        const selectedTypes = new Set(
            [...document.querySelectorAll('.type-filter:checked')].map(f => f.dataset.type)
        );
        
        // 遍历所有问题
        document.querySelectorAll('.issue').forEach(issueEl => {{
            const level = issueEl.dataset.level;
            const type = issueEl.dataset.type;
            
            // 检查是否应该显示
            const shouldShow = (
                ((level === 'error' && showErrors) || 
                (level === 'warning' && showWarnings) ||
                (level === 'notice' && showNotices)) &&
                selectedTypes.has(type)
            );
            
            issueEl.style.display = shouldShow ? 'block' : 'none';
        }});
        
        // 新增：检查每个论文条目是否有可见的错误/警告
        document.querySelectorAll('.bib-entry').forEach(entryDiv => {{
            // 查找该条目中所有可见的问题元素
            const visibleIssues = entryDiv.querySelectorAll('.issue[style="display: block;"]');
            
            // 如果有至少一个可见的问题，显示整个条目；否则隐藏
            if (visibleIssues.length > 0) {{
                entryDiv.style.display = 'block';
            }} else {{
                entryDiv.style.display = 'none';
            }}
        }});
    }}
    updateDisplay();
    </script>
    '''
    
    return control_str

def save_and_open_html(html_str: str, filename: str):
    """保存 HTML 并自动用浏览器打开"""
    file_path = Path(filename)
    file_path.write_text(html_str, encoding="utf-8")
    
    webbrowser.open(f"file://{file_path.absolute()}")

def issue_to_div(issue) -> str:
    if issue.issue_level == IssueLevel.NOTICE:
        prefix = f'<font color={Color.NOTICE.value} class="notice">[Notice]</font> <b>[{issue.legend}]</b>'
    elif issue.issue_level == IssueLevel.WARNING:
        prefix = f'<font color={Color.WARNING.value} class="warning">[Warning]</font> <b>[{issue.legend}]</b>'
    elif issue.issue_level == IssueLevel.ERROR:
        prefix = f'<font color={Color.ERROR.value} class="error">[Error]</font> <b>[{issue.legend}]</b>'
    else:
        assert False
        
    return f'''\
        <div class="issue {issue.issue_level.text.lower()}" data-type="{issue.get_issue_type()}" data-level="{issue.issue_level.text.lower()}"> \
            {prefix} {issue.message} \
        </div> \
    '''
    
def issue_convert_html(entries) -> str:
    html_str = ""
    
    for i, entry in enumerate(entries):
        if entry.get_num_issues() == 0:
            continue
        
        entry_str = str(entry)
        for issue in entry.issues:
            entry_str += issue_to_div(issue)
        
        entry_str = entry_str.replace("\n", "<br>").replace("\t", "&emsp;&emsp;")
        
        entry_title = entry.title if entry.title is not None else ""
        
        html_str += issue_html_div(f'Line {entry.line_number}', entry_title, entry_str, i)
    
    return html_str

def search_paper(paper_title: str) -> str:
    search_html_str = f'''Search this paper in \
        <a target="_blank" style="color:{Color.HYPERLINK.value}" href="https://scholar.google.com/scholar?q={paper_title.replace(' ', '+')}">Google Scholar</a>, \
        <a target="_blank" style="color:{Color.HYPERLINK.value}" href="https://dblp.org/search?q={paper_title.replace(' ', '%20')}">DBLP</a>, \
        <a target="_blank" style="color:{Color.HYPERLINK.value}" href="https://www.semanticscholar.org/search?q={paper_title.replace(' ', '%20')}">Semantic Scholar</a>, \
        <a target="_blank" style="color:{Color.HYPERLINK.value}" href="https://www.google.com/search?q={paper_title.replace(' ', '+')}">Google</a>, \
        <a target="_blank" style="color:{Color.HYPERLINK.value}" href="https://github.com/search?q={paper_title.replace(' ', '%20')}&type=repositories">Github</a>. \
    '''
    
    return search_html_str
    
def html_open(entries, file_name) -> None:
    warning_error_html_str = issue_convert_html(entries)
    html_content = add_html_settings(warning_error_html_str, entries)
    save_and_open_html(html_content, file_name)

if __name__ == "__main__":
    python_str = """
    <p>这是 Python 字符串生成的 HTML！</p>
    <ul>
        <li>列表项 1</li>
        <li>列表项 2</li>
        <li>列表项 3</li>
    </ul>
    """
    
    html_content = issue_html_div('Python-Generated HTML', python_str)
    html_content = html_content + html_content
    html_content = add_html_settings(html_content)
    save_and_open_html(html_content)