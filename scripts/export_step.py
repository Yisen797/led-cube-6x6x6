# -*- coding: utf-8 -*-
"""用 gmsh(OCC 内核) 生成实体 STEP，SolidWorks 可直接打开。
输出：led_single.step / layer_6x6.step / cube_6x6x6.step
"""
import os
import gmsh

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'docs', 'cad')
os.makedirs(OUT, exist_ok=True)

PITCH, GAP = 20.0, 20.0
BODY_D, BODY_H = 3.0, 5.0
FLANGE_D, FLANGE_H = 4.0, 0.5
LR, LP = 0.25, 2.54
PLATE_T, ANODE_BEND, CATHODE = 2.0, 21.5, 22.0


def led(occ, cx, cy, z0):
    occ.addCylinder(cx, cy, z0, 0, 0, FLANGE_H, FLANGE_D / 2)
    occ.addCylinder(cx, cy, z0 + FLANGE_H, 0, 0, BODY_H, BODY_D / 2)
    xa, ya = cx, cy - LP / 2
    xk, yk = cx, cy + LP / 2
    zb = z0 - PLATE_T
    occ.addCylinder(xa, ya, z0, 0, 0, -PLATE_T, LR)          # 阳极穿板
    occ.addCylinder(xa, ya, zb, ANODE_BEND, 0, 0, LR)         # 阳极弯折
    occ.addCylinder(xk, yk, z0, 0, 0, -CATHODE, LR)           # 阴极向下


def build(positions, name, path):
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.model.add(name)
    occ = gmsh.model.occ
    for (x, y, z) in positions:
        led(occ, x, y, z)
    occ.synchronize()
    gmsh.write(path)
    gmsh.finalize()
    return os.path.getsize(path)


def layer_positions(z=0.0):
    h = PITCH * 2.5
    return [(x, y, z) for iy in range(6) for x in [(-h + ix * PITCH) for ix in range(6)]
            for y in [(-h + iy * PITCH)]]


def cube_positions():
    return [(x, y, k * GAP) for k in range(6) for (x, y, _) in layer_positions()]


if __name__ == '__main__':
    print('single', build([(0.0, 0.0, 0.0)], 'led', os.path.join(OUT, 'led_single.step')))
    print('layer', build(layer_positions(), 'layer', os.path.join(OUT, 'layer_6x6.step')))
    print('cube', build(cube_positions(), 'cube', os.path.join(OUT, 'cube_6x6x6.step')))
