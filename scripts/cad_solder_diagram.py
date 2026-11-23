# -*- coding: utf-8 -*-
"""出两张焊接工艺图（2D）：
   docs/cad/图_单行剖面.png    —— 一行灯 + 夹具板 + 阳极母线的侧视剖面（带尺寸标注）
   docs/cad/图_四个步骤.png    —— 插灯 → 掰阳极 → 焊母线 → 叠层 四步示意
"""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyArrowPatch

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'docs', 'cad')
os.makedirs(OUT, exist_ok=True)

C_BODY = '#3b6fd4'
C_FLANGE = '#8fa3bd'
C_ANODE = '#d98620'
C_CATHODE = '#9aa0a6'
C_BUS = '#e0a92e'
C_PLATE = '#c8b28a'
C_TEXT = '#222'
LW = 1.8


def draw_led(ax, x, y0, bend=True, bend_len=21.5, cathode_len=22.0, lw=LW, body=True):
    """侧视一只灯。y0 = 板面（法兰底面）。bend=False 时阳极不弯。"""
    # 实际两脚沿 y 分开（阳极 −y / 阴极 +y）；侧视时把它们在图上错开 1.8mm 以便看清
    xa, xk = x - 0.9, x + 0.9
    if body:
        ax.add_patch(Rectangle((x - 2.0, y0), 4.0, 0.5, facecolor=C_FLANGE,
                               edgecolor='#5c6b7a', lw=0.7, zorder=4))
        ax.add_patch(Rectangle((x - 1.5, y0 + 0.5), 3.0, 5.0, facecolor=C_BODY,
                               edgecolor='#2b4f9e', lw=0.7, alpha=0.9, zorder=4))
    # 阳极（长脚）
    ax.plot([xa, xa], [y0, y0 - 2.0], color=C_ANODE, lw=lw, solid_capstyle='round', zorder=5)
    if bend:
        ax.plot([xa, xa + bend_len], [y0 - 2.0, y0 - 2.0], color=C_ANODE, lw=lw,
                solid_capstyle='round', zorder=5)
    # 阴极（短脚）
    ax.plot([xk, xk], [y0, y0 - cathode_len], color=C_CATHODE, lw=lw,
            solid_capstyle='round', zorder=3)


def fig_top():
    """俯视图：两脚沿 y 错开、阳极沿 x 弯折、跨接线走在两列之间。"""
    fig, ax = plt.subplots(figsize=(9.5, 9.5), dpi=150)
    ax.set_aspect('equal')
    xs = [0, 20, 40, 60, 80, 100]
    ys = [0, 20, 40, 60, 80, 100]
    # 阳极弯折线（沿 x，位于 y-1.27）
    for y in ys:
        ax.plot([-1.27, 100 - 1.27 + 18], [y - 1.27, y - 1.27], color=C_ANODE, lw=1.6, zorder=2, alpha=0.85)
    # 跨接线（沿 y，在两列之间）
    for xc in (10, 90):
        ax.plot([xc, xc], [-12, 112], color='#2e8b57', lw=2.4, zorder=3)
    for y in ys:
        for x in xs:
            ax.add_patch(Circle((x, y), 2.0, facecolor='none', edgecolor='#2b4f9e', lw=1.2, zorder=4))
            ax.add_patch(Circle((x, y - 1.27), 0.55, facecolor=C_ANODE, edgecolor='none', zorder=5))
            ax.add_patch(Circle((x, y + 1.27), 0.55, facecolor='#777', edgecolor='none', zorder=5))
    ax.annotate('阳极（长脚）统一朝 −y', xy=(40, 40 - 1.27), xytext=(-4, 72),
                fontsize=10, color=C_ANODE, arrowprops=dict(arrowstyle='->', color=C_ANODE, lw=1.0))
    ax.annotate('阴极（短脚）朝 +y，竖直向下', xy=(40, 40 + 1.27), xytext=(52, 62),
                fontsize=10, color='#555', arrowprops=dict(arrowstyle='->', color='#777', lw=1.0))
    ax.annotate('阳极弯折方向 +x（每根接到隔壁灯的阳极脚）', xy=(60, 20 - 1.27), xytext=(8, -16),
                fontsize=10, color=C_ANODE, arrowprops=dict(arrowstyle='->', color=C_ANODE, lw=1.0))
    ax.annotate('跨接线沿 y 走两列灯之间（x=10 / 90）', xy=(90, 66), xytext=(40, 108),
                fontsize=10, color='#2e8b57', arrowprops=dict(arrowstyle='->', color='#2e8b57', lw=1.0))
    ax.set_xlim(-16, 116)
    ax.set_ylim(-24, 118)
    ax.axis('off')
    ax.set_title('俯视图（从立方体上方看）：两脚沿 y 错开 2.54 mm', fontsize=13)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, '图_俯视接线.png'), bbox_inches='tight')
    plt.close(fig)


