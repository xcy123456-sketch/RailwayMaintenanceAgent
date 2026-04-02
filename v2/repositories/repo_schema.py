from typing_extensions import TypedDict, List, Annotated, Literal
from pydantic import BaseModel, Field, model_validator


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

