import os
import pdfplumber
from pathlib import Path

def get_all_pdfs(folder_path)->list:
    '''
    读取所有pdf文件名
    '''
    folder = Path(folder_path)
    return list(folder.rglob("*.pdf"))

current_dir = os.path.dirname(os.path.abspath(__file__))

# 判断是否存在生成文件存放目录，如果没有就创建
result_dir = os.path.join(current_dir, 'result')
if not os.path.exists(result_dir):
    os.makedirs(result_dir)
result_text_dir = os.path.join(current_dir, 'result/text')
if not os.path.exists(result_text_dir):
    os.makedirs(result_text_dir)
result_table_dir = os.path.join(current_dir, 'result/table')
if not os.path.exists(result_table_dir):
    os.makedirs(result_table_dir)

pdf_file_path = os.path.join(current_dir, 'file_lib')
pdf_list = get_all_pdfs(pdf_file_path)

for pdf in pdf_list:
    file_dir = os.path.join(pdf_file_path, pdf.name)
    with pdfplumber.open(file_dir) as pdf:
        for page in pdf.pages:
            if page.extract_tables():
                print(page.extract_tables())



