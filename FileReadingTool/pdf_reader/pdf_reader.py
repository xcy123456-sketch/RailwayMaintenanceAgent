import os
import pdfplumber
from pathlib import Path
import pandas as pd

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

# 测试
file_dir = os.path.join(pdf_file_path, "《高速铁路线路维修规则》（铁工电〔2023〕106号）.pdf")

with pdfplumber.open(file_dir) as pdf:
    for page_num in range(pdf.pages.__len__()):
        page_n = pdf.pages[page_num] # 第一页
        tables = page_n.find_tables()
        for i, table in enumerate(tables):
            bbox = table.bbox
            # 裁剪表格区域
            cropped_page = page_n.crop([bbox[0], bbox[1]-50, bbox[2], bbox[3]])

            # 转成图片
            img = cropped_page.to_image(resolution=300)

            # 单独保存
            img.save(os.path.join(current_dir, "result/table", f"table_{page_num}_{i}.png"))
        texts = page_n.extract_text()
        


    # page_table_list = page_n.extract_tables()
    # for table_idx in range(page_table_list.__len__()):
    #     table = page_table_list[table_idx]
    #     print(table)
    #     table_df = pd.DataFrame(table)
    #     table_df = table_df.apply(
    #         lambda col: col.str.replace(r"\s+", "", regex=True))        
    #     table_df.to_csv(
    #         os.path.join(current_dir, 'result', 'table',  f"table_{page_num}_{table_idx}.csv"))
        

# for pdf in pdf_list:
#     file_dir = os.path.join(pdf_file_path, pdf.name)
#     with pdfplumber.open(file_dir) as pdf:
#         for page in pdf.pages:
#             if page.extract_tables():
#                 print(page.extract_tables())

# if __name__=="__main__":
#     # 一下wz

