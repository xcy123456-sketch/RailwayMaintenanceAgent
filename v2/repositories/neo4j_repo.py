from langchain_neo4j import Neo4jGraph
from repo_schema import *
from typing_extensions import Type


NODE_CLASS_MAP: dict[str, Type[KGNode]] = {
    "Infrastructure": KGNode_Infrastructure,
    "Defect": KGNode_Defect,
    "Threshold": KGNode_Threshold,
    "Inspection": KGNode_Inspection,
}

EDGE_CLASS_MAP: dict[str, Type[KGNode]] = {
    "Infrastructure": KGNode_Infrastructure,
    "Defect": KGNode_Defect,
    "Threshold": KGNode_Threshold,
    "Inspection": KGNode_Inspection,
}

# Neo4j数据访问层，提供读写接口
class KGRepo:
    def __init__(self, driver: Neo4jGraph):
        self.driver = driver

    def get_nodes_and_edges(self):
        # 1) 获取所有节点
        nodes = self.driver.query("""
        MATCH (n)
        RETURN
        elementId(n) AS element_id,
        labels(n) AS labels,
        properties(n) AS props    
        """)
        node_entities = {}
        for node in nodes:
            props = node.get("props", {})
            node_type = props.get("node_type")
            node_id = props.get("id")
            if node_type not in NODE_CLASS_MAP.keys():
                print(f"Unknown node type: {node_type}, skipping...")
                continue
            node_entities[node_id] = NODE_CLASS_MAP[node_type](**props)
        edges = self.driver.query("""
        MATCH (s)-[r]->(t)
        RETURN s, r, t        
        """)
        edge_entities = []
        for edge in edges[0:1]:
            source_id = edge.get("s", {}).get("id")
            target_id = edge.get("t", {}).get("id")
            edge_entities.append(KGEdge(
                source=node_entities.get(source_id),
                target=node_entities.get(target_id),
                edge_info=edge.get("r", {})[1]
            ))
        return node_entities, edge_entities

    def write_to_neo4j(self, subgraph):
        for node in subgraph.nodes:
            self.upsert_node(node)
        for edge in subgraph.edges:
            self.upsert_edge(edge)
    
    def clear_neo4j(self):
        cypher = "MATCH (n) DETACH DELETE n"
        self.driver.query(cypher)
    
    def upsert_node(self, node):
        label = node.node_type
        props = node.dict()
        cypher = f"""
        MERGE (n:{label} {{id: $id}})
        SET n += $props
        RETURN n.id AS id
        """
        self.driver.query(cypher, params={
            "id": node.id,
            "props": props
        })
    
    def upsert_edge(self, edge):
        cypher = """
        MATCH (s {id: $source_id})
        MATCH (t {id: $target_id})
        MERGE (s)-[r:RELATED_TO {edge_info: $edge_info}]->(t)
        RETURN count(r) AS merged_count
        """
        self.driver.query(cypher, params={
            "source_id": edge.source.id,
            "target_id": edge.target.id,
            "edge_info": edge.edge_info
        })

if __name__ == "__main__":
    import os
    import dotenv
    # 初始化Neo4j连接
    os.environ["NEO4J_URI"] = dotenv.get_key(dotenv.find_dotenv(), "NEO4J_URI")
    os.environ["NEO4J_USERNAME"] = dotenv.get_key(dotenv.find_dotenv(), "NEO4J_USERNAME")
    os.environ["NEO4J_PASSWORD"] = dotenv.get_key(dotenv.find_dotenv(), "NEO4J_PASSWORD")
    graph = Neo4jGraph(
        url=os.environ["NEO4J_URI"],
        username=os.environ["NEO4J_USERNAME"],
        password=os.environ["NEO4J_PASSWORD"],
    )
    repo = KGRepo(graph)
    repo.get_nodes_and_edges()
