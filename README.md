# RailwayMaintenanceAgent

### 前期准备
1. 安装docker
2. 运行docker-compose.yml拉取neo4j镜像
3. 执行以下代码将docker内核中的apoccore放到neo4j的plugins中
```bash
docker exec -it neo4j bash -lc "cp /var/lib/neo4j/labs/*apoc*core*.jar /plugins/ 2>/dev/null || cp /labs/*apoc*core*.jar /plugins/"
```