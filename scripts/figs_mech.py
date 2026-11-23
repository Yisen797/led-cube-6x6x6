# -*- coding: utf-8 -*-
"""图2 单层俯视接线、图4 刷新时序、图5 层叠侧视"""
import matplotlib
matplotlib.use('Agg')
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
matplotlib.rcParams['axes.unicode_minus'] = False

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, FancyArrowPatch, FancyBboxPatch

OUT = '../docs/'

# =====================================================================
# 图2  单层 6×6 俯视接线图
# =====================================================================
NN = 6
SPAN = (NN - 1) * 20          # 100 mm
fig, ax = plt.subplots(figsize=(8.6, 8.6))
p = 20.0
xs = [i * p for i in range(NN)]
ys = [j * p for j in range(NN)]
R = 2.2
XR = SPAN + 10                # 右侧母线端点
XL = -10

# LED 本体
for y in ys:
    for x in xs:
        ax.add_patch(Circle((x, y), R, fc='#DCEBFF', ec='#2A78D6', lw=1.1, zorder=3))

# 阳极横排母线（沿行，LED 之间分段）
for y in ys:
    ax.plot([XL, -R], [y, y], color='#C0392B', lw=2.2, zorder=2, solid_capstyle='round')
    for a, b in zip(xs[:-1], xs[1:]):
        ax.plot([a + R, b - R], [y, y], color='#C0392B', lw=2.2, zorder=2,
                solid_capstyle='round')
    ax.plot([xs[-1] + R, XR], [y, y], color='#C0392B', lw=2.2, zorder=2,
            solid_capstyle='round')

# 跨接线：把 6 条母线连成一个阳极层
for xj in (XL, XR):
    ax.plot([xj, xj], [0, SPAN], color='#1F7A3F', lw=2.0, zorder=1, solid_capstyle='round')
    for y in ys:
        ax.add_patch(Circle((xj, y), 1.1, fc='#1F7A3F', ec='none', zorder=4))

# 阴极：竖直向下（穿出本层，焊到下层同位置）
for y in ys:
    for x in xs:
        ax.annotate('', xy=(x, y - 6.6), xytext=(x, y - R),
                    arrowprops=dict(arrowstyle='-|>', color='#5B4BA8', lw=1.0,
                                    shrinkA=0, shrinkB=0, mutation_scale=8),
                    zorder=5)

# 尺寸标注
def hdim(y, x0, x1, text, off=0.0):
    ax.annotate('', xy=(x1, y), xytext=(x0, y),
                arrowprops=dict(arrowstyle='<|-|>', color='#555555', lw=0.9,
                                shrinkA=0, shrinkB=0, mutation_scale=8))
    ax.plot([x0, x0], [y - 1.8, y + 1.8], color='#555555', lw=0.7)
    ax.plot([x1, x1], [y - 1.8, y + 1.8], color='#555555', lw=0.7)
    ax.text((x0 + x1) / 2, y + 2.4 + off, text, ha='center', va='bottom',
            fontsize=9, color='#333333')

hdim(-12, 0, 20, '20 mm')
hdim(-21, 0, SPAN, '6 × 20 = 100 mm')

# 行列编号
for i, x in enumerate(xs):
    ax.text(x, -30, f'x={i}', ha='center', va='top', fontsize=8.5, color='#2A78D6')
for j, y in enumerate(ys):
    ax.text(-22, y, f'y={j}', ha='right', va='center', fontsize=8.5, color='#2A78D6')

# 编号标记
def badge(x, y, s):
    ax.add_patch(Circle((x, y), 3.6, fc='white', ec='#C99A2E', lw=1.2, zorder=8))
    ax.text(x, y, s, ha='center', va='center', fontsize=9, color='#8A6210', zorder=9)

badge(XL, SPAN + 10, '②')
badge(SPAN / 2, SPAN + 5, '①')
badge(30, -8.5, '③')

ax.set_xlim(-30, XR + 22)
ax.set_ylim(-48, SPAN + 18)
ax.set_aspect('equal')
ax.axis('off')

ax.text(SPAN / 2, SPAN + 14, '单层（6 × 6）俯视接线图', ha='center', va='bottom',
        fontsize=14, fontweight='bold')

ax.text(-28, -40,
        '① 红色：阳极引线弯折后沿行互焊，每层形成 6 条横排母线\n'
        '② 绿色：左右各一根跨接线把 6 条母线连成一个整体 = 该层阳极\n'
        '③ 紫色：阴极引线保持竖直向下，穿过下一层阳极平面，焊到下层同位置阴极上',
        ha='left', va='top', fontsize=9.5, color='#222222', linespacing=1.5)

