# -*- coding: utf-8 -*-
"""
绘制“数据-病理-决策”异构知识图谱示意图
适用于：重载铁路轨道病害诊断、知识图谱+大模型思维链推理框架图

运行环境：
pip install networkx matplotlib

如果中文显示异常，可把 font.sans-serif 改成你电脑已有中文字体：
如 ['SimHei']、['Microsoft YaHei']、['STSong']
"""

import matplotlib.pyplot as plt
import networkx as nx
plt.rcParams['font.sans-serif'] = ['SimHei', 'Liberation Sans']
# =========================
# 1. 基础绘图配置
# =========================
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False

# =========================
# 2. 创建有向图
# =========================
G = nx.DiGraph()

# =========================
# 3. 定义分层节点
# =========================
feature_nodes = [
    "振噪异常",
    "GPR介电异常",
    "轨道几何突变",
    "轮轨冲击增大",
    "轨枕/扣件异常响应",
]

state_nodes = [
    "支承刚度衰减",
    "道砟细粒侵入",
    "局部脱空",
    "结构不均匀支撑",
    "累积损伤加剧",
]

disease_nodes = [
    "钢轨波磨",
    "翻浆冒泥",
    "道床板结",
    "轨道不平顺劣化",
    "扣件失效",
]

decision_nodes = [
    "限速预警",
    "精细化巡检",
    "捣固整治",
    "清筛换砟",
    "扣件更换",
    "大修方案生成",
]

# 给节点添加类别属性
for n in feature_nodes:
    G.add_node(n, layer="feature")
for n in state_nodes:
    G.add_node(n, layer="state")
for n in disease_nodes:
    G.add_node(n, layer="disease")
for n in decision_nodes:
    G.add_node(n, layer="decision")

# =========================
# 4. 定义因果边
# =========================
edges = [
    # 监测特征 -> 物理状态
    ("振噪异常", "支承刚度衰减"),
    ("振噪异常", "局部脱空"),
    ("GPR介电异常", "道砟细粒侵入"),
    ("轨道几何突变", "结构不均匀支撑"),
    ("轮轨冲击增大", "累积损伤加剧"),
    ("轨枕/扣件异常响应", "支承刚度衰减"),

    # 物理状态 -> 病害类型
    ("支承刚度衰减", "轨道不平顺劣化"),
    ("支承刚度衰减", "扣件失效"),
    ("道砟细粒侵入", "翻浆冒泥"),
    ("道砟细粒侵入", "道床板结"),
    ("局部脱空", "轨道不平顺劣化"),
    ("结构不均匀支撑", "钢轨波磨"),
    ("累积损伤加剧", "钢轨波磨"),
    ("累积损伤加剧", "扣件失效"),

    # 病害类型 -> 决策方案
    ("钢轨波磨", "精细化巡检"),
    ("钢轨波磨", "捣固整治"),
    ("翻浆冒泥", "清筛换砟"),
    ("道床板结", "清筛换砟"),
    ("轨道不平顺劣化", "限速预警"),
    ("轨道不平顺劣化", "捣固整治"),
    ("扣件失效", "扣件更换"),

    # 决策汇总
    ("精细化巡检", "大修方案生成"),
    ("捣固整治", "大修方案生成"),
    ("清筛换砟", "大修方案生成"),
    ("扣件更换", "大修方案生成"),
    ("限速预警", "大修方案生成"),
]

G.add_edges_from(edges)

# =========================
# 5. 手动布局（分层）
# =========================
pos = {}

# 横向四列，纵向均匀排布
x_feature = 0
x_state = 3
x_disease = 6
x_decision = 9

feature_y = [8, 6, 4, 2, 0]
state_y = [8, 6, 4, 2, 0]
disease_y = [8, 6, 4, 2, 0]
decision_y = [10, 8, 6, 4, 2, 0]

for i, n in enumerate(feature_nodes):
    pos[n] = (x_feature, feature_y[i])
