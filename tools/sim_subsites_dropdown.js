/* 首页专栏条「子网站」下拉的护栏：六个二级域名齐不齐、顺序对不对、开合四种收起路径、中英两份文案。
   跑法：cd 仓库根 && node tools/sim_subsites_dropdown.js（需 npm i jsdom --no-save）。 */
const fs=require('fs');const {JSDOM}=require('jsdom');
const html=fs.readFileSync(__dirname + '/../public/browse/index.html','utf8');
let pass=0,fail=0;const t=(n,c)=>{c?(pass++):(fail++,console.log("FAIL:",n));};
const dom=new JSDOM(html,{runScripts:"dangerously",pretendToBeVisual:true,url:"https://sdeuniverses.com/browse/"});
const d=dom.window.document;
setTimeout(()=>{
 const box=d.getElementById('nbs-sub'),btn=box&&box.querySelector('.nbs-sub-btn'),menu=d.getElementById('nbs-sub-menu');
 t("下拉存在",!!box&&!!btn&&!!menu);
 t("在专栏条里",box.parentElement.classList.contains('nbs-row'));
 t("专栏条共16格",d.querySelector('.nbs-row').children.length===16+15); // links doubled by zh/en
 const links=[...menu.querySelectorAll('a')];
 t("六条分站",links.length===6);
 const want=['health','lang','liter','edu','math','comp'].map(s=>`https://${s}.sdeuniverses.com/`);
 t("六个域名齐且顺序对",JSON.stringify(links.map(a=>a.getAttribute('href')))===JSON.stringify(want));
 t("每条都有中英两份",links.every(a=>a.querySelector('b.zh-only')&&a.querySelector('b.en-only')));
 t("默认收起",menu.hidden===true&&btn.getAttribute('aria-expanded')==='false');
 btn.dispatchEvent(new dom.window.MouseEvent('click',{bubbles:true}));
 t("点按钮展开",menu.hidden===false&&btn.getAttribute('aria-expanded')==='true');
 btn.dispatchEvent(new dom.window.MouseEvent('click',{bubbles:true}));
 t("再点收起",menu.hidden===true);
 btn.dispatchEvent(new dom.window.MouseEvent('click',{bubbles:true}));
 d.body.dispatchEvent(new dom.window.MouseEvent('click',{bubbles:true}));
 t("点别处收起",menu.hidden===true);
 btn.dispatchEvent(new dom.window.MouseEvent('click',{bubbles:true}));
 d.dispatchEvent(new dom.window.KeyboardEvent('keydown',{key:'Escape',bubbles:true}));
 t("Esc 收起",menu.hidden===true);
 btn.dispatchEvent(new dom.window.MouseEvent('click',{bubbles:true}));
 links[0].dispatchEvent(new dom.window.MouseEvent('click',{bubbles:true}));
 t("点条目后收起",menu.hidden===true);
 // 中英切换
 dom.window.setLang('en');
 t("切英文后按钮英文文案在",btn.querySelector('.en-only').textContent.includes('Sub-sites'));
 t("body 类切到 en",d.body.classList.contains('en'));
 dom.window.setLang('zh');
 t("切回中文",d.body.classList.contains('zh'));
 // 让位量：菜单开合改 nav 高度，观察器在
 t("nav 存在且含专栏条",!!d.querySelector('nav .nbs-row'));
 console.log(`\n${pass} PASS / ${fail} FAIL`);
 process.exit(fail?1:0);
},600);
