import dotenv, os
from v1.agent_lib import qianwen_llm, gpt_llm
from typing_extensions import TypedDict, List, Annotated, Literal
from pydantic import BaseModel, Field, model_validator
from langchain_core.prompts import ChatPromptTemplate
from langchain_neo4j import Neo4jGraph
from langgraph.graph import StateGraph, START, END

# 初始化Neo4j连接
os.environ["NEO4J_URI"] = dotenv.get_key(dotenv.find_dotenv(), "NEO4J_URI")
os.environ["NEO4J_USERNAME"] = dotenv.get_key(dotenv.find_dotenv(), "NEO4J_USERNAME")
os.environ["NEO4J_PASSWORD"] = dotenv.get_key(dotenv.find_dotenv(), "NEO4J_PASSWORD")
graph = Neo4jGraph(
    url=os.environ["NEO4J_URI"],
    username=os.environ["NEO4J_USERNAME"],
    password=os.environ["NEO4J_PASSWORD"],
)

# 调用llm api
llm = gpt_llm

rules_for_extraction = """
抽取规则：
1. 仅抽取以下五类节点：
- 基础设施：如路基、桥梁、隧道、轨道、扣件、简支梁桥
- 病害：如裂纹、渗漏水、沉降、掉块
- 线路要素：如圆曲线、缓和曲线、坡段
- 阈值：仅当文本中出现明确的限制、范围、技术要求时抽取，如“间隙不应大于1 mm”
- 巡检：仅当文本中出现明确的巡检要求时抽取，如“应定期进行巡检”

2. 基础设施抽取到三级节点并展示：
- 允许：轨道->扣件
- 允许：桥梁->简支梁桥
- 不允许：轨道->扣件->垫板->5mm垫板 （过细的分类会导致节点过多，且不利于后续关系抽取）

3. 节点名称必须简洁规范，避免重复，不要抽取同义重复项，名称不能含糊，例如“轨下基础”比较含糊

4. 如何文本没有体现节点的某个属性，则该部分为空。
"""

# 节点类
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

# 边类
class KGEdge(BaseModel): # 边类
    source: KGNode = Field(description="node in graph")
    target: KGNode = Field(description="关系的终止端")
    edge_info: str = Field(description="关系名称")

class KGGenState(TypedDict):
    text: str
    node_analysis: str
    node_group: List[KGNode_Defect | KGNode_Infrastructure | KGNode_Threshold | KGNode_Inspection]
    edge_analysis: str
    edge_group: List[KGEdge]


class EntityOutput(BaseModel):
    nodes: List[KGNode_Defect | KGNode_Infrastructure | KGNode_Threshold | KGNode_Inspection]

class EdgeOutput(BaseModel):
    edges: List[KGEdge]


def clear_neo4j(state: KGGenState):
    cypher = """
    MATCH (n)
    DETACH DELETE n
    """
    graph.query(cypher)
    print("Neo4j database cleared.")

def generate_node_analysis(state: KGGenState):
    """"Use llm to find potential node items"""
    prompt = ChatPromptTemplate.from_template(
        """你现在要将轨道规范整理成知识图谱，请先从文本中抽取知识图谱节点。
        """ + prompt1 + """
        文本：
        {text}"""
    )
    node_analysis = llm.invoke(
        prompt.invoke({
            'text': state["text"]
        })
    )
    print("generate_node_analysis done.")
    return {"node_analysis": node_analysis.content}

def generate_node_entity(state: KGGenState):
    """Use llm to obtain node entity based on previous analysis."""
    prompt = ChatPromptTemplate.from_template(
        """你现在要将轨道规范整理成知识图谱，以下是一段规范原文：
        {text}
        """ + prompt1 + """根据原文，你已经进行了如下分析：
        {node_analysis}
        接下来请生成对应的知识图谱节点实体
        """
    )
    temp_chain = prompt | llm.with_structured_output(EntityOutput)
    result = temp_chain.invoke({
            'text': state["text"],
            'node_analysis': state["node_analysis"]
        })
    print("generate_node_entity done.")
    return {"node_group": result.nodes}

def generate_edge_analysis(state: KGGenState):
    """"Use llm to find potential node items"""
    prompt = ChatPromptTemplate.from_template(
        """你现在要将轨道规范整理成知识图谱，以下是一段规范原文：
        {text}
        根据原文，你已经发掘了如下节点：
        {node_group}
        请根据你收集的节点信息找到所有的对应关系，对应关系仅包含如下关系：
        基础设施-包含->基础设施
        基础设施-存在病害->病害
        病害-存在管理阈值->阈值
        基础设施-存在巡检->巡检
        巡检-存在管理阈值->阈值
        请确保每条边的两端节点都来自发掘节点
        """
    )
    edge_analysis = llm.invoke(
        prompt.invoke({
            'text': state["text"],
            'node_group': state["node_group"]
        })
    )
    print("generate_edge_analysis done.")
    return {"edge_analysis": edge_analysis.content}

