// 巴渝「预习材料」幻灯页运行时模拟：mock DOM + mock pdfjsLib，跑一遍
// /banyu/prep/math-slides/ 的内联脚本。用法：node tools/sim_banyu_slides.js（仓库根目录）。
// 与 sim_tv_reader.js 同一套骨架，差别只有两处：这一页没有陪读挂钩（WDS_READ），
// 因为它是幻灯不是文章；PDF 路径不同。
// 失败路径复验：把 getDocument 换成 Promise.reject 再跑一遍，应仍打印 SIM OK。
const fs=require('fs');
const html=fs.readFileSync('public/banyu/prep/math-slides/index.html','utf8');
const js=html.match(/<script>([\s\S]*?)<\/script>/)[1];
const IDS=['error','loading','next','page-wrap','pageInput','pdfCanvas','prev','stage','textLayer','totalPages','zoomIn','zoomOut'];
function mkEl(id){return {id,style:{},innerHTML:'',textContent:'',value:'',max:0,disabled:false,
  clientWidth:900,appendChild(){},getBoundingClientRect(){return{width:10}},
  getContext(){return{setTransform(){}};}};}
const els={};IDS.forEach(i=>els[i]=mkEl(i));
const listeners={};
global.document={getElementById:i=>els[i]||null,
  createElement:()=>mkEl('x'),createDocumentFragment:()=>({appendChild(){}}),
  addEventListener:(e,f)=>{(listeners[e]=listeners[e]||[]).push(f);}};
global.window={devicePixelRatio:2,innerWidth:1000,addEventListener:(e,f)=>{(listeners[e]=listeners[e]||[]).push(f);},
  scrollTo(){},WDS_READ:null};
global.setTimeout=setTimeout;global.clearTimeout=clearTimeout;
const items=[{str:'一二三',transform:[12,0,0,12,50,700],width:36},{str:'',transform:[12,0,0,12,0,0],width:0}];
const page={getViewport:({scale})=>({width:600*scale,height:850*scale,scale,transform:[scale,0,0,-scale,0,850*scale]}),
  render(){return{promise:Promise.resolve()};},getTextContent(){return Promise.resolve({items});}};
global.pdfjsLib={GlobalWorkerOptions:{},
  Util:{transform:(a,b)=>[b[0],b[1],b[2],b[3],b[4],b[5]]},
  getDocument:()=>({promise:Promise.resolve({numPages:39,getPage:()=>Promise.resolve(page)})})};
eval(js);
setTimeout(()=>{
  const $=i=>els[i];
  console.log('totalPages =',$('totalPages').textContent);
  console.log('loading display =',$('loading').style.display);
  console.log('page-wrap display =',$('page-wrap').style.display);
  $('next').onclick();$('zoomIn').onclick();$('zoomOut').onclick();
  $('pageInput').value=12;$('pageInput').onchange({target:{value:'12'}});
  setTimeout(()=>{
    console.log('after next+jump, pageInput =',$('pageInput').value);
      console.log('keydown 监听器 =',(listeners['keydown']||[]).length,'resize =',(listeners['resize']||[]).length);
    console.log('SIM OK');
  },60);
},60);