def fig_section():
    fig, ax = plt.subplots(figsize=(12.5, 6.6), dpi=150)
    ax.set_aspect('equal')
    centers = (30.0, 50.0)
    # 夹具板（2mm），每只灯一个 Ø3.8 的孔（两脚都在孔里）
    segs, prev = [], -30.0
    for c in centers:
        segs.append((prev, c - 1.9))
        prev = c + 1.9
    segs.append((prev, 92.0))
    for x0, x1 in segs:
        ax.add_patch(Rectangle((x0, -2.0), x1 - x0, 2.0, facecolor=C_PLATE,
                               edgecolor='#8a7550', lw=0.8, zorder=2))
    for c in centers:
        draw_led(ax, c, 0.0)
    # 阳极弯脚：每根弯 21.5 mm，够到隔壁灯阳极脚并搭焊
    for c in centers:
        xa = c - 0.9
        ax.plot([xa, xa + 21.5], [-2.0, -2.0], color=C_BUS, lw=2.6, zorder=6, solid_capstyle='round')
    for c in centers[:-1]:
        ax.add_patch(Circle((c + 20 - 0.9, -2.0), 1.1, facecolor=C_BUS,
                            edgecolor='#8a6a10', lw=0.8, zorder=7))

    def note(xy, xytext, s, color=C_TEXT, ha='left'):
        ax.annotate(s, xy=xy, xytext=xytext, fontsize=9.5, color=color, ha=ha,
                    arrowprops=dict(arrowstyle='->', color='#777', lw=1.0,
                                    shrinkA=2, shrinkB=2), zorder=10)

    note((30.0, 4.6), (2, 11), '灯体 Ø3 × 5')
    note((51.9, 0.3), (60, 9), '法兰 Ø4：卡在板面')
    note((14, -1.0), (-29, 4), '夹具板 2 mm，孔 Ø3.8')
    note((45, -2.0), (33, 7.5), '阳极（长脚）：板下弯 90°，指向 +x（隔壁灯）')
    note((28.73, -15), (6, -20), '阴极（短脚）：竖直向下贯通')
    note((58, -2.0), (58, -9), '阳极脚弯 21.5 mm，与隔壁灯阳极脚搭焊')

    ax.annotate('', xy=(30, -26), xytext=(50, -26),
                arrowprops=dict(arrowstyle='<->', color='#444', lw=1.0))
    ax.text(40, -25, '20 mm', ha='center', va='bottom', fontsize=10, color='#444')
    ax.annotate('', xy=(29.1, -4.2), xytext=(49.1, -4.2),
                arrowprops=dict(arrowstyle='<->', color=C_ANODE, lw=1.0))
    ax.text(40, -5.2, '弯折 21.5 mm（20 + 1.5 搭接）', ha='center', va='top', fontsize=9, color=C_ANODE)

    ax.set_xlim(-32, 98)
    ax.set_ylim(-28, 14)
    ax.axis('off')
    ax.set_title('单行剖面：灯体在上、灯脚在板下（从侧面看）', fontsize=13, color=C_TEXT)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, '图_单行剖面.png'), bbox_inches='tight')
    plt.close(fig)


def fig_steps():
    fig, axes = plt.subplots(1, 4, figsize=(17, 4.8), dpi=150)
    titles = ['① 插灯', '② 阳极掰 90°', '③ 焊阳极母线', '④ 叠层焊阴极']
    subs = ['灯体朝上，灯脚全部穿到板下\n（夹具架空，从下往上焊）',
            '长脚（阳极）沿 +x 掰 90°\n贴板底；两脚沿 y 错开不交叉',
            '弯脚末端与隔壁灯阳极脚搭焊\n一行成母线；再沿 y 拉跨接线',
            '起层、垫 20 mm；上层阴极\n与下层阴极焊成一列']
    for i, (ax, title, sub) in enumerate(zip(axes, titles, subs)):
        ax.set_aspect('equal')
        ax.set_xlim(-14, 38)
        ax.set_ylim(-40, 13)
        ax.axis('off')
        ax.set_title(title, fontsize=12, pad=8)
        ax.text(12, -39, sub, ha='center', va='bottom', fontsize=8.8, color='#444')
        if i < 3:   # 第 4 格是叠层，不画夹具板
            ax.add_patch(Rectangle((-12, -2), 44, 2, facecolor=C_PLATE,
                                   edgecolor='#8a7550', lw=0.8, zorder=1))

    xs = (2, 10, 18, 26)
    # ① 插灯（不弯）
    for x in xs:
        draw_led(axes[0], x, 0.0, bend=False, lw=1.4)
    # ② 掰阳极
    for x in xs:
        draw_led(axes[1], x, 0.0, bend=True, bend_len=9.5, lw=1.4)
    axes[1].add_patch(FancyArrowPatch((4.27, 2.2), (7.6, 2.2), arrowstyle='-|>',
                                      mutation_scale=14, color='#b3261e', lw=1.6))
    axes[1].text(4.8, 3.2, '掰 90°', fontsize=9, color='#b3261e')
    # ③ 焊母线
    for x in xs:
        draw_led(axes[2], x, 0.0, bend=True, bend_len=9.5, lw=1.4)
    for x in xs[:-1]:   # 与隔壁灯阳极脚搭焊的点
        axes[2].add_patch(Circle((x + 8 - 0.9, -2), 1.0, facecolor=C_BUS,
                                 edgecolor='#8a6a10', lw=0.7, zorder=7))
    # ④ 两层叠起来（去掉夹具板，只看灯和阴极）
    for dz, cl in ((0.0, 21.0), (-20.0, 11.0)):
        for x in (6, 16):
            draw_led(axes[3], x, dz, bend=False, cathode_len=cl, lw=1.3)
    for x in (5.9, 15.9):
        axes[3].add_patch(Circle((x, -21.5), 1.1, facecolor='#e8e8e8',
                                 edgecolor='#777', lw=0.8, zorder=6))
    axes[3].annotate('', xy=(30, 0), xytext=(30, -22),
                     arrowprops=dict(arrowstyle='<->', color='#444', lw=1.0))
    axes[3].text(31, -11, '20 mm', fontsize=9, color='#444', va='center', rotation=90)

    fig.suptitle('6×6×6 光立方：一层灯的焊接顺序', fontsize=14, y=1.03)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, '图_四个步骤.png'), bbox_inches='tight')
    plt.close(fig)