def generate_edge_entity(state: KGGenState):
    """Use llm to obtain node entity based on previous analysis."""
    prompt = ChatPromptTemplate.from_template(
        """你现在要将轨道规范整理成知识图谱，以下是一段规范原文：
        {text}

        根据原文，你获得了如下节点：
        {node_entity}
        
        根据节点，你做了如下节点之间买的关系分析：
        {edge_analysis}
        
        请生成对应的关系实体
        """
    )
    temp_chain = prompt | llm.with_structured_output(EdgeOutput)
    result = temp_chain.invoke({
            'text': state["text"],
            'node_entity': state["node_group"],
            'edge_analysis': state["edge_analysis"]
        })
    print("generate_edge_entity done.")
    return {"edge_group": result.edges}

def write_to_neo4j(state: KGGenState):
    nodes = state["node_group"]
    edges = state["edge_group"]
    for node in nodes:
        props = node.model_dump()
        print(props)
        props = {k: v for k, v in props.items() if v is not None}

        label = node.node_type  # 自动标签

        cypher = f"""
        MERGE (n:{label} {{id: $id}})
        SET n += $props
        """

        graph.query(
            cypher,
            params={
                "id": node.id,
                "props": props
            }
        )
    for edge in edges:
        props = edge.model_dump()
        print(props)
        props = {k: v for k, v in props.items() if v is not None}

        rel_type = edge.edge_info

        cypher = f"""
        MATCH (s {{id: $source_id}})
        MATCH (t {{id: $target_id}})
        MERGE (s)-[r:`{rel_type}`]->(t)
        """

        graph.query(
            cypher,
            params={
                "source_id": edge.source.id,
                "target_id": edge.target.id
            }
        )


# Build workflow
workflow = StateGraph(KGGenState)
workflow.add_node("generate_node_analysis", generate_node_analysis)
workflow.add_node("generate_node_entity", generate_node_entity)
workflow.add_node("generate_edge_analysis", generate_edge_analysis)
workflow.add_node("generate_edge_entity", generate_edge_entity)
workflow.add_node("write_to_neo4j", write_to_neo4j)
workflow.add_node("clear_neo4j", clear_neo4j)

workflow.add_edge(START, "clear_neo4j")
workflow.add_edge("clear_neo4j", "generate_node_analysis")
workflow.add_edge("generate_node_analysis", "generate_node_entity")
workflow.add_edge("generate_node_entity", "generate_edge_analysis")
workflow.add_edge("generate_edge_analysis", "generate_edge_entity")
workflow.add_edge("generate_edge_entity", "write_to_neo4j")
workflow.add_edge("write_to_neo4j", END)

chain = workflow.compile()

if __name__ == "__main__":
    sample_1 = """调节器检查内容和周期 表4.3.7
    序号 检查内容 检查方式 检查周期
    1 轨距、水平、高低、轨向、三角坑 全面检测 每月检查1遍
    活动钢枕与梁端固定轨枕（钢枕）、
    2 相邻活动钢枕间的间距差，轨枕偏 全面检测 每月检查1遍
    斜
    3 尖轨与基本轨间间隙 全面查看，重点检测 每月检查1遍
    扣件、垫板、联结零件、以及梁端
    伸缩装置活动钢枕、剪刀叉（剪刀
    4 全面查看，重点检测 每月检查1遍
    装置）、纵梁（联结钢梁）等部件状
    态
    5 各部螺栓扭矩 全面查看，重点检测 每月检查1遍
    6 有砟调节器轨枕状态 全面查看，重点检测 每月检查1遍
    7 有砟道床状态 全面查看，重点检测 每月检查1遍
    8 无砟道床状态 全面查看，重点检测 每季检查1遍
    9 尖轨相对于基本轨降低值 全面检测 每季检查1遍
    第4.3.8条 对无缝线路、道岔钢轨纵向位移观测，每半年不少于1次，一般春、
    秋季各1次，对桥上无缝道岔、调节器等地段钢轨纵向位移每季观测 1次，按附录五
    记录观测结果；对纵向位移超过 10mm 及需进行应力放散和调整的区段应分析原因，
    及时处理。对调节器基本轨伸缩量、焊缝位置与气温关系应定期进行分析，发现伸缩
    异常应及时处理。
    第4.3.9条 对标志标识每年检查不少于1遍。
    第4.3.10条 线路设备的巡检要求。
    一、应根据线路速度等级、设备条件、列车对数等情况，合理确定线路设备人工
    巡检要求，应加强对道岔、调节器、大跨度桥梁、过渡段和沉降等重点地段的线路设
    备巡检，具体办法由铁路局集团公司规定。
    二、正线及到发线道岔人工巡检，每 10 天不少于 1 遍，其他道岔每月不少于 1
    遍。调节器人工巡检每月不少于 2遍。当人工巡检与周期性检查时间重叠时，按周期
    性检查办理。
    第四节 钢 轨 检 查      
    45"""
    sample_2 = """
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
    测量并调整；曲股方向不良时，应在直股方向符合要求的基础上，通过控制支距的方
    """
    state = chain.invoke({
        "text": sample_1
    })
