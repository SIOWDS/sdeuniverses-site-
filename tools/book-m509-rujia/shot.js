const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1004,height:1418}});
for (const [src,out] of [['cover.html','cover.jpg'],['backcover.html','backcover.jpg']]){
 try{await p.goto('file:///home/claude/rujia/build/'+src);await p.waitForTimeout(400);
 await p.screenshot({path:'/home/claude/rujia/build/'+out,type:'jpeg',quality:92});console.log('ok',out)}catch(e){console.log('skip',src,e.message.slice(0,80))}}
await b.close()})();
