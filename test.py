import dotenv, os
os.environ["NEO4J_URI"] = dotenv.get_key(dotenv.find_dotenv(), "NEO4J_URI")
os.environ["NEO4J_USERNAME"] = dotenv.get_key(dotenv.find_dotenv(), "NEO4J_USERNAME")
os.environ["NEO4J_PASSWORD"] = dotenv.get_key(dotenv.find_dotenv(), "NEO4J_PASSWORD")

from langchain_neo4j import Neo4jGraph
graph = Neo4jGraph(
    url=os.environ["NEO4J_URI"],
    username=os.environ["NEO4J_USERNAME"],
    password=os.environ["NEO4J_PASSWORD"],
)

from agent_lib import qianwen_llm
llm = qianwen_llm

# 智能体初始化
from langchain.tools import tool
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

from pydantic import BaseModel, Field
from typing_extensions import TypedDict, Dict, List, Any

class KGNode(BaseModel):
    id: str = Field(..., description="子图内唯一ID，例如 n1, n2")
    name: str
    type: str
    aliases: List[str] = Field(default_factory=list)
    attrs: Dict[str, Any] = Field(default_factory=dict)

class KGEdge(BaseModel):
    source: str
    target: str
    type: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    evidence: str = Field(..., description="支撑该关系的原句/片段")
    attrs: Dict[str, Any] = Field(default_factory=dict)

class Subgraph(BaseModel):
    nodes: List[KGNode]
    edges: List[KGEdge]
    meta: Dict[str, Any] = Field(default_factory=dict)

class State(TypedDict):
    subgraph: Subgraph
    validity: bool


# 大模型抽取子图
def subgraph_extractor(State):
    # TODO
    pass

def graph_validator(State):
    # TODO
    pass

def graph_writter(State):
    # TODO
    pass

from langgraph.graph import StateGraph, START, END
builder = StateGraph(State)

builder.add_node("subgraph_extractor", subgraph_extractor)
builder.add_node("graph_validator",graph_validator)
builder.add_node("graph_writter", graph_writter)

builder.add_edge(START, "subgraph_extractor")
builder.add_edge("subgraph_extractor", "graph_validator")
builder.add_edge("graph_validator", "graph_writter")
builder.add_edge("graph_writter", END)
chain = builder.compile()

png = chain.get_graph().draw_mermaid_png()

with open("workflow.png", "wb") as f:
    f.write(png)

