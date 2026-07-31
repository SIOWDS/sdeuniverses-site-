/* 朋友圈文章附件的定向模拟：装真 DO + 假存储 + 假 R2，跑真逻辑（沿用 sim_moments 的套路） */
import { CommentBox } from "../src/worker.js";
let ok=0,bad=0; const t=(n,c)=>{ if(c){ok++;console.log("  ✓ "+n);} else {bad++;console.log("  ✗ "+n);} };
class Store{ constructor(){this.m=new Map()}
  async get(k){return this.m.get(k)} async put(k,v){this.m.set(k,v)} async delete(k){return this.m.delete(k)}
  async list(o={}){const p=o.prefix||"";let ks=[...this.m.keys()].filter(k=>k.startsWith(p)).sort();
    if(o.startAfter)ks=ks.filter(k=>k>o.startAfter); if(o.limit)ks=ks.slice(0,o.limit);
    return new Map(ks.map(k=>[k,this.m.get(k)]));} }
const mkDO=()=>{const st=new Store();const box=new CommentBox({storage:st},{});return {box,st};};
const call=async(box,p)=>JSON.parse(await (await box.fetch(new Request("https://do/_dir",{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify(p)}))).text());
const UID="a1b2c3d4e5f6", K="0123456789abcdef";

console.log("场景1 · 只附一篇文章、不写字不放图，也该发得出去");
{const {box}=mkDO();
 const r=await call(box,{op:"mopost",uid:UID,name:"张琼",text:"",imgs:[],doc:{k:K,t:"pdf",n:"论静为.pdf",s:123456}});
 t("发表成功", r.ok===true);
 t("doc 落库", !!(r.post&&r.post.doc&&r.post.doc.k===K));
 t("类型与文件名保住", r.post.doc.t==="pdf"&&r.post.doc.n==="论静为.pdf");
 t("字节数保住", r.post.doc.s===123456);}

console.log("场景2 · 三者皆空才该被拦");
{const {box}=mkDO();
 const r=await call(box,{op:"mopost",uid:UID,name:"张琼",text:"",imgs:[],doc:null});
 t("空动态被拦", r.ok===false);
 t("提示里提到了文章", String(r.msg||"").includes("文章"));}

console.log("场景3 · 伪造的 doc 一律丢掉，不炸");
{ /* ⚠️ mopost 有「两条间隔 5 秒」限流，循环里必须每次换一个新 DO，否则第二条起被限流挡掉、
      看起来像 doc 没被丢弃。第一版模拟就是栽在这里。 */
 for(const d of [{k:"短",t:"pdf"},{k:K,t:"exe"},{k:K.toUpperCase(),t:"pdf"},{k:"../../etc/passwd",t:"pdf"}]){
   const {box}=mkDO();
   const r=await call(box,{op:"mopost",uid:UID,name:"张琼",text:"正文在此",imgs:[],doc:d});
   if(!(r.ok===true&&r.post.doc===null)){bad++;console.log("  ✗ 非法 doc 未被丢弃: "+JSON.stringify(d));ok--;}
 }
 ok++;console.log("  ✓ 四种非法 doc 全被丢弃且正文照发");}

console.log("场景4 · 图片＋文章可以同时有（用户要的『即有图片 和 文章』）");
{const {box}=mkDO();
 const r=await call(box,{op:"mopost",uid:UID,name:"张琼",text:"配图与全文",imgs:["ffffffffffffffff"],doc:{k:K,t:"docx",n:"稿.docx",s:9}});
 t("图片与文章并存", r.ok&&r.post.imgs.length===1&&r.post.doc.t==="docx");}

console.log("场景5 · 删动态要把附件一并回传给路由层去删 R2");
{const {box}=mkDO();
 const p=await call(box,{op:"mopost",uid:UID,name:"张琼",text:"x",imgs:["ffffffffffffffff"],doc:{k:K,t:"pdf",n:"a.pdf",s:1}});
 const d=await call(box,{op:"model",uid:UID,id:p.post.id});
 t("删除成功", d.ok===true);
 t("回传 imgs", Array.isArray(d.imgs)&&d.imgs[0]==="ffffffffffffffff");
 t("回传 doc（否则附件会永远留在桶里）", !!(d.doc&&d.doc.k===K&&d.doc.t==="pdf"));}

console.log("场景6 · 别人删不动我的动态，附件也不该被删");
{const {box}=mkDO();
 const p=await call(box,{op:"mopost",uid:UID,name:"张琼",text:"x",imgs:[],doc:{k:K,t:"pdf",n:"a.pdf",s:1}});
 const d=await call(box,{op:"model",uid:"ffffffffffff",id:p.post.id});
 t("非作者删除被拒", d.ok===false&&d.code===403);
 t("被拒时不回传 doc", !d.doc);}

console.log("场景7 · 文件名过长要截断，不能撑爆存储");
{const {box}=mkDO();
 const r=await call(box,{op:"mopost",uid:UID,name:"张琼",text:"x",imgs:[],doc:{k:K,t:"pdf",n:"名".repeat(500),s:1}});
 t("文件名被截到 80 以内", r.post.doc.n.length<=80);}

console.log("场景8 · 真身校验的字节判据（路由层用的那两条）");
{const magic=(b)=>({pdf:b[0]===0x25&&b[1]===0x50&&b[2]===0x44&&b[3]===0x46, zip:b[0]===0x50&&b[1]===0x4b&&b[2]===0x03&&b[3]===0x04});
 t("%PDF- 认作 pdf", magic(new Uint8Array([0x25,0x50,0x44,0x46,0x2d])).pdf===true);
 t("PK\\x03\\x04 认作 docx", magic(new Uint8Array([0x50,0x4b,0x03,0x04])).zip===true);
 t("改了扩展名的假 PDF 认不出", magic(new Uint8Array([0x00,0x01,0x02,0x03])).pdf===false);}

console.log("\n通过 "+ok+" / 失败 "+bad); process.exit(bad?1:0);
