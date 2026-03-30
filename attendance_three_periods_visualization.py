
# -*- coding: utf-8 -*-
"""
读取考勤 Excel，并把某一天内“3个打卡时段”下每个人的状态可视化。
适配当前这类表头结构：
- 第1~2行为说明
- 第3行为字段名
- 第4行可能是空行/子表头
- 数据从后续行开始

输出：
1) 人员 × 三个时段 的热力图（带中文标注）
2) 各时段状态人数统计柱状图

使用方法：
python attendance_three_periods_visualization.py
或
python attendance_three_periods_visualization.py --file "你的表.xlsx" --date "26-03-15 星期日"
"""

from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import font_manager


# =========================
# 可直接修改的参数
# =========================
DEFAULT_FILE = "291b9ea4-cc73-417d-aae4-a5124a05c513.xlsx"
DEFAULT_OUTPUT_DIR = "attendance_viz_output"

# 中文显示设置：自动选择本机可用中文字体
_CANDIDATE_FONTS = [
    "Noto Sans CJK SC", "Microsoft YaHei", "SimHei",
    "Arial Unicode MS", "Noto Serif CJK SC", "AR PL UMing CN", "DejaVu Sans"
]
_available_fonts = {f.name for f in font_manager.fontManager.ttflist}
for _font in _CANDIDATE_FONTS:
    if _font in _available_fonts:
        plt.rcParams["font.sans-serif"] = [_font]
        break
plt.rcParams["axes.unicode_minus"] = False


def make_unique_columns(columns):
    """处理重复列名 / 空列名。"""
    counts = {}
    new_cols = []
    for col in columns:
        name = str(col).strip() if col is not None else ""
        if name == "" or name.lower() == "none":
            name = "空列"
        counts[name] = counts.get(name, 0) + 1
        if counts[name] == 1:
            new_cols.append(name)
        else:
            new_cols.append(f"{name}_{counts[name]}")
    return new_cols


def find_header_row(raw_df: pd.DataFrame) -> int:
    """自动寻找表头行（包含 姓名 / 日期 等关键字段）。"""
    required = {"姓名", "日期"}
    for i in range(min(10, len(raw_df))):
        vals = set(str(v).strip() for v in raw_df.iloc[i].tolist() if pd.notna(v))
        if required.issubset(vals):
            return i
    raise ValueError("未找到表头行，请检查 Excel 结构。")


def load_attendance(file_path: str | Path) -> pd.DataFrame:
    """读取并清洗考勤表。"""
    raw = pd.read_excel(file_path, header=None)
    header_row = find_header_row(raw)

    df = raw.iloc[header_row + 1:].copy()
    df.columns = make_unique_columns(raw.iloc[header_row].tolist())
    df = df.reset_index(drop=True)

    # 删除完全空白行
    df = df.dropna(how="all").copy()

    # 删除类似“工作日加班/休息日加班/节假日加班”的子表头行
    if "姓名" in df.columns:
        df = df[df["姓名"].notna()].copy()

    # 常用字段转为字符串，便于统一处理
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].astype(str).replace({"nan": "", "None": ""}).str.strip()

    return df


def choose_target_date(df: pd.DataFrame, target_date: str | None = None) -> str:
    """优先用用户指定日期，否则自动选择‘有打卡结果的最新日期’。"""
    status_cols = [
        "上班1打卡结果", "下班1打卡结果",
        "上班2打卡结果", "下班2打卡结果",
        "上班3打卡结果", "下班3打卡结果",
    ]
    for col in status_cols:
        if col not in df.columns:
            df[col] = ""

    if target_date:
        if target_date not in set(df["日期"].astype(str)):
            raise ValueError(f"指定日期不存在：{target_date}")
        return target_date

    tmp = df.copy()
    tmp["有记录"] = tmp[status_cols].fillna("").astype(str).apply(
        lambda r: any(str(v).strip() != "" for v in r), axis=1
    )
    valid = tmp[tmp["有记录"]].copy()
    if valid.empty:
        # 如果没有任何打卡结果，就退回到最后一个日期
        return str(df["日期"].dropna().iloc[-1])
    return str(valid["日期"].iloc[-1])


def norm_text(x) -> str:
    if pd.isna(x):
        return ""
    s = str(x).strip()
    if s.lower() in {"nan", "none"}:
        return ""
    return s


def merge_period_status(in_status: str, out_status: str) -> str:
    """
    将一个时段的上班/下班状态合并成一个总状态。
    规则可按需要继续细化。
    """
    a = norm_text(in_status)
    b = norm_text(out_status)
    vals = [v for v in [a, b] if v]

    if not vals:
        return "无记录"

    text = " ".join(vals)

    if any(k in text for k in ["旷工", "严重迟到"]):
        return "严重异常"
    if any(k in text for k in ["迟到", "早退"]):
        return "迟到/早退"
    # 两端都有异常打卡
    if all(any(k in v for k in ["缺卡", "未打卡"]) for v in vals):
        return "缺卡/未打卡"
    # 一端正常，一端异常
    if any(k in text for k in ["缺卡", "未打卡"]):
        return "部分异常"
    if "外勤" in text:
        return "外勤"
    if all("正常" in v for v in vals):
        return "正常"
    return "其他"


