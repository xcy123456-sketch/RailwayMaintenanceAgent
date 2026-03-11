from agent_lib import qianwen_llm
import dotenv
import os
from langchain_neo4j import Neo4jGraph, GraphCypherQAChain
from langchain_core.tools import Tool
from langchain.agents import create_agent
from pydantic import BaseModel
from langchain.tools import tool, ToolRuntime

# 一些cypher的基础语法
create_node_query = """
CREATE (n: {name: $name, age: $age})
"""
match_node_query = """
MATCH (n:基础设施 {name:$name})
"""

# class Context(BaseModel):
#     graph_database: Neo4jGraph

llm = qianwen_llm

os.environ["NEO4J_URI"] = dotenv.get_key(dotenv.find_dotenv(), "NEO4J_URI")
os.environ["NEO4J_USERNAME"] = dotenv.get_key(dotenv.find_dotenv(), "NEO4J_USERNAME")
os.environ["NEO4J_PASSWORD"] = dotenv.get_key(dotenv.find_dotenv(), "NEO4J_PASSWORD")

# 连接Neo4j数据库
graph = Neo4jGraph(
    url=os.environ["NEO4J_URI"],
    username=os.environ["NEO4J_USERNAME"],
    password=os.environ["NEO4J_PASSWORD"],
)


cypher_qa = GraphCypherQAChain.from_llm(
    llm=llm,
    graph=graph,
    verbose=True,
    allow_dangerous_requests=True
    # 可选：限制返回字段、加 schema 限制等（看你的数据安全需求）
)



# 图数据库合法性检查工具
@tool
def tool_validity_check():
    """Check if graph database meets predefined constraints.
    
    Args:
        ...
    """
    # TODO
    return True

# 图数据库初始化工具
@tool
def tool_graph_initializer():
    """Initialize graph database. 
    """
    root_nodes = [
        {'label': '基础设施', 'name': '路基'},
        {'label': '基础设施', 'name': '桥梁'},
        {'label': '基础设施', 'name': '隧道'},
        {'label': '基础设施', 'name': '轨道'},
    ]
    for node in root_nodes:
        if not graph.query('MATCH (n:基础设施 {name:$name}) RETURN n', {'name': node['name']}):
            graph.query('create (n:基础设施 {name:$name}) RETURN n', {'name': node['name']})
    return graph.query("MATCH (n) RETURN n")

# 3) 把 chain 包成 Tool 交给 Agent
tools = [
    # Tool(
    #     name="neo4j_cypher_qa",
    #     func=cypher_qa.run,
    #     description="此工具只允许对图数据库进行查找，不允许增删改。",
    # ),
    tool_graph_initializer
]

# 4) 创建 Agent（会自动选择是否调用 tool）
agent = create_agent(
    model=llm, 
    tools=tools,
    )
# agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# 5) 调用
resp = agent.invoke({"messages": [{'role': 'user', 'content': '帮我检索所有节点信息'}]})
for msg in resp['messages']:
    print(msg.content)
# print(resp["output"])