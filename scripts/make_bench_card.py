# -*- coding: utf-8 -*-
"""生成 A4 焊接工艺卡 PDF（打印用）。

输出：docs/焊接工艺卡_A4.pdf
  第 1 页：参数 + 两条铁律 + 俯视图 + 剖面 + 四步 + 检查清单
  第 2 页：逐层检查记录表 + 可裁剪的线缆标签（L0–L5 / C00–C55）

所有排版坐标都用 mm，canvas 内部乘 mm 转 pt。
"""
import os
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAD = os.path.join(ROOT, 'docs', 'cad')
OUT = os.path.join(ROOT, 'docs', '焊接工艺卡_A4.pdf')

FONT = 'SimHei'
pdfmetrics.registerFont(TTFont(FONT, r'C:\Windows\Fonts\simhei.ttf'))

PW, PH = 210, 297            # mm
M = 10
INK = HexColor('#1f2430')
ACC = HexColor('#c0392b')
GREY = HexColor('#667085')
BG = HexColor('#f4f6f8')
BGR = HexColor('#fdf1ef')

TOP = os.path.join(CAD, '图_俯视接线.png')
SEC = os.path.join(CAD, '图_单行剖面.png')
STEP = os.path.join(CAD, '图_四个步骤.png')


def text(c, x, y, s, size=9, color=INK):
    c.setFont(FONT, size)
    c.setFillColor(color)
    c.drawString(x * mm, y * mm, s)


def box(c, x, y, w, h, fill=None, stroke=INK, lw=0.6):
    if fill is not None:
        c.setFillColor(fill)
        c.rect(x * mm, y * mm, w * mm, h * mm, stroke=0, fill=1)
    c.setStrokeColor(stroke)
    c.setLineWidth(lw)
    c.rect(x * mm, y * mm, w * mm, h * mm, stroke=1, fill=0)


def img(c, path, x, y_top, w):
    iw, ih = Image.open(path).size
    h = w * ih / iw
    c.drawImage(path, x * mm, (y_top - h) * mm, width=w * mm, height=h * mm, mask='auto')
    return h


def page1(c):
    text(c, M, PH - 13, '6×6×6 光立方 · LED 单层焊接工艺卡', 17)
    text(c, M, PH - 20, '每层 36 只  ·  共 6 层  ·  灯体朝上、灯脚朝下  ·  单位 mm', 8.5, GREY)

    # ① 俯视图（左）
    text(c, M, 268, '① 俯视接线（从上方看）', 10)
    h1 = img(c, TOP, M, 261, 64)
    text(c, M, 261 - h1 - 4, '红点=阳极  灰点=阴极  橙线=阳极弯折 绿线=跨接线', 6.6, GREY)

    # 两条铁律（左下）
    ky = 156
    box(c, M, ky, 64, 27, fill=BGR, stroke=ACC, lw=1.0)
    text(c, M + 3, ky + 24, '⚠ 两条铁律', 9.5, ACC)
    text(c, M + 3, ky + 16, '1. 两脚沿 y 错开：长脚(阳极)朝 −y、', 7.0, INK)
    text(c, M + 8, ky + 11, '短脚(阴极)朝 +y', 7.0, INK)
    text(c, M + 3, ky + 5, '2. 阳极沿 +x 弯 21.5 mm，与隔壁灯阳极脚', 7.0, INK)
    text(c, M + 8, ky + 1, '搭焊（每行 5 个焊点）', 7.0, INK)

    # 参数表（右上）
    bx, bt, bw, bh = 84, 264, 116, 50
    box(c, bx, bt - bh, bw, bh, fill=BG, stroke=GREY)
    rows = [
        ('层内间距', '20 mm × 6×6（100×100 见方）'),
        ('灯脚', 'Ø0.5，总长 25–27，两脚间距 2.54'),
        ('夹具板', '150×150×2，孔 Ø3.0–3.2'),
        ('阳极弯折', '沿 +x 弯 21.5 mm（20 + 1.5 搭接）'),
        ('层距', '20 mm，阴极叠焊 ≥ 3 mm'),
    ]
    yy = bt - 9
    for k, v in rows:
        text(c, bx + 3, yy, k, 7.4, GREY)
        text(c, bx + 30, yy, v, 7.4, INK)
        yy -= 8.6

    # ② 剖面
    text(c, bx, 208, '② 侧视剖面（灯体在上、灯脚在板下）', 10)
    img(c, SEC, bx, 204, bw)

    # ③ 四步
    text(c, M, 152, '③ 四步流程', 10)
    img(c, STEP, M, 150, PW - 2 * M)

    # ④ 检查清单
    text(c, M, 80, '④ 本层完成前必须逐项打勾', 10)
    checks = [
        '36 只灯方向一致（长脚朝 −y，平边=阴极）',
        '每只法兰压紧板面，层内平整',
        '36 根阳极都弯 21.5 mm，每行 5 个焊点',
        '两条跨接线焊好（x=10 / 90），不碰阴极脚',
        '通断：任意两个阳极脚 < 1 Ω',
        '逐只点灯：3V + 100Ω，36 只全亮',
    ]
    colw = (PW - 2 * M - 6) / 2
    for i, s in enumerate(checks):
        col, row = i % 2, i // 2
        x = M + col * (colw + 6)
        y = 72 - row * 9
        c.setStrokeColor(INK)
        c.setLineWidth(0.7)
        c.rect(x * mm, (y - 1.4) * mm, 3.4 * mm, 3.4 * mm, stroke=1, fill=0)
        text(c, x + 5.5, y, s, 7.6)

    text(c, PW - M - 42, 12, 'REV A · 2026-11-18', 6.5, GREY)


