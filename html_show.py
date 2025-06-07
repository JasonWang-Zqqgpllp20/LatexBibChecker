import webbrowser
from pathlib import Path
from typing import List

def add_html_settings(content: str) -> str:
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
            .content {{ background: #f0f0f0; padding: 15px; border-radius: 5px; }}
        </style>
    </head>
    {control_html()}
    {content}
    </html>
    """
    return html_template

def warning_error_html_div(header: str, content: str) -> str:
    html_content = f"""
    <body>
        <h1>{header}</h1>
        <div class="content">
            {content}
        </div>
    </body>
    """
    return html_content

def control_html() -> str:
    # TODO: params: 'problems: List[str]'
    problems = [('MISSING_FIELD', 'Missing Fields'), ('PAGE_FORMAT', 'Page Format')]
    problem_str = [f'''
        <label>
            <input type="checkbox" class="type-filter" data-type="{value}" checked> {text}
        </label>
    ''' for value, text in problems]
    problems = "".join(problem_str)
    
    control_str = f'''
    <!-- Filter -->
    <div id="filter-panel">
        <h3>Filtering Errors or Warnings</h3>
        
        <div class="filter-group">
            <label>
                <input type="checkbox" class="level-filter" data-level="error" checked> Errors
            </label>
            <label>
                <input type="checkbox" class="level-filter" data-level="warning" checked> Warnings
            </label>
        </div>
        
        <h3>Filtering Errors or Problems</h3>
        <div class="filter-group">
            {problems}
        </div>
    </div>

    <!-- 条目展示 -->
    <div class="bib-entry">
        <h3>Examples (To be Deleted)</h3>
        <div class="citation-key">Smith2023</div>
        
        <!-- 问题列表 -->
        <div class="issue error" data-type="MISSING_FIELD" data-level="error">
            [ERROR] 缺少必须字段: journal, volume
        </div>
        
        <div class="issue warning" data-type="PAGE_FORMAT" data-level="warning">
            [WARNING] 出版物名称大小写不规范: of, the
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
                (level === 'warning' && showWarnings)) &&
                selectedTypes.has(type)
            );
            
            issueEl.style.display = shouldShow ? 'block' : 'none';
        }});
    }}
    </script>
    '''
    
    return control_str

def save_and_open_html(html_str: str, filename: str = "temp.html"):
    """保存 HTML 并自动用浏览器打开"""
    # 保存文件
    file_path = Path(filename)
    file_path.write_text(html_str, encoding="utf-8")
    
    # 用默认浏览器打开
    webbrowser.open(f"file://{file_path.absolute()}")
    
def warning_error_convert_html(entries) -> str:
    html_str = ""
    
    for i, entry in enumerate(entries):
        if entry.get_num_errors() == 0 and entry.get_num_warnings() == 0:
            continue
        
        entry_str = str(entry)
        for warning in entry.warnings:
            entry_str += '\n<font color="#F2A477" id="warning">[Warning] </font>' + warning
        for error in entry.errors:
            entry_str += '\n<font color="#FF0000" id="error">[Error] </font>' + error
        
        entry_str = entry_str.replace("\n", "<br>").replace("\t", "&emsp;&emsp;")
        
        html_str += warning_error_html_div(f'Paper {i+1}', entry_str) # TODO: line number of the entry
    
    return html_str

def search_paper(paper_title: str) -> str:
    search_html_str = f'''Is this arxiv paper accepted by a journal/conference? [ Search in \
        <a target="_blank" href="https://scholar.google.com/scholar?q={paper_title.replace(' ', '+')}">Google Scholar</a>, \
        <a target="_blank" href="https://dblp.org/search?q={paper_title.replace(' ', '%20')}">DBLP</a>, \
        <a target="_blank" href="https://www.semanticscholar.org/search?q={paper_title.replace(' ', '%20')}">Semantic Scholar</a>, \
        <a target="_blank" href="https://www.google.com/search?q={paper_title.replace(' ', '+')}">Google</a>, \
        <a target="_blank" href="https://github.com/search?q={paper_title.replace(' ', '%20')}&type=repositories">Github</a>. \
        ]
    '''
    
    return search_html_str
    
def html_open(entries) -> None:
    warning_error_html_str = warning_error_convert_html(entries)
    html_content = add_html_settings(warning_error_html_str)
    save_and_open_html(html_content)

if __name__ == "__main__":
    # 示例：把 Python 字符串变成 HTML 内容
    python_str = """
    <p>这是 Python 字符串生成的 HTML！</p>
    <ul>
        <li>列表项 1</li>
        <li>列表项 2</li>
        <li>列表项 3</li>
    </ul>
    """
    
    html_content = warning_error_html_div('Python-Generated HTML', python_str)
    html_content = html_content + html_content
    html_content = add_html_settings(html_content)
    save_and_open_html(html_content)