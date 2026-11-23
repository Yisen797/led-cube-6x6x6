# scripts 说明

全部脚本用办公环境里的 Python 跑（自带 numpy / matplotlib / reportlab / ezdxf / gmsh）：

```bash
VENV=python
```

| 脚本 | 作用 | 产物 |
|:--|:--|:--|
| `eda_exec.py` | 把一段 JS 发到本地 EasyEDA 桥执行（用法：`py eda_exec.py code.js [windowId]`） | — |
| `dump_layout.js` | 导出当前 PCB 的器件/焊盘/丝印数据 | `docs/_layout_dump.json` |
| `render_layout.py` | 把上面的 JSON 画成顶面/底面双视图 | `docs/驱动板布局预览.png` |
| `cad_led_cube.py` | 参数化生成光立方几何（LED/母线/夹具） | `docs/cad/*.stl`、`图_单层焊接.png`、`图_整体装配.png` |
| `cad_solder_diagram.py` | 2D 焊接工艺图（俯视/剖面/四步） | `docs/cad/图_俯视接线.png` 等 |
| `export_step.py` | gmsh(OCC) 导出实体 STEP | `docs/cad/*.step` |
| `make_stl_viewer.py` | 把 STL 打包成离线可旋转的 HTML | `docs/cad/*_3D查看器.html` |
| `make_bench_card.py` | 生成 A4 焊接工艺卡（工艺图 + 记录表 + 标签） | `docs/焊接工艺卡_A4.pdf` |
| `fig1_system.dot` | Graphviz 系统框图源文件 | `docs/fig1_系统框图.*` |
| `figs_mech.py` | 单层接线 / 刷新时序 / 层叠结构三张图 | `docs/fig2/fig4/fig5_*.png/svg` |
| `jig_a4.py` | 夹具 1:1 钻孔图 | `docs/夹具图纸_A4_1比1.pdf` |

## 常用

```bash
cd <项目根目录>

# 重新出 CAD 全套（STL + 渲染 + STEP）
$VENV scripts/cad_led_cube.py
$VENV scripts/cad_solder_diagram.py
$VENV scripts/export_step.py

# 重新出工艺卡
$VENV scripts/make_bench_card.py

# 从 EDA 重新抓布局并出预览（需要 EDA 开着 + 桥在跑）
py scripts/eda_exec.py scripts/dump_layout.js > docs/_layout_dump.json
$VENV scripts/render_layout.py
```

## 注意

- `eda_exec.py` 用的是系统 `py`（3.12），其它脚本用办公 venv；别混。
- EasyEDA 有新版本时枚举/接口可能变，踩坑记录见全局记忆 `easyeda-api-bridge`。
- 尺寸常量都在脚本顶部（PITCH / LAYER_GAP / ANODE_BEND …），改尺寸只动那里。
