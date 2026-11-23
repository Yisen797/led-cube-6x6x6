# -*- coding: utf-8 -*-
"""生成 A4 1:1 钻孔图纸（20mm 孔距，6×6）"""
import matplotlib
matplotlib.use('Agg')
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
matplotlib.rcParams['axes.unicode_minus'] = False

import matplotlib.pyplot as plt
from matplotlib.patches import Circle

MM = 1.0 / 25.4  # inch per mm
fig = plt.figure(figsize=(210 * MM, 297 * MM))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 210)
ax.set_ylim(0, 297)
ax.set_aspect('equal')
ax.axis('off')

P = 20.0
N = 6
SPAN = (N - 1) * P
X0, Y0 = (210 - SPAN) / 2, 100.0      # 居中放置 (0,0)

# 外框
ax.add_patch(plt.Rectangle((10, 10), 190, 277, fill=False, lw=0.6, ec='#999999'))

# 标题与说明
ax.text(105, 278, '6 × 6 × 6 光立方  单层钻孔图（1:1）', ha='center', va='center',
        fontsize=13, fontweight='bold')
ax.text(105, 270, '孔距 20 mm   ·   孔径 3.2 mm   ·   板厚 2–3 mm   ·   打印请选 100% 实际大小',
        ha='center', va='center', fontsize=8.5, color='#333333')
ax.text(105, 263, '把本页贴在板上 → 锥子打定位坑 → 3.2 mm 钻头钻穿 → 撕掉纸',
        ha='center', va='center', fontsize=8.5, color='#333333')

# 网格参考线
for i in range(N):
    x = X0 + i * P
    ax.plot([x, x], [Y0, Y0 + SPAN], color='#DDDDDD', lw=0.5, zorder=1)
for j in range(N):
    y = Y0 + j * P
    ax.plot([X0, X0 + SPAN], [y, y], color='#DDDDDD', lw=0.5, zorder=1)

# 孔位
for j in range(N):
    for i in range(N):
        x = X0 + i * P
        y = Y0 + j * P
        ax.add_patch(Circle((x, y), 1.6, fill=False, lw=1.0, ec='#111111'))
        ax.plot([x - 4, x + 4], [y, y], color='#111111', lw=0.6)
        ax.plot([x, x], [y - 4, y + 4], color='#111111', lw=0.6)

# 行列编号
for i in range(N):
    ax.text(X0 + i * P, Y0 - 9, f'x={i}', ha='center', va='center', fontsize=8.5)
for j in range(N):
    ax.text(X0 - 11, Y0 + j * P, f'y={j}', ha='right', va='center', fontsize=8.5)

# 原点标记
ax.annotate('原点 (0,0)', xy=(X0 - 3, Y0 - 3), xytext=(X0 - 8, Y0 - 22),
            fontsize=8, color='#B03A2E',
            arrowprops=dict(arrowstyle='->', color='#B03A2E', lw=0.8))
ax.plot([X0], [Y0], marker='o', ms=3, color='#B03A2E')

# 外形轮廓
ax.add_patch(plt.Rectangle((X0 - 3, Y0 - 3), SPAN + 6, SPAN + 6,
                           fill=False, lw=0.8, ec='#666666', ls='--'))

# 50 mm 标尺
sx, sy = 105, 45
ax.plot([sx, sx + 50], [sy, sy], color='#111111', lw=1.2)
for k in range(0, 51, 10):
    ax.plot([sx + k, sx + k], [sy - 1.5, sy + 1.5], color='#111111', lw=0.9)
ax.text(sx + 25, sy + 4, '50 mm 标尺（打印后量一下，必须是 50 mm）',
        ha='center', va='bottom', fontsize=8.5)

# 尺寸标注
ax.annotate('', xy=(X0, Y0 + SPAN + 14), xytext=(X0 + SPAN, Y0 + SPAN + 14),
            arrowprops=dict(arrowstyle='<|-|>', color='#555555', lw=0.8, mutation_scale=7))
ax.text(X0 + SPAN / 2, Y0 + SPAN + 16, '100 mm', ha='center', va='bottom', fontsize=8.5)

ax.annotate('', xy=(X0 - 22, Y0), xytext=(X0 - 22, Y0 + P),
            arrowprops=dict(arrowstyle='<|-|>', color='#555555', lw=0.8, mutation_scale=7))
ax.text(X0 - 24, Y0 + P / 2, '20', ha='right', va='center', fontsize=8.5, rotation=90)

fig.savefig('../docs/夹具图纸_A4_1比1.pdf', format='pdf')
fig.savefig('../docs/夹具图纸预览.png', dpi=170, facecolor='white')
print('saved')