# ---------------- 2D DXF（AutoCAD 俯视装配图） ----------------
CRLF = chr(13) + chr(10)


def write_topview_dxf(path):
    """单层俯视装配图：LED 圆、阳极弯折线、跨接线、坐标标注。"""
    out = []

    def L(*xs):
        out.extend(str(x) for x in xs)

    def line(layer, x1, y1, x2, y2):
        L('0', 'LINE', '8', layer, '10', '%.3f' % x1, '20', '%.3f' % y1, '30', '0',
          '11', '%.3f' % x2, '21', '%.3f' % y2, '31', '0')

    def circle(layer, x, y, r):
        L('0', 'CIRCLE', '8', layer, '10', '%.3f' % x, '20', '%.3f' % y, '30', '0',
          '40', '%.3f' % r)

    def text(layer, x, y, h, s, rot=0):
        L('0', 'TEXT', '8', layer, '10', '%.3f' % x, '20', '%.3f' % y, '30', '0',
          '40', '%.3f' % h, '1', s, '50', '%.1f' % rot)

    layers = [('LED', 5), ('ANODE', 1), ('CATHODE', 8), ('BUS', 2), ('NOTE', 7)]
    L('0', 'SECTION', '2', 'HEADER', '9', '$ACADVER', '1', 'AC1009', '0', 'ENDSEC')
    L('0', 'SECTION', '2', 'TABLES', '0', 'TABLE', '2', 'LAYER', '70', len(layers))
    for name, color in layers:
        L('0', 'LAYER', '2', name, '70', 0, '62', color, '6', 'CONTINUOUS')
    L('0', 'ENDTAB', '0', 'ENDSEC')
    L('0', 'SECTION', '2', 'ENTITIES')

    xs = [i * 20 for i in range(6)]
    for y in xs:
        # 阳极弯折线（沿 x，位于 y-1.27）
        for x in xs:
            line('ANODE', x - 1.27, y - 1.27, x - 1.27 + 21.5, y - 1.27)
    for xc in (10, 90):                       # 纵向跨接线
        line('BUS', xc, -12, xc, 112)
    for y in xs:
        for x in xs:
            circle('LED', x, y, 2.0)          # 法兰 Ø4
            circle('ANODE', x, y - 1.27, 0.25)
            circle('CATHODE', x, y + 1.27, 0.25)
        text('NOTE', -14, y, 3.5, 'y=%d' % (y // 20))
    for x in xs:
        text('NOTE', x - 2, -18, 3.5, 'x=%d' % (x // 20))
    text('NOTE', -14, 112, 4.0, '6x6 LED CUBE LAYER - TOP VIEW  (unit mm)')
    text('NOTE', -14, 106, 3.0, 'RED = anode lead bent +x ; GREY dot = cathode (down) ; YELLOW = cross wire')
    text('NOTE', -14, -26, 3.0, 'PITCH 20mm ; ANODE BEND 21.5mm ; TWO LEADS OFFSET 2.54mm IN Y')
    L('0', 'ENDSEC', '0', 'EOF')
    with open(path, 'w', encoding='ascii', newline='') as fh:
        fh.write(CRLF.join(out) + CRLF)
    return len(out)


if __name__ == '__main__':
    fig_top()
    fig_section()
    fig_steps()
    print('dxf2d', write_topview_dxf(os.path.join(OUT, 'layer_6x6_俯视.dxf')))
    print('ok')