def build_person_period_table(df: pd.DataFrame, target_date: str) -> pd.DataFrame:
    """构造‘每个人 × 3个时段’状态表。"""
    sub = df[df["日期"].astype(str) == str(target_date)].copy()
    if sub.empty:
        raise ValueError(f"日期 {target_date} 无数据。")

    result = pd.DataFrame({
        "姓名": sub["姓名"].astype(str),
        "时段1": [
            merge_period_status(a, b)
            for a, b in zip(sub.get("上班1打卡结果", ""), sub.get("下班1打卡结果", ""))
        ],
        "时段2": [
            merge_period_status(a, b)
            for a, b in zip(sub.get("上班2打卡结果", ""), sub.get("下班2打卡结果", ""))
        ],
        "时段3": [
            merge_period_status(a, b)
            for a, b in zip(sub.get("上班3打卡结果", ""), sub.get("下班3打卡结果", ""))
        ],
    })

    # 按姓名排序，图更整齐
    result = result.sort_values("姓名").reset_index(drop=True)
    return result


def plot_heatmap(person_period_df: pd.DataFrame, output_path: str | Path, title: str):
    """画‘人员 × 时段’热力图，并写中文标注。"""
    plot_df = person_period_df.set_index("姓名")

    ordered_labels = [
        "正常", "外勤", "无记录", "部分异常",
        "缺卡/未打卡", "迟到/早退", "严重异常", "其他"
    ]
    label_to_num = {lab: i for i, lab in enumerate(ordered_labels)}

    numeric = plot_df.apply(lambda col: col.map(lambda x: label_to_num.get(x, label_to_num["其他"]))).values

    fig_w = max(8, 1.6 * plot_df.shape[1] + 3)
    fig_h = max(6, 0.45 * plot_df.shape[0] + 2.5)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))

    im = ax.imshow(numeric)

    ax.set_xticks(range(plot_df.shape[1]))
    ax.set_xticklabels(plot_df.columns, fontsize=11)
    ax.set_yticks(range(plot_df.shape[0]))
    ax.set_yticklabels(plot_df.index, fontsize=10)

    # 单元格内写入状态文字
    for i in range(plot_df.shape[0]):
        for j in range(plot_df.shape[1]):
            ax.text(j, i, plot_df.iloc[i, j], ha="center", va="center", fontsize=9)

    ax.set_title(title, fontsize=14)
    ax.set_xlabel("时间段", fontsize=11)
    ax.set_ylabel("人员", fontsize=11)

    # 图例
    cbar = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.04)
    cbar.set_ticks(list(label_to_num.values()))
    cbar.set_ticklabels(list(label_to_num.keys()))

    plt.tight_layout()
    plt.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close()


def plot_status_summary(person_period_df: pd.DataFrame, output_path: str | Path, title: str):
    """画各时段不同状态的人数统计图。"""
    long_df = person_period_df.melt(id_vars="姓名", var_name="时段", value_name="状态")
    summary = long_df.groupby(["时段", "状态"]).size().unstack(fill_value=0)

    # 为了图例顺序一致
    ordered_labels = [
        "正常", "外勤", "无记录", "部分异常",
        "缺卡/未打卡", "迟到/早退", "严重异常", "其他"
    ]
    summary = summary.reindex(columns=[c for c in ordered_labels if c in summary.columns], fill_value=0)

    fig, ax = plt.subplots(figsize=(10, 6))
    summary.plot(kind="bar", ax=ax)

    ax.set_title(title, fontsize=14)
    ax.set_xlabel("时间段", fontsize=11)
    ax.set_ylabel("人数", fontsize=11)
    ax.tick_params(axis="x", rotation=0)
    plt.tight_layout()
    plt.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", default=DEFAULT_FILE, help="Excel 文件路径")
    parser.add_argument("--date", default=None, help="指定日期，例如：26-03-15 星期日")
    parser.add_argument("--outdir", default=DEFAULT_OUTPUT_DIR, help="输出目录")
    args = parser.parse_args()

    file_path = Path(args.file)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    df = load_attendance(file_path)
    target_date = choose_target_date(df, args.date)
    person_period_df = build_person_period_table(df, target_date)

    # 导出中间结果，方便你核对
    person_period_df.to_excel(outdir / "每人三个时段状态汇总.xlsx", index=False, engine="openpyxl")
    person_period_df.to_csv(outdir / "每人三个时段状态汇总.csv", index=False, encoding="utf-8-sig")

    plot_heatmap(
        person_period_df,
        outdir / "人员_三个时段状态热力图.png",
        title=f"{target_date} 每人三个时段状态"
    )

    plot_status_summary(
        person_period_df,
        outdir / "三个时段状态人数统计.png",
        title=f"{target_date} 三个时段状态人数统计"
    )

    print(f"已完成，输出目录：{outdir.resolve()}")
    print(f"自动识别日期：{target_date}")


if __name__ == "__main__":
    main()
