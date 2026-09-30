const {chromium}=require('/opt/node22/lib/node_modules/playwright');
const fs=require('fs');const dir=process.argv[2];const only=process.argv[3];
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1920,height:1080}});
await p.goto('file://'+__dirname+'/farm.html');const TL=JSON.parse(fs.readFileSync(__dirname+'/timeline.json'));
await p.evaluate(o=>setTL(o),TL);fs.mkdirSync(dir,{recursive:true});
const fps=30;const times=only?only.split(',').map(Number):[...Array(Math.ceil(TL.total*fps)).keys()].map(i=>i/fps);
for(let i=0;i<times.length;i++){await p.evaluate(t=>renderAt(t),times[i]);
 await p.screenshot({path:`${dir}/f${String(i).padStart(5,'0')}.jpg`,type:'jpeg',quality:92});}
await b.close()})();
