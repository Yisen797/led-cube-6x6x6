# -*- coding: utf-8 -*-
"""生成 6×6×6 光立方的 CAD 模型（STL）+ 焊接示意图（PNG）。

尺寸全部来自 02_制作步骤.md / 01_原理与接口.md：
  LED 3mm 蓝光：灯体 Ø3.0×5.0，法兰 Ø4.0×0.5，脚 Ø0.5
  层内间距 20 mm，层距 20 mm，共 6 层
  夹具板 150×150×2，36 孔 Ø3.0
  阳极（长脚）在板下向右弯 90° 焊成母线；阴极（短脚）竖直向下
输出：
  docs/cad/layer_6x6.stl      单层（含夹具框、阳极母线）
  docs/cad/cube_6x6x6.stl     整体六层
  docs/cad/图_单层焊接.png
  docs/cad/图_整体装配.png
"""
import os
import struct
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'docs', 'cad')
os.makedirs(OUT, exist_ok=True)

# ---------------- 尺寸（mm） ----------------
PITCH = 20.0          # 层内/列间距
N = 6                 # 6×6×6
LAYER_GAP = 20.0      # 层距
BODY_D, BODY_H = 3.0, 5.0
FLANGE_D, FLANGE_H = 4.0, 0.5
LEAD_D = 0.5
PLATE_T = 2.0
ANODE_BEND = 21.5     # 阳极弯折长度（沿 +x，够到隔壁灯阳极脚并搭接 1.5）
CATHODE_LEN = 22.0    # 阴极竖直段长（略长于层距，留焊接搭接）
BOTTOM_EXTRA = 25.0   # 最底层阴极再往下伸到驱动板

SEG = 14              # 圆柱分段

tris = []             # [(v0,v1,v2, material), ...]
MATS = {}


def add(tri, mat):
    tris.append((tri[0], tri[1], tri[2], mat))


def cyl(p0, p1, r, mat, seg=None, caps=True):
    if seg is None:
        seg = SEG
    p0 = np.asarray(p0, float)
    p1 = np.asarray(p1, float)
    axis = p1 - p0
    L = np.linalg.norm(axis)
    if L < 1e-9:
        return
    z = axis / L
    tmp = np.array([0, 0, 1.0]) if abs(z[2]) < 0.9 else np.array([1.0, 0, 0])
    u = np.cross(z, tmp)
    u /= np.linalg.norm(u)
    v = np.cross(z, u)
    ring0, ring1 = [], []
    for i in range(seg):
        a = 2 * np.pi * i / seg
        d = np.cos(a) * u + np.sin(a) * v
        ring0.append(p0 + r * d)
        ring1.append(p1 + r * d)
    for i in range(seg):
        j = (i + 1) % seg
        add((ring0[i], ring0[j], ring1[j]), mat)
        add((ring0[i], ring1[j], ring1[i]), mat)
    if caps:
        c0, c1 = p0, p1
        for i in range(seg):
            j = (i + 1) % seg
            add((c0, ring0[j], ring0[i]), mat)
            add((c1, ring1[i], ring1[j]), mat)


def box(x0, y0, z0, x1, y1, z1, mat):
    p = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    faces = [(0, 1, 2), (0, 2, 3), (4, 6, 5), (4, 7, 6), (0, 4, 5), (0, 5, 1),
             (1, 5, 6), (1, 6, 2), (2, 6, 7), (2, 7, 3), (3, 7, 4), (3, 4, 0)]
    for f in faces:
        add((p[f[0]], p[f[1]], p[f[2]]), mat)


LEAD_PITCH = 2.54      # 3mm LED 两脚间距


