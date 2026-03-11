# RailwayMaintenanceAgent
徐博士的第一个github项目，目前正在进行中。

项目主要面向高速铁路智能运维，想把修规集成到大模型智能体中，实现维修自动和决策。

### 前期准备
#### Neo4j的docker容器配置 
1. 安装docker
2. 运行docker-compose.yml拉取neo4j镜像
3. 执行以下代码将docker内核中的apoccore放到neo4j的plugins中
```bash
docker exec -it neo4j bash -lc "cp /var/lib/neo4j/labs/*apoc*core*.jar /plugins/ 2>/dev/null || cp /labs/*apoc*core*.jar /plugins/"
```
4. 清理旧容器
```bash
docker compose down -v
```
5. 重启
```bash
docker compose up -d
```
> **注意：** 直接运行可能会出现未连接数据库的情况，因为数据库还在加载，稍等片刻即可。

### 图数据库约束