fig.savefig(OUT + 'fig2_单层接线.png', dpi=200, bbox_inches='tight', facecolor='white')
fig.savefig(OUT + 'fig2_单层接线.svg', bbox_inches='tight', facecolor='white')
plt.close(fig)

# =====================================================================
# 图4  刷新时序
# =====================================================================
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 5.2),
                               gridspec_kw={'height_ratios': [0.75, 1.5]})
fig.subplots_adjust(left=0.10, right=0.97, top=0.92, bottom=0.12, hspace=0.45)

slot = 0.825
for z in range(6):
    ax1.add_patch(Rectangle((z * slot, 0), slot, 1,
                            fc='#4A90D9' if z % 2 == 0 else '#8FC0EA',
                            ec='white', lw=1.5))
    ax1.text(z * slot + slot / 2, 0.5, f'L{z}', ha='center', va='center',
             color='white' if z % 2 == 0 else '#12466E', fontsize=11, fontweight='bold')
ax1.set_xlim(0, 4.95)
ax1.set_ylim(-0.6, 1.9)
ax1.set_yticks([])
ax1.set_xticks([0, 0.825, 1.65, 2.475, 4.95])
ax1.set_xticklabels(['0', '0.825', '1.65', '2.475', '4.95 ms'])
ax1.set_xlabel('时间', fontsize=9)
for s in ('top', 'right', 'left'):
    ax1.spines[s].set_visible(False)
ax1.annotate('', xy=(0, 1.35), xytext=(4.95, 1.35),
             arrowprops=dict(arrowstyle='<|-|>', color='#888', lw=1))
ax1.text(2.475, 1.45, '一帧 4.95 ms → 202 Hz；每层只亮 0.825 ms（占空比 1/6）',
         ha='center', va='bottom', fontsize=10)

# 单槽放大：4 位 BCM 子场
ax2.set_xlim(0, 15.6)
ax2.set_ylim(-1.5, 4.2)
ax2.set_xlabel('一个层时隙 = 15 份 × 55 µs ≈ 825 µs   （横轴单位：份）', fontsize=9)
ax2.set_yticks([2.85, 1.85])
ax2.set_yticklabels(['子场宽度', '重发 56 bit'], fontsize=9)
for s in ('top', 'right', 'left'):
    ax2.spines[s].set_visible(False)
ax2.set_xticks([0, 1, 3, 7, 15])
ax2.set_xticklabels(['0', '1', '3', '7', '15 份'])

fields = [(3, 8, '#1F5FA8'), (2, 4, '#3C7FC4'), (1, 2, '#6FA8DC'), (0, 1, '#A8C8E8')]
s = 0
for bit, w, col in fields:
    ax2.add_patch(Rectangle((s, 2.40), w, 0.9, fc=col, ec='white', lw=1.5))
    # 宽度小的子场标签放到上方，避免压字
    if w >= 2:
        ax2.text(s + w / 2, 2.85, f'位{bit} · {w}/15', ha='center', va='center',
                 color='white' if w >= 4 else '#12466E', fontsize=9.5, fontweight='bold')
    else:
        ax2.text(s + w / 2, 3.45, f'位{bit} · {w}/15', ha='center', va='bottom',
                 color='#12466E', fontsize=9)
    # 该子场开始前重发一次 72 bit
    ax2.add_patch(Rectangle((s, 1.40), 0.30, 0.5, fc='none', ec='#C0392B',
                            hatch='||||', lw=0.9))
    s += w
ax2.text(7.8, 1.12, '每个子场开始前重发 56 bit（≈8 µs，已从保持时间扣除）',
         ha='center', va='center', fontsize=9, color='#C0392B')

ax2.annotate('', xy=(0, 0.50), xytext=(15, 0.50),
             arrowprops=dict(arrowstyle='<|-|>', color='#888', lw=1))
ax2.text(7.5, 0.25, '一块 0.825 ms 时隙内，同一层的 36 只灯被点亮 8/15、4/15、2/15、1/15 时间',
         ha='center', va='top', fontsize=9, color='#555')
ax2.text(7.5, -0.55, '像素亮度 = 该像素「位为 1」的子场时间之和 → 0 ~ 15 级',
         ha='center', va='top', fontsize=10, color='#1F5FA8', fontweight='bold')

fig.suptitle('6 层扫描 + 4 位灰度时序（逐层点亮 · 每层内再分 4 个子场）',
             fontsize=13, fontweight='bold')
