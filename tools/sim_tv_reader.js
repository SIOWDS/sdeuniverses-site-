// 三视角阅读页运行时模拟：mock DOM + mock pdfjsLib，跑一遍 /three-views/read/a001/ 的内联脚本。
// 用法：node tools/sim_tv_reader.js（在仓库根目录跑）。改阅读页模板后强制跑一次——
// node --check 只查语法，抓不到「载入失败后按缩放键抛 TypeError」那一类运行时错。
// 失败路径复验：把 getDocument 换成 Promise.reject 再跑一遍，应仍打印 SIM OK。
// 模拟：假的 DOM + 假的 pdfjsLib，跑一遍阅读页脚本，抓运行时错误
const fs=require('fs');
const html=fs.readFileSync('public/three-views/read/a001/index.html','utf8');
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
    console.log('WDS_READ title =',global.window.WDS_READ.title);
    console.log('WDS_READ text  =',global.window.WDS_READ.docTextFn().slice(0,40).replace(/\n/g,' | '));
    console.log('keydown 监听器 =',(listeners['keydown']||[]).length,'resize =',(listeners['resize']||[]).length);
    console.log('SIM OK');
  },60);
},60);