def led(cx, cy, z0, anode_dir=+1, cathode_len=CATHODE_LEN):
    """一只灯：灯体在 z0 以上，法兰贴板面。

    两脚沿 **y** 方向分开（阳极 −y、阴极 +y，间距 2.54），阳极沿 **x** 弯折。
    这样弯折后的阳极母线走在 y=cy−1.27 的线上，永远不会碰到 y=cy+1.27 的阴极。
    """
    xa, ya = cx, cy - LEAD_PITCH / 2
    xk, yk = cx, cy + LEAD_PITCH / 2
    # 法兰 + 灯体
    cyl((cx, cy, z0), (cx, cy, z0 + FLANGE_H), FLANGE_D / 2, 'flange')
    cyl((cx, cy, z0 + FLANGE_H), (cx, cy, z0 + FLANGE_H + BODY_H), BODY_D / 2, 'body')
    # 阳极：竖直穿过板，再沿 x 弯折平贴在板下
    zb = z0 - PLATE_T
    cyl((xa, ya, z0), (xa, ya, zb), LEAD_D / 2, 'anode')
    cyl((xa, ya, zb), (xa + anode_dir * ANODE_BEND, ya, zb), LEAD_D / 2, 'anode')
    # 阴极：竖直向下
    cyl((xk, yk, z0), (xk, yk, z0 - cathode_len), LEAD_D / 2, 'cathode')


def jig_frame(z_top):
    """夹具板画成外框，方便看清板下焊点。"""
    half, t = PITCH * N / 2 + 15, PLATE_T
    w = 18
    z1 = z_top
    z0 = z_top - t
    box(-half, -half, z0, half, -half + w, z1, 'jig')
    box(-half, half - w, z0, half, half, z1, 'jig')
    box(-half, -half + w, z0, -half + w, half - w, z1, 'jig')
    box(half - w, -half + w, z0, half, half - w, z1, 'jig')


def build_layer(z0=0.0, bus=True):
    """单层 6×6，返回层内每个 (x,y) 的世界坐标。"""
    half = PITCH * (N - 1) / 2
    pos = {}
    for iy in range(N):
        y = -half + iy * PITCH
        for ix in range(N):
            x = -half + ix * PITCH
            led(x, y, z0, +1, CATHODE_LEN)
            pos[(ix, iy)] = (x, y)
    if bus:
        # 跨接线：沿 y 走两根，位置在两列灯之间（x = 10 和 90），把 6 条横排母线连成一层
        for xc in (-half + 10.0, -half + 90.0):
            cyl((xc, -half - 1.0, z0 - PLATE_T), (xc, half + 1.0, z0 - PLATE_T), 0.35, 'bus')
    return pos


def build_cube():
    """六层，每层 z = k*LAYER_GAP。"""
    half = PITCH * (N - 1) / 2
    for k in range(N):
        z = k * LAYER_GAP
        for iy in range(N):
            y = -half + iy * PITCH
            for ix in range(N):
                x = -half + ix * PITCH
                btn = (k == 0)
                led(x, y, z, +1, CATHODE_LEN + (BOTTOM_EXTRA if btn else 0))
        for xc in (-half + 10.0, -half + 90.0):
            cyl((xc, -half - 1.0, z - PLATE_T), (xc, half + 1.0, z - PLATE_T), 0.35, 'bus')



# ---------------- DXF（AutoCAD 可直接打开，3DFACE 曲面） ----------------
DXF_LAYERS = {
    'body':    ('LED_BODY', 5),     # 蓝
    'flange':  ('LED_FLANGE', 4),   # 青
    'anode':   ('ANODE', 1),        # 红
    'cathode': ('CATHODE', 8),      # 深灰
    'bus':     ('BUS', 2),          # 黄
    'jig':     ('JIG', 3),          # 绿
}


CRLF = chr(13) + chr(10)


def write_dxf(path):
    """导出 R12 ASCII DXF，用 3DFACE 表示三角面，按材料分图层着色。"""
    out = []

    def L(*xs):
        out.extend(str(x) for x in xs)

    f = lambda v: '%.4f' % v
    L('0', 'SECTION', '2', 'HEADER', '9', '$ACADVER', '1', 'AC1009', '0', 'ENDSEC')
    L('0', 'SECTION', '2', 'TABLES')
    L('0', 'TABLE', '2', 'LAYER', '70', len(DXF_LAYERS))
    for name, color in DXF_LAYERS.values():
        L('0', 'LAYER', '2', name, '70', 0, '62', color, '6', 'CONTINUOUS')
    L('0', 'ENDTAB', '0', 'ENDSEC')
    L('0', 'SECTION', '2', 'ENTITIES')
    for a, b, c, m in tris:
        name = DXF_LAYERS.get(m, ('LED_BODY', 7))[0]
        L('0', '3DFACE', '8', name,
          '10', f(a[0]), '20', f(a[1]), '30', f(a[2]),
          '11', f(b[0]), '21', f(b[1]), '31', f(b[2]),
          '12', f(c[0]), '22', f(c[1]), '32', f(c[2]),
          '13', f(c[0]), '23', f(c[1]), '33', f(c[2]))
    L('0', 'ENDSEC', '0', 'EOF')
    with open(path, 'w', encoding='ascii', newline='') as fh:
        fh.write(CRLF.join(out) + CRLF)
    return len(tris)


