"""把 docs/_layout_dump.json 渲染成顶面/底面双视图 PNG（坐标渲染，非 EDA 截图）。
数据来源：py scripts/eda_exec.py scripts/dump_layout.js > docs/_layout_dump.json
"""
import json
from PIL import Image, ImageDraw, ImageFont

data = json.load(open('docs/_layout_dump.json', encoding='utf-8'))['result']
MM = data['mm']
box = data['box']
W_MM = (box['x1'] - box['x0']) / MM
H_MM = (box['y1'] - box['y0']) / MM
S = max(6, int(900 / max(W_MM, H_MM)))  # px per mm
W = int(W_MM * S)
H = int(H_MM * S)
PAD = 30

img = Image.new('RGB', (W * 2 + PAD * 3, H + PAD * 2 + 64), 'white')
d = ImageDraw.Draw(img)
try:
    f = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 10)
    fs = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 8)
    ft = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 13)
except Exception:
    f = fs = ft = ImageFont.load_default()


def plane(ox, oy, mirror=False):
    def px(x, y):
        xm = (x - box['x0']) / MM
        if mirror:
            xm = W_MM - xm
        return (ox + xm * S, oy + (H_MM - (y - box['y0']) / MM) * S)
    return px


def frame(ox, oy, title):
    d.rectangle([ox, oy, ox + W, oy + H], outline='black', width=2)
    d.text((ox, oy - 18), title, fill='black', font=ft)


# M3 孔 = 无网络通孔（直径 3.2mm）
holes = [t for t in data['th'] if not t['net']]

# ---------- 顶面 ----------
ox, oy = PAD, PAD + 10
frame(ox, oy, '顶面（朝立方体）：36 列焊盘 + 6 层焊盘')
p = plane(ox, oy)
for t in holes:
    cx, cy = p(t['x'], t['y'])
    r = 3 * S
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline='red', width=2)
for t in data['th']:
    if not t['net']:
        continue
    cx, cy = p(t['x'], t['y'])
    r = 1.2 * S
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline='#b00000', fill='#ffd9d9', width=1)
    d.text((cx - 7, cy - 12), t['net'], fill='#800000', font=fs)

# ---------- 底面 ----------
ox2 = PAD * 2 + W
frame(ox2, oy, '底面（从下往上看）：全部器件贴装')
p2 = plane(ox2, oy, mirror=True)
for c in data['comps']:
    pts = [p2(q['x'], q['y']) for q in c['pads']]
    if not pts:
        continue
    xs = [q[0] for q in pts]
    ys = [q[1] for q in pts]
    m = 0.7 * S
    d.rectangle([min(xs) - m, min(ys) - m, max(xs) + m, max(ys) + m], outline='#3a6ea5')
    for x, y in pts:
        r = 1.0 * S
        d.ellipse([x - r, y - r, x + r, y + r], outline='#c08040')
    if len(str(c['d'])) <= 3:
        d.text(((sum(xs) / len(xs)) - 7, (sum(ys) / len(ys)) - 5), str(c['d']), fill='black', font=f)
for t in holes:
    cx, cy = p2(t['x'], t['y'])
    r = 3 * S
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline='red', width=2)
for t in data['th']:
    if not t['net']:
        continue
    cx, cy = p2(t['x'], t['y'])
    r = 1.2 * S
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline='#b00000', width=1)
for tx in data['texts']:
    cx, cy = p2(tx['x'], tx['y'])
    d.text((cx - 12, cy - 4), tx['s'][:16], fill='#888', font=fs)

d.text((PAD, oy + H + 14),
       f'6×6×6 光立方驱动板 · {W_MM:.0f}×{H_MM:.0f} mm · 四角 M3(3.2mm) · 顶面只有 42 个通孔焊盘，器件全部在底面',
       fill='#222', font=ft)
d.text((PAD, oy + H + 36),
       '红圈=M3 孔　蓝框=器件　橙圈=器件焊盘　深红=42 个通孔焊盘（标网络名）',
       fill='#444', font=f)
img.save('docs/驱动板布局预览.png')
print('ok', W_MM, H_MM)
