import dotenv, os
from langchain_neo4j import Neo4jGraph
from v1.agent_lib import gpt_llm,qianwen_llm
from typing_extensions import TypedDict, List, Annotated, Literal
from pydantic import BaseModel, Field, model_validator


os.environ["NEO4J_URI"] = dotenv.get_key(dotenv.find_dotenv(), "NEO4J_URI")
os.environ["NEO4J_USERNAME"] = dotenv.get_key(dotenv.find_dotenv(), "NEO4J_USERNAME")
os.environ["NEO4J_PASSWORD"] = dotenv.get_key(dotenv.find_dotenv(), "NEO4J_PASSWORD")

graph = Neo4jGraph(
    url=os.environ["NEO4J_URI"],
    username=os.environ["NEO4J_USERNAME"],
    password=os.environ["NEO4J_PASSWORD"],
)

llm = qianwen_llm



class KGNode(BaseModel): # 节点类
    id: str = Field(description="节点唯一ID，格式为 节点类型:节点名称")
    name: str = Field(description="节点名称")
    node_type: str = Field(description="节点类型")
    @model_validator(mode="after")
    def check_id(self):
        expected = f"{self.node_type}:{self.name}"
        if self.id != expected:
           self.id = expected
        return self

class KGNode_Infrastructure(KGNode): # 节点类
    node_type: Literal["Infrastructure"] = "Infrastructure"

class KGNode_Defect(KGNode):
    node_type: Literal["Defect"] = "Defect"
    infrastructure: str = Field(description="病害所属基础设施")
    cause: str = Field(description="病害产生原因")
    impact: str = Field(description="病害潜在影响")

class KGNode_Threshold(KGNode):
    node_type: Literal["Threshold"] = "Threshold"
    infrastructure: str = Field(description="阈值对应的基础设施")
    defect: str = Field(description="阈值对应的病害")
    description: str = Field(description="病害产生原因")
    impact: str = Field(description="病害潜在影响")

class KGNode_Inspection(KGNode):
    node_type: Literal["Inspection"] = "Inspection"
    infrastructure: str = Field(description="巡检对应的基础设施")
    description: str = Field(description="巡检产生原因")


class KGEdge(BaseModel): # 边类
    source: KGNode = Field(description="node in graph")
    target: KGNode = Field(description="关系的终止端")
    edge_info: str = Field(description="关系名称")

class KGIntegrateState(TypedDict):
    db_nodes: List[KGNode]
    db_edges: List[KGEdge]
    matching_analysis: str
    subgraph_nodes: List[KGNode]
    subgraph_edges: List[KGEdge]
    
# class EntityOutput(BaseModel):
#     nodes: List[KGNode_Defect | KGNode_Infrastructure | KGNode_Threshold | KGNode_Inspection]

# class EdgeOutput(BaseModel):
#     edges: List[KGEdge]

# 流程包括：读取子图，与原有图谱对齐，合并入图谱
# 读取子图：将Neo4j转换成实体
# def load_neo4j_db(state: KGIntegrateState):
#     # 1) 获取所有节点
#     nodes = graph.query("""
#     MATCH (n)
#     RETURN
#     elementId(n) AS element_id,
#     labels(n) AS labels,
#     properties(n) AS props    
#     """)

#     # # 2) 获取所有关系
#     # edges = graph.query("""
#     # MATCH ()-[r]->()
#     # RETURN r
#     # """)
    
#     for node in nodes:
#         del node["element_id"]
#     print(nodes)
#     state["db_nodes"] = nodes
    
def merge_KG():
    # TODO
    pass
    
# from langchain_core.prompts import ChatPromptTemplate
# # 对齐：将子图中的节点和边与原有图谱进行对齐，找出新增的节点和边
# def node_matching(state: KGIntegrateState):
#     """Use llm to find potentially same node items between subgraph and db graph"""
#     prompt = ChatPromptTemplate.from_template(
#     """你目前要把铁路修规中新的子知识图谱融合到数据库知识图谱中。请你根据以下提示，找出子图中和数据库图谱中可能相同的节点。
#     知识图谱中目前包含以下节点：
#     {db_nodes}
#     新的子图中包含以下节点：
#     {subgraph_nodes}
#     """)
    
#     return {"matching_analysis": prompt.format(db_nodes=state["db_nodes"], subgraph_nodes=state["subgraph_nodes"])}
        

    
# 合并入图谱：将新的节点和边合并入图谱
# TODO

from langgraph.graph import StateGraph, START, END
workflow = StateGraph(KGIntegrateState)
workflow.add_node("load_neo4j_db", load_neo4j_db)
workflow.add_node("align", align_subgraph)
workflow.add_edge(START, "load_neo4j_db")
workflow.add_edge("load_neo4j_db", "align")
workflow.add_edge("align", END)
chain = workflow.compile()
chain.invoke({})