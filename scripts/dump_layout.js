// 导出当前 PCB 布局数据到 docs/_layout_dump.json（配合 render_layout.py 出预览图）
// 用法：py scripts/eda_exec.py scripts/dump_layout.js > docs/_layout_dump.json
const MM = 39.3701;
const pcbs = await eda.dmt_Pcb.getAllPcbsInfo();
await eda.dmt_EditorControl.openDocument(pcbs[0].uuid);
await new Promise(r => setTimeout(r, 1800));

const lines = await eda.pcb_PrimitiveLine.getAll() || [];
const outline = lines.filter(l => l.getState_Layer() === 11).map(l => ({
  x1: l.getState_StartX(), y1: l.getState_StartY(), x2: l.getState_EndX(), y2: l.getState_EndY()
}));
const xs = [], ys = [];
for (const o of outline) { xs.push(o.x1, o.x2); ys.push(o.y1, o.y2); }
const box = { x0: Math.min(...xs), x1: Math.max(...xs), y0: Math.min(...ys), y1: Math.max(...ys) };

const comps = await eda.pcb_PrimitiveComponent.getAll();
const out = [];
const compPadIds = new Set();
for (const c of comps) {
  const pins = await eda.pcb_PrimitiveComponent.getAllPinsByPrimitiveId(c.getState_PrimitiveId()) || [];
  for (const p of pins) compPadIds.add(p.getState_PrimitiveId());
  out.push({ d: c.getState_Designator(), rot: c.getState_Rotation(), layer: c.getState_Layer(),
    x: c.getState_X(), y: c.getState_Y(),
    pads: pins.map(p => ({ n: p.getState_PadNumber(), x: p.getState_X(), y: p.getState_Y(), net: p.getState_Net() })) });
}
const th = [];
for (const p of await eda.pcb_PrimitivePad.getAll()) {
  if (compPadIds.has(p.getState_PrimitiveId())) continue;
  th.push({ n: p.getState_PadNumber(), x: p.getState_X(), y: p.getState_Y(), net: p.getState_Net() });
}
const texts = await eda.pcb_PrimitiveString.getAll() || [];
return {
  box, outline, mm: MM,
  comps: out, th,
  texts: texts.map(t => ({ s: t.getState_Text ? t.getState_Text() : '', x: t.getState_X(), y: t.getState_Y(), rot: t.getState_Rotation ? t.getState_Rotation() : 0 }))
};
