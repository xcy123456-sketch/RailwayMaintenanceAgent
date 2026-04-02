import os
import dotenv
from typing import List, Literal
from pydantic import BaseModel, Field, model_validator

# =========================
# 1. Neo4j 连接
# =========================
os.environ["NEO4J_URI"] = dotenv.get_key(dotenv.find_dotenv(), "NEO4J_URI")
os.environ["NEO4J_USERNAME"] = dotenv.get_key(dotenv.find_dotenv(), "NEO4J_USERNAME")
os.environ["NEO4J_PASSWORD"] = dotenv.get_key(dotenv.find_dotenv(), "NEO4J_PASSWORD")

from langchain_neo4j import Neo4jGraph

graph = Neo4jGraph(
    url=os.environ["NEO4J_URI"],
    username=os.environ["NEO4J_USERNAME"],
    password=os.environ["NEO4J_PASSWORD"],
)

# =========================
# 2. 节点 / 边定义
# =========================
class KGNode(BaseModel):
    id: str = Field(description="节点唯一ID，格式为 节点类型:节点名称")
    name: str = Field(description="节点名称")
    node_type: str = Field(description="节点类型")

    @model_validator(mode="after")
    def check_id(self):
        expected = f"{self.node_type}:{self.name}"
        if self.id != expected:
            self.id = expected
        return self


class KGNode_Infrastructure(KGNode):
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
    description: str = Field(description="阈值描述")
    impact: str = Field(description="阈值相关影响")


class KGNode_Inspection(KGNode):
    node_type: Literal["Inspection"] = "Inspection"
    infrastructure: str = Field(description="巡检对应的基础设施")
    description: str = Field(description="巡检说明")


class KGEdge(BaseModel):
    source: KGNode = Field(description="起点节点")
    target: KGNode = Field(description="终点节点")
    edge_info: str = Field(description="关系名称")


# =========================
# 3. 工具函数
# =========================
def node_to_props(node: KGNode) -> dict:
    """Pydantic 节点对象 -> Neo4j 属性字典"""
    return node.model_dump(exclude_none=True)


def deduplicate_nodes(nodes: List[KGNode]) -> List[KGNode]:
    """按 id 去重，后出现的覆盖前面的"""
    node_map = {}
    for node in nodes:
        node_map[node.id] = node
    return list(node_map.values())


def deduplicate_edges(edges: List[KGEdge]) -> List[KGEdge]:
    """按 (source.id, target.id, edge_info) 去重"""
    edge_map = {}
    for edge in edges:
        key = (edge.source.id, edge.target.id, edge.edge_info)
        edge_map[key] = edge
    return list(edge_map.values())


# =========================
# 4. 写入 Neo4j
# =========================
def merge_node_to_neo4j(node: KGNode):
    """
    按 id 合并节点。
    每种 node_type 对应一个 Neo4j label。
    """
    label = node.node_type
    props = node_to_props(node)

    cypher = f"""
    MERGE (n:{label} {{id: $id}})
    SET n += $props
    RETURN n.id AS id
    """

    graph.query(cypher, params={
        "id": node.id,
        "props": props
    })


def merge_edge_to_neo4j(edge: KGEdge):
    """
    关系统一使用 RELATED_TO，edge_info 作为属性。
    这样最稳，不需要动态关系类型。
    """
    cypher = """
    MATCH (s {id: $source_id})
    MATCH (t {id: $target_id})
    MERGE (s)-[r:RELATED_TO {edge_info: $edge_info}]->(t)
    RETURN count(r) AS merged_count
    """

    graph.query(cypher, params={
        "source_id": edge.source.id,
        "target_id": edge.target.id,
        "edge_info": edge.edge_info
    })


# =========================
# 5. 知识图谱合并主函数
# =========================
def merge_KG(subgraph_nodes: List[KGNode], subgraph_edges: List[KGEdge]):
    """
    直接把新子图合并进现有 Neo4j 图谱：
    - 相同 id 的节点：更新属性
    - 不同 id 的节点：新增
    - 相同 (source, target, edge_info) 的关系：去重
    - 不同关系：新增
    """
    # 先对子图内部去重
    subgraph_nodes = deduplicate_nodes(subgraph_nodes)
    subgraph_edges = deduplicate_edges(subgraph_edges)

    # 1) 先合并所有节点
    for node in subgraph_nodes:
        merge_node_to_neo4j(node)

    # 2) 再合并所有关系
    for edge in subgraph_edges:
        # 为稳妥起见，确保端点节点一定存在
        merge_node_to_neo4j(edge.source)
        merge_node_to_neo4j(edge.target)
        merge_edge_to_neo4j(edge)

    print(f"合并完成：节点 {len(subgraph_nodes)} 个，关系 {len(subgraph_edges)} 条")


# =========================
# 6. 示例
# =========================
if __name__ == "__main__":
    # 示例节点
    n1 = KGNode_Infrastructure(
        id="Infrastructure:轨道",
        name="轨道"
    )

    n2 = KGNode_Defect(
        id="Defect:裂纹",
        name="裂纹",
        infrastructure="轨道",
        cause="疲劳荷载",
        impact="降低结构安全性"
    )

    n3 = KGNode_Threshold(
        id="Threshold:轨道裂纹限值",
        name="轨道裂纹限值",
        infrastructure="轨道",
        defect="裂纹",
        description="裂纹长度不应超过规定值",
        impact="超限需维修"
    )

    n4 = KGNode_Inspection(
        id="Inspection:轨道巡检",
        name="轨道巡检",
        infrastructure="轨道",
        description="定期检查轨道表面状态"
    )

    # 示例关系
    e1 = KGEdge(source=n1, target=n2, edge_info="has_defect")
    e2 = KGEdge(source=n2, target=n3, edge_info="has_threshold")
    e3 = KGEdge(source=n1, target=n4, edge_info="requires_inspection")

    subgraph_nodes = [n1, n2, n3, n4]
    subgraph_edges = [e1, e2, e3]

    merge_KG(subgraph_nodes, subgraph_edges)