fig.savefig(OUT + 'fig4_刷新时序.png', dpi=200, facecolor='white')
fig.savefig(OUT + 'fig4_刷新时序.svg', facecolor='white')
plt.close(fig)

# =====================================================================
# 图5  层叠侧视（斜投影）
# =====================================================================
fig, ax = plt.subplots(figsize=(9.0, 7.6))

KY = 1.9   # y 方向投影系数（放大，让阳极/阴极引线在图上分得开）


def prj(x, y, z):
    return x + KY * y, z + 0.30 * y


def led(x, y, z, lw=1.0):
    """画一只 LED：本体 + 阳极（沿 x 弯折）+ 阴极（竖直向下 25mm）"""
    cx, cy = prj(x, y, z)
    # 本体
    ax.add_patch(FancyBboxPatch((cx - 1.5, cy), 3.0, 5.0,
                                boxstyle='round,pad=0.2,rounding_size=0.6',
                                fc='#DCEBFF', ec='#2A78D6', lw=1.1, zorder=4))
    # 阳极：本体底部沿 +x 伸出（y 偏 -1.27）
    ax_ = prj(x, y - 1.27, z)
    ax.plot([ax_[0], ax_[0] + 9.5], [ax_[1], ax_[1]], color='#C0392B', lw=1.6, zorder=5)
    # 阴极：竖直向下 25mm（y 偏 +1.27）
    kx, ky = prj(x, y + 1.27, z)
    ax.plot([kx, kx], [ky, ky - 25], color='#5B4BA8', lw=1.6, zorder=6)


for z in (0, 20, 40):
    for x in (0, 20):
        led(x, 0, z)
    # 该层阳极母线穿过两只 LED
    a0 = prj(0, -1.27, z)
    a1 = prj(20, -1.27, z)
    ax.plot([a0[0], a1[0]], [a0[1], a1[1]], color='#C0392B', lw=1.6, zorder=5)

# 叠焊区高亮（z=20 的阴极与 z=0 的阴极重叠 5mm）
kx, ky = prj(0, 1.27, 20)
ax.plot([kx, kx], [ky - 20, ky - 25], color='#E67E22', lw=3.2, zorder=7,
        solid_capstyle='round')

# 层间距标注
for z in (0, 20, 40):
    ax.plot([-17.5, -14.5], [z, z], color='#777', lw=0.8)
ax.annotate('', xy=(-16, 20), xytext=(-16, 0),
            arrowprops=dict(arrowstyle='<|-|>', color='#555', lw=0.9, mutation_scale=8))
ax.annotate('', xy=(-16, 40), xytext=(-16, 20),
            arrowprops=dict(arrowstyle='<|-|>', color='#555', lw=0.9, mutation_scale=8))
ax.text(-18, 10, '20 mm', ha='right', va='center', fontsize=9)
ax.text(-18, 30, '20 mm', ha='right', va='center', fontsize=9)

ax.annotate('阳极引线沿行弯折，\n同层互焊成母线（接层电源）',
            xy=(10, 19.6), xytext=(32, 32), fontsize=9,
            arrowprops=dict(arrowstyle='->', color='#C0392B', lw=1.0))
ax.annotate('阴极引线竖直向下 25 mm，\n与下层同位置阴极叠焊 5 mm\n→ 形成贯穿 6 层的列线',
            xy=(2.6, 8.0), xytext=(34, 6.0), fontsize=9,
            arrowprops=dict(arrowstyle='->', color='#5B4BA8', lw=1.0))
ax.annotate('叠焊区 5 mm', xy=(2.6, -2.5), xytext=(15, -12), fontsize=9, color='#E67E22',
            arrowprops=dict(arrowstyle='->', color='#E67E22', lw=1.0))

ax.set_xlim(-26, 92)
ax.set_ylim(-30, 52)
ax.set_aspect('equal')
ax.axis('off')
ax.text(30, 48, '层叠与引线弯折（斜投影，只画 2 列 × 3 层）',
        ha='center', va='bottom', fontsize=13, fontweight='bold')
ax.text(-24, -25, '注：图中只示意引线走向；实际 6 层 × 6 × 6 = 216 只，层间距 20 mm，总高约 100 mm。',
        ha='left', va='top', fontsize=9, color='#444')

fig.savefig(OUT + 'fig5_层叠结构.png', dpi=200, bbox_inches='tight', facecolor='white')
fig.savefig(OUT + 'fig5_层叠结构.svg', bbox_inches='tight', facecolor='white')
plt.close(fig)

print('done')
