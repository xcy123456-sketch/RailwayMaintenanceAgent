import os
import dotenv
from langchain_openai import ChatOpenAI
from langchain_neo4j import Neo4jGraph, GraphCypherQAChain

os.environ["DASHSCOPE_API_KEY"] = dotenv.get_key(dotenv.find_dotenv(), "DASHSCOPE_API_KEY")

# 3. 初始化百炼模型 (推荐使用 OpenAI 兼容模式)
qianwen_llm = ChatOpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model="qwen-plus",
)
