# -*- coding: utf-8 -*-
"""把二进制 STL 打包成一个**离线可旋转**的 HTML 查看器（three.js 内联，双击就能看）。

用法：
    python make_stl_viewer.py <a.stl> <out.html> [标题]

不依赖任何在线资源；产出的 html 自己带 three.js 和模型数据。
"""
import base64
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
THREE_JS = os.environ.get('THREE_JS', r'<用户目录>\AppData\Local\Temp\three.min.js')

TPL = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>__TITLE__</title>
<style>
  html,body{margin:0;height:100%;overflow:hidden;background:#eef1f5;font-family:"Microsoft YaHei",sans-serif}
  #hud{position:fixed;left:14px;top:12px;color:#333;font-size:13px;line-height:1.7;pointer-events:none}
  #hud b{font-size:15px}
</style>
</head>
<body>
<div id="hud"><b>__TITLE__</b><br>左键拖动＝旋转　滚轮＝缩放　右键拖动＝平移</div>
<script>__THREE__</script>
<script>
const STL_B64 = "__STL__";
function b64bytes(s){const b=atob(s),u=new Uint8Array(b.length);for(let i=0;i<b.length;i++)u[i]=b.charCodeAt(i);return u;}
function parseSTL(u){
  const dv=new DataView(u.buffer,u.byteOffset,u.byteLength);
  const n=dv.getUint32(80,true);
  const pos=new Float32Array(n*9),nor=new Float32Array(n*9);
  let o=84;
  for(let i=0;i<n;i++){
    const nx=dv.getFloat32(o,true),ny=dv.getFloat32(o+4,true),nz=dv.getFloat32(o+8,true);o+=12;
    for(let k=0;k<3;k++){
      const x=dv.getFloat32(o,true),y=dv.getFloat32(o+4,true),z=dv.getFloat32(o+8,true);o+=12;
      const j=i*9+k*3;pos[j]=x;pos[j+1]=y;pos[j+2]=z;nor[j]=nx;nor[j+1]=ny;nor[j+2]=nz;
    }
    o+=2;
  }
  return {pos,nor};
}
const geoData=parseSTL(b64bytes(STL_B64));
const scene=new THREE.Scene();
scene.background=new THREE.Color(0xeef1f5);
const camera=new THREE.PerspectiveCamera(40,innerWidth/innerHeight,0.1,5000);
const renderer=new THREE.WebGLRenderer({antialias:true});
renderer.setSize(innerWidth,innerHeight);
renderer.setPixelRatio(Math.min(devicePixelRatio,2));
document.body.appendChild(renderer.domElement);

const geo=new THREE.BufferGeometry();
geo.setAttribute('position',new THREE.BufferAttribute(geoData.pos,3));
geo.setAttribute('normal',new THREE.BufferAttribute(geoData.nor,3));
geo.computeBoundingSphere();
const mesh=new THREE.Mesh(geo,new THREE.MeshStandardMaterial({
  color:0x4a7fd4,metalness:0.15,roughness:0.55,flatShading:false,side:THREE.DoubleSide}));
mesh.rotation.x=-Math.PI/2;           // STL 是 Z 向上，three 是 Y 向上
scene.add(mesh);

scene.add(new THREE.AmbientLight(0xffffff,0.75));
const d1=new THREE.DirectionalLight(0xffffff,0.85);d1.position.set(120,-160,220);scene.add(d1);
const d2=new THREE.DirectionalLight(0xffffff,0.45);d2.position.set(-180,120,-90);scene.add(d2);

const bs=geo.boundingSphere;
const target=bs.center.clone().applyEuler(mesh.rotation);
let dist=bs.radius*2.6, theta=0.9, phi=1.05;
function upd(){
  camera.position.set(
    target.x+dist*Math.sin(phi)*Math.cos(theta),
    target.y+dist*Math.cos(phi),
    target.z+dist*Math.sin(phi)*Math.sin(theta));
  camera.lookAt(target);
}
upd();

let drag=null,px=0,py=0;
renderer.domElement.addEventListener('mousedown',e=>{drag=e.button;px=e.clientX;py=e.clientY;});
addEventListener('mouseup',()=>drag=null);
addEventListener('mousemove',e=>{
  if(drag===null)return;
  const dx=(e.clientX-px)/220, dy=(e.clientY-py)/220; px=e.clientX;py=e.clientY;
  if(drag===0){theta-=dx; phi=Math.max(0.15,Math.min(Math.PI-0.15,phi-dy));}
  else{const s=dist*0.0016; target.x-=dx*s*Math.sin(theta)*0+dx*s*Math.cos(theta); target.z-=dx*s*Math.sin(theta); target.y+=dy*s;}
  upd();
});
renderer.domElement.addEventListener('contextmenu',e=>e.preventDefault());
addEventListener('wheel',e=>{dist*=Math.exp(e.deltaY*0.0012);dist=Math.max(bs.radius*0.6,Math.min(bs.radius*12,dist));upd();},{passive:true});
addEventListener('resize',()=>{camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight);});
(function loop(){requestAnimationFrame(loop);renderer.render(scene,camera);})();
</script>
</body></html>
"""


def make(stl_path, out_path, title):
    data = open(stl_path, 'rb').read()
    b64 = base64.b64encode(data).decode('ascii')
    three = open(THREE_JS, encoding='utf-8').read()
    html = TPL.replace('__TITLE__', title).replace('__THREE__', three).replace('__STL__', b64)
    open(out_path, 'w', encoding='utf-8').write(html)
    return len(html)


if __name__ == '__main__':
    stl = sys.argv[1]
    out = sys.argv[2]
    title = sys.argv[3] if len(sys.argv) > 3 else os.path.basename(stl)
    n = make(stl, out, title)
    print('wrote', out, n, 'bytes')
