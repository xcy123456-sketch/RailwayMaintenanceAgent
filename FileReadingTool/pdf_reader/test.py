import base64
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
import dotenv
import os

os.environ["DASHSCOPE_API_KEY"] = dotenv.get_key(dotenv.find_dotenv(), "DASHSCOPE_API_KEY")

def to_data_url(path: str) -> str:
    ext = path.split(".")[-1].lower()
    mime = "jpeg" if ext in ["jpg", "jpeg"] else ext
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/{mime};base64,{b64}"

llm = ChatOpenAI(
    model="qwen-vl-plus",
    api_key='sk-f6cf4f3ccd6649bda55450d7197b8232',
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

img_data_url = to_data_url("/Users/xucongyang/Desktop/python_projects/RailwayMaintenanceAgent/FileReadingTool/pdf_reader/result/table/table_14_1.png")

msg = HumanMessage(
    content=[
        {"type": "image_url", "image_url": {"url": img_data_url}},
        {"type": "text", "text": "这张图里有什么？给出关键目标与文字说明。"},
    ]
)

print(llm.invoke([msg]).content)