for i, n in enumerate(state_nodes):
    pos[n] = (x_state, state_y[i])
for i, n in enumerate(disease_nodes):
    pos[n] = (x_disease, disease_y[i])
for i, n in enumerate(decision_nodes):
    pos[n] = (x_decision, decision_y[i])

# =========================
# 6. 设置颜色
# =========================
layer_color = {
    "feature": "#5B8FF9",   # 蓝
    "state": "#61DDAA",     # 绿
    "disease": "#F6BD16",   # 黄
    "decision": "#E8684A",  # 橙红
}

node_colors = [layer_color[G.nodes[n]["layer"]] for n in G.nodes()]

# =========================
# 7. 定义需要高亮的“思维链推理路径”
# =========================
reasoning_path = [
    ("振噪异常", "支承刚度衰减"),
    ("支承刚度衰减", "轨道不平顺劣化"),
    ("轨道不平顺劣化", "限速预警"),
    ("限速预警", "大修方案生成"),
]

# 其余边
other_edges = [e for e in G.edges() if e not in reasoning_path]

# =========================
# 8. 开始绘图
# =========================
fig, ax = plt.subplots(figsize=(16, 9))
ax.set_facecolor("white")

# 先画普通边
nx.draw_networkx_edges(
    G,
    pos,
    edgelist=other_edges,
    edge_color="#B0B0B0",
    width=1.6,
    alpha=0.8,
    arrows=True,
    arrowsize=18,
    arrowstyle="-|>",
    ax=ax
)

# 再画高亮思维链
nx.draw_networkx_edges(
    G,
    pos,
    edgelist=reasoning_path,
    edge_color="#D62728",
    width=3.5,
    alpha=0.95,
    arrows=True,
    arrowsize=22,
    arrowstyle="-|>",
    ax=ax
)

# 画节点
nx.draw_networkx_nodes(
    G,
    pos,
    node_color=node_colors,
    node_size=2600,
    edgecolors="#2F2F2F",
    linewidths=1.2,
    ax=ax
)

# 画标签
nx.draw_networkx_labels(
    G,
    pos,
    font_size=13,
    font_weight="bold",
    font_color="black",
    ax=ax
)

# =========================
# 9. 添加分层标题
# =========================
ax.text(x_feature, 11.5, "多源监测特征层", ha="center", va="center",
        fontsize=16, fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.35", facecolor="#DCEBFF", edgecolor="#5B8FF9"))

ax.text(x_state, 11.5, "物理演化状态层", ha="center", va="center",
        fontsize=16, fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.35", facecolor="#DDF7ED", edgecolor="#61DDAA"))

ax.text(x_disease, 11.5, "典型病害层", ha="center", va="center",
        fontsize=16, fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.35", facecolor="#FFF3CC", edgecolor="#F6BD16"))

ax.text(x_decision, 11.5, "维修决策层", ha="center", va="center",
        fontsize=16, fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.35", facecolor="#FCE3DD", edgecolor="#E8684A"))

# =========================
# 10. 添加说明文字
# =========================
ax.text(
    4.5, -1.8,
    "红色路径表示：大模型思维链推理（异常识别 → 状态推断 → 病害诊断 → 决策生成）",
    ha="center",
    va="center",
    fontsize=13,
    color="#D62728",
    fontweight="bold"
)

ax.text(
    4.5, -2.8,
    "图：融合知识图谱与大模型生成式推理的重载铁路轨道病害智能诊断示意图",
    ha="center",
    va="center",
    fontsize=14,
    color="black"
)

# =========================
# 11. 美化并保存
# =========================
ax.set_xlim(-1.5, 10.5)
ax.set_ylim(-3.5, 12.5)
ax.axis("off")
plt.tight_layout()

output_path = "railway_knowledge_graph.png"
plt.savefig(output_path, dpi=300, bbox_inches="tight", facecolor="white")
plt.show()

print(f"图已保存到: {output_path}")