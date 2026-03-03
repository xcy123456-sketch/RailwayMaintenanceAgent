# RailwayMaintenanceAgent

### 前期准备
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
> 直接运行可能会出现未连接数据库的情况，因为数据库还在加载，稍等片刻即可。