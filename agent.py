import os
from langchain_neo4j import Neo4jGraph

os.environ["NEO4J_URI"] = "bolt://localhost:7687"
os.environ["NEO4J_USERNAME"] = "neo4j"
os.environ["NEO4J_PASSWORD"] = "12345678"

graph = Neo4jGraph()

# 写入一点数据（Cypher）
graph.query("""
MERGE (p:Person {name:'Alice'})
MERGE (q:Person {name:'Bob'})
MERGE (p)-[:KNOWS]->(q)
""")

# 查询
res = graph.query("MATCH (p:Person)-[:KNOWS]->(q:Person) RETURN p.name, q.name")
print(res)