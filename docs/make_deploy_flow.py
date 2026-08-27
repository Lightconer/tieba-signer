#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成「百度贴吧自动签到 · 部署与运行流程图」。
输出: docs/deploy_flow.png
运行: python docs/make_deploy_flow.py
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "SimSun", "PingFang SC", "Noto Sans CJK SC"]
plt.rcParams["axes.unicode_minus"] = False

# 阶段配色
STAGES = {
    "user":  {"face": "#DEEBF7", "edge": "#2E75B6", "label": "用户操作\n（一次性配置）"},
    "manual": {"face": "#E4DFEC", "edge": "#7030A0", "label": "手动触发\n（首次运行）"},
    "auto":   {"face": "#E2EFDA", "edge": "#548235", "label": "每日自动\n（GitHub Actions）"},
}

# 步骤: (文字, 阶段)
STEPS = [
    ("1.  登录百度贴吧，F12 复制 BDUSS", "user"),
    ("2.  Fork 本项目到你的 GitHub", "user"),
    ("3.  Settings → Secrets 添加 BDUSS", "user"),
    ("4.  Settings → Actions 开启工作流", "user"),
    ("5.  Actions 页 Run workflow 手动触发（首次）", "manual"),
    ("6.  每日 06:30 定时触发（cron）", "auto"),
    ("7.  检出代码 · 安装 Python 依赖", "auto"),
    ("8.  运行 tieba_sign.py", "auto"),
    ("9.  获取 tbs · 校验 BDUSS 登录态", "auto"),
    ("10.  获取关注的吧列表（≤ 200）", "auto"),
    ("11.  逐吧调用手机端签到接口（经验 +6）", "auto"),
    ("12.  输出签到统计 · 流程结束", "auto"),
]

W, H = 10, 15
fig, ax = plt.subplots(figsize=(W, H), dpi=160)
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")

# 标题
ax.text(0.5, 0.962, "百度贴吧自动签到 · 部署与运行流程图",
        ha="center", va="center", fontsize=20, fontweight="bold", color="#1F3864")
ax.text(0.5, 0.932, "手机端签到接口 · 单吧经验 +6（PC 端 +2）· 仅需 BDUSS · 每日自动 · 最多 200 吧",
        ha="center", va="center", fontsize=11, color="#595959")

# 布局参数
start_y = 0.880
box_h = 0.034
gap = 0.024
pitch = box_h + gap
box_w = 0.52
box_l = 0.24
cx = box_l + box_w / 2

# 先计算各阶段标签的纵向范围
stage_ys = {}
for i, (_, stage) in enumerate(STEPS):
    yc = start_y - i * pitch
    stage_ys.setdefault(stage, []).append(yc)

# 左侧阶段标签
for stage, ys in stage_ys.items():
    y_top = max(ys) + box_h / 2
    y_bot = min(ys) - box_h / 2
    y_mid = (y_top + y_bot) / 2
    ax.add_patch(FancyBboxPatch(
        (0.055, y_bot), 0.145, y_top - y_bot,
        boxstyle="round,pad=0.004", linewidth=1.2,
        facecolor=STAGES[stage]["face"], edgecolor=STAGES[stage]["edge"], alpha=0.85,
    ))
    ax.text(0.127, y_mid, STAGES[stage]["label"], ha="center", va="center",
            fontsize=9.5, color=STAGES[stage]["edge"], fontweight="bold")

# 绘制步骤框与箭头
for i, (text, stage) in enumerate(STEPS):
    yc = start_y - i * pitch
    ax.add_patch(FancyBboxPatch(
        (box_l, yc - box_h / 2), box_w, box_h,
        boxstyle="round,pad=0.004", linewidth=1.4,
        facecolor=STAGES[stage]["face"], edgecolor=STAGES[stage]["edge"],
    ))
    ax.text(cx, yc, text, ha="center", va="center", fontsize=10.5, color="#1F1F1F")

    if i < len(STEPS) - 1:
        yc_next = start_y - (i + 1) * pitch
        ax.add_patch(FancyArrowPatch(
            (cx, yc - box_h / 2 - 0.003), (cx, yc_next + box_h / 2 + 0.003),
            arrowstyle="-|>", mutation_scale=16, linewidth=1.6, color="#7F7F7F",
        ))

# 底部注释
ax.text(0.5, 0.05,
        "提示：部署后仅需在仓库 Secrets 中配置 BDUSS，其余流程全部自动化。",
        ha="center", va="center", fontsize=10, color="#808080")

out_dir = os.path.dirname(os.path.abspath(__file__))
out = os.path.join(out_dir, "deploy_flow.png")
fig.savefig(out, bbox_inches="tight", facecolor="white")
plt.close(fig)
print("流程图已生成:", out)