def page2(c):
    text(c, M, PH - 13, '逐层检查记录 & 线缆标签', 16)
    text(c, M, PH - 20, '每做完一层填一行；标签沿虚线剪下，贴在对应引线上', 8, GREY)

    top = PH - 30
    cw = [14, 22, 20, 22, 20, 24, 30]
    heads = ['层', '日期', '36 只全亮', '阳极 <1Ω', '跨接线', '引出线', '备注']
    rh = 11
    x = M
    for w, hd in zip(cw, heads):
        box(c, x, top - rh, w, rh, fill=BG, stroke=GREY)
        text(c, x + 1.5, top - rh + 3.8, hd, 7.2)
        x += w
    for r in range(6):
        y = top - rh * (r + 2)
        x = M
        for i, w in enumerate(cw):
            box(c, x, y, w, rh, stroke=GREY, lw=0.5)
            if i == 0:
                text(c, x + 4, y + 3.8, 'L%d' % r, 8)
            elif i in (2, 3, 4):
                c.setStrokeColor(INK)
                c.setLineWidth(0.7)
                c.rect((x + w / 2 - 1.7) * mm, (y + 3.6) * mm, 3.4 * mm, 3.4 * mm, stroke=1, fill=0)
            x += w

    # 标签区
    y0 = top - rh * 8 + 6
    text(c, M, y0, '线缆标签（沿虚线剪下）', 10)
    labels = ['L%d' % i for i in range(6)] + ['C%d%d' % (y, x) for y in range(6) for x in range(6)]
    bw, bh, per = 22, 9, 8
    for i, lab in enumerate(labels):
        r, k = divmod(i, per)
        x = M + k * (bw + 1.5)
        y = y0 - 16 - r * (bh + 1.5)
        c.setStrokeColor(GREY)
        c.setLineWidth(0.4)
        c.setDash(1.2, 1.2)
        c.rect(x * mm, y * mm, bw * mm, bh * mm, stroke=1, fill=0)
        c.setDash()
        text(c, x + 6.5, y + 3, lab, 8.5)

    yn = y0 - 16 - 6 * (bh + 1.5) - 12
    notes = [
        'L0–L5 = 六层阳极（L0 最下层）；C{y}{x} = 第 y 行、第 x 列的竖直列线（阴极）。',
        '板上丝印对应：ROW0–ROW5 对应 y=0–5，一组内按 x=0–5 排列；L0–L5 单独一排。',
        '叠层焊阴极前先核对标签，错一根就是一个点亮位置偏移。',
        '每层焊完把该层的阳极引出线标好 L 号，再起层。',
    ]
    for s in notes:
        text(c, M, yn, '· ' + s, 7.6, GREY)
        yn -= 6.5


if __name__ == '__main__':
    c = canvas.Canvas(OUT, pagesize=A4)
    c.setTitle('6x6x6 光立方 · 单层焊接工艺卡')
    page1(c)
    c.showPage()
    page2(c)
    c.showPage()
    c.save()
    print('saved', OUT, os.path.getsize(OUT), 'bytes')
