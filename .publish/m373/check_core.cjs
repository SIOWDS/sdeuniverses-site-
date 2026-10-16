const fs=require('fs'),vm=require('vm'),path=require('path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../..'),window={};
vm.runInNewContext(fs.readFileSync(path.join(root,'public/books/m/373/unit/core.js'),'utf8'),{window,crypto:globalThis.crypto,TextDecoder,DOMException});
(async()=>{const C=window.BookUnitCore;assert.equal(C.BOOK,'m-373');const cases=[
 ['complete transport','data: {"t":"token","v":"模拟"}\n\ndata: {"t":"end"}\n\ndata: [DONE]\n\n','received-unverified'],
 ['truncated','data: {"t":"token","v":"片段"}\n\n','interrupted'],
 ['upstream error','data: {"t":"error","v":"模拟错误"}\n\ndata: {"t":"end"}\n\ndata: [DONE]\n\n','error'],
 ['invalid frame','data: not-json\n\ndata: {"t":"end"}\n\ndata: [DONE]\n\n','interrupted']
];for(const [name,body,expected] of cases){assert.equal(await C.parseSSE(new Response(body),()=>{}),expected,name);}const report={passed:true,book:C.BOOK,checks:cases.map(x=>x[0]),realModelTested:false,browserTested:false};fs.writeFileSync(path.join(__dirname,'core-report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));})().catch(e=>{console.error(e);process.exit(1)});
