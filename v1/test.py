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

from v1.agent_lib import gpt_llm
llm = gpt_llm

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

from pydantic import BaseModel, Field, model_validator
from typing_extensions import TypedDict, Dict, List, Any, Literal, Annotated, Union

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
    
class Node_JCSS(KGNode):
    node_type: Literal["基础设施"] = Field(
        description="""
        用于描述基础设施节点类型
        """
    )
    
class Node_BH(KGNode):
    node_type: Literal["病害"]

class Node_XLYS(KGNode):
    node_type: Literal["线路要素"]

class Node_YZ(KGNode):
    node_type: Literal['阈值']
    description: str = Field(
        description="""
        用于描述非表格化的限制的一段话，例如：
        弹条中部前端下颚与钢轨不宜接触，两者间隙不应大于 0.5 mm，螺旋道钉参考扭矩 W2 型弹条为 130～170N•m，X3 型弹条为 80～110N•m。
        """
    )
    
# class Node_BH(KGNode):
#     node_type: Literal["病害"] = Field(
#         description="""
#         用于描述病害节点类型
#         """
#     )

# class Node_BH(KGNode):
#     node_type: Literal["表格"] = Field(description="用于描述表格节点类型")
#     table_path: str | None = Field(description="表格截图存储的位置") 
#     number: str | None = Field(description="表格对应规范的编号")
#     caption: str | None = Field(description="表格的表题")
    
class KGEdge(BaseModel): # 边类
    source: Annotated[Union[Node_BH, Node_JCSS, Node_XLYS, Node_YZ], Field(description="node in graph")]
    target: KGNode = Field(description="关系的终止端")
    edge_info: Literal["包含子类", "存在病害"] = Field(description="关系名称")

class Subgraph(BaseModel):
    """Extract graph from text."""
    nodes: List[Annotated[Union[Node_BH, Node_JCSS, Node_XLYS, Node_YZ], Field(description="""
                                                           图谱中的节点，其中：
                                                           Node_BH为病害节点
                                                           Node_JCSS为基础设施节点，例如路基
                                                           Node_XLYS为线路要素，例如圆曲线
                                                           Node_YZ为基础设施对应的管理阈值的相关描述
                                                           """)]]
    # edges: List[KGEdge]
    # meta: Dict[str, Any] = Field(default_factory=dict)

class State(TypedDict):
    subgraph: Subgraph
    validity: bool

from langchain_core.prompts import ChatPromptTemplate

# 大模型抽取子图
subgraph_extractor_prompt = ChatPromptTemplate.from_template("""
请从文本中抽取知识图谱节点。

抽取规则：
1. 仅抽取以下四类节点：
   - 基础设施：如路基、桥梁、隧道、轨道、扣件、简支梁桥
   - 病害：如裂纹、渗漏水、沉降、掉块
   - 线路要素：如圆曲线、缓和曲线、坡段
   - 阈值：仅当文本中出现明确的限制、范围、技术要求时抽取，如“间隙不应大于1 mm”

2. 基础设施最多抽取到二级节点：
   - 允许：轨道->扣件
   - 允许：桥梁->简支梁桥
   - 不允许：轨道->扣件->弹条

3. 像“弹条”“螺旋道钉”“轨距挡板”“调高垫板”这类若属于扣件系统内部部件，不作为节点抽取。

4. 节点名称必须简洁规范，避免重复，不要抽取同义重复项。

5. 若文本主要描述技术要求而不是病害，则优先抽取“基础设施”和“阈值”节点。

文本：
{text}
""")

subgraph_extractor_chain = subgraph_extractor_prompt | llm.with_structured_output(Subgraph)

# def subgraph_extractor(State):
#     return 

# def graph_validator(State):
#     # TODO
#     pass

# def graph_writter(State):
#     # TODO
#     pass

from langgraph.graph import StateGraph, START, END
builder = StateGraph(State)

# builder.add_node("subgraph_extractor", subgraph_extractor)
# builder.add_node("graph_validator",graph_validator)
# builder.add_node("graph_writter", graph_writter)

# builder.add_edge(START, "subgraph_extractor")
# builder.add_edge("subgraph_extractor", "graph_validator")
# builder.add_edge("graph_validator", "graph_writter")
# builder.add_edge("graph_writter", END)
# chain = builder.compile()

# png = chain.get_graph().draw_mermaid_png()

# with open("workflow.png", "wb") as f:
#     f.write(png)

result = subgraph_extractor_chain.invoke({"text": """
第5.6.1条 道岔维修作业应符合以下要求：
一、 道岔尖轨或基本轨伤损时，宜同时更换尖轨和基本轨。
二、 道岔可动心轨辙叉伤损时，宜整体更换。
三、 道岔基本轨、尖轨、辙叉、导轨伤损更换时，应使几何形位、各部间隔尺寸、
钢轨密贴、尖轨相对基本轨降低值、心轨相对翼轨降低值等偏差满足现行标准要求；
更换后但未焊接时，限速不超过 160km/h，钢轨接头轨面及内侧错牙不得大于 1 mm，
并应尽快恢复原结构。
四、 有砟轨道可动心轨辙叉道岔起道作业时，直、曲股应同时起平，保证可动心
轨辙叉在一个水平面上，并做好道岔前后及道岔曲股顺坡，同时加强焊接接头、辙叉、
牵引点等部位的道床捣固。
五、 道岔精调精整应注重几何尺寸与结构相结合，降低值修复与廓形打磨相结合。
六、 作业时严禁撞击轨下基础，保持轨下基础完好。
七、 作业时按规定扭矩紧固螺栓。
第5.6.2条 道岔（调节器）区水平、高低应通过起道或更换不同规格调高垫板进
行调整，调高垫板的规格和数量应符合铺设图要求。调整作业应作好记录。
第5.6.3条 道岔区轨距及支距、调节器轨距应通过更换不同规格调整件进行调
整。轨向通过拨道及更换不同规格调整件进行调整。道岔直股方向不良时，可用弦线
测量并调整；曲股方向不良时，应在直股方向符合要求的基础上，通过控制支距的方"""})
print(result)