# ---------------- STL ----------------
def write_stl(path):
    normals = []
    face_list = []
    for a, b, c, _ in tris:
        n = np.cross(np.subtract(b, a), np.subtract(c, a))
        ln = np.linalg.norm(n)
        n = n / ln if ln > 1e-12 else np.array([0, 0, 0.0])
        normals.append(n)
        face_list.append((a, b, c))
    with open(path, 'wb') as f:
        f.write(b'\0' * 80)
        f.write(struct.pack('<I', len(face_list)))
        for n, (a, b, c) in zip(normals, face_list):
            f.write(struct.pack('<3f', *n))
            for p in (a, b, c):
                f.write(struct.pack('<3f', *p))
            f.write(struct.pack('<H', 0))
    return len(face_list)


COLORS = {
    'body':   (0.15, 0.35, 0.95, 0.55),
    'flange': (0.55, 0.62, 0.72, 1.0),
    'anode':  (0.85, 0.55, 0.15, 1.0),
    'cathode': (0.72, 0.72, 0.78, 1.0),
    'bus':    (0.95, 0.72, 0.25, 1.0),
    'jig':    (0.55, 0.45, 0.35, 0.35),
}


def render(path, elev, azim, title, subtitle=''):
    fig = plt.figure(figsize=(11, 9), dpi=140)
    ax = fig.add_subplot(111, projection='3d')
    by_mat = {}
    for a, b, c, m in tris:
        by_mat.setdefault(m, []).append([a, b, c])
    for m, faces in by_mat.items():
        coll = Poly3DCollection(np.array(faces), facecolors=COLORS[m],
                                edgecolors='none', linewidths=0)
        ax.add_collection3d(coll)
    pts = np.array([[a, b, c] for a, b, c, _ in tris]).reshape(-1, 3)
    lo, hi = pts.min(0), pts.max(0)
    ctr = (lo + hi) / 2
    span = (hi - lo).max() / 2 * 1.05
    ax.set_xlim(ctr[0] - span, ctr[0] + span)
    ax.set_ylim(ctr[1] - span, ctr[1] + span)
    ax.set_zlim(ctr[2] - span, ctr[2] + span)
    ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev=elev, azim=azim)
    ax.set_xlabel('X mm')
    ax.set_ylabel('Y mm')
    ax.set_zlabel('Z mm')
    ax.set_title(title + ('\n' + subtitle if subtitle else ''), fontsize=12)
    ax.grid(False)
    for pane in (ax.xaxis, ax.yaxis, ax.zaxis):
        pane.pane.set_alpha(0.06)
    plt.tight_layout()
    fig.savefig(path, bbox_inches='tight')
    plt.close(fig)


if __name__ == '__main__':
    # 单层
    tris.clear()
    jig_frame(0.0)
    build_layer(0.0, bus=True)
    n1 = write_stl(os.path.join(OUT, 'layer_6x6.stl'))
    write_dxf(os.path.join(OUT, 'layer_6x6.dxf'))
    render(os.path.join(OUT, '图_单层焊接.png'), 22, -62,
           '单层：36 只灯 + 阳极母线（从板下看）',
           '橙色=阳极(长脚)沿 x 弯折后互焊成横排母线；两条橙竖线=沿 y 的跨接线；灰色=阴极(短脚)竖直向下')
    print('layer tris', n1)

    # 整体
    tris.clear()
    build_cube()
    n2 = write_stl(os.path.join(OUT, 'cube_6x6x6.stl'))
    write_dxf(os.path.join(OUT, 'cube_6x6x6.dxf'))
    render(os.path.join(OUT, '图_整体装配.png'), 18, -58,
           '6×6×6 整体：216 只灯 / 6 层 / 层距 20 mm',
           '每层 6 条横排阳极母线 + 2 条纵向跨接线，36 根阴极竖直贯通到底部驱动板')
    print('cube tris', n2)
    print('done ->', OUT)
