/* sim_measure_block.js — ChatSDE 1.2c 分寸闸护栏（2026-09-16）
 * ① MEASURE_BLOCK 能求值成字符串 ② 七条硬句子都在 ③ 不含母体术语（改姓档也注入）
 * ④ 注入点独立一行、紧跟 SDE_FRAME_BLOCK 那一行 ⑤ 恰好出现两次（定义＋注入） */
const fs=require('fs');const src=fs.readFileSync(__dirname+'/../src/worker.js','utf8');
let pass=0,fail=0;const ok=(c,m)=>{if(c){pass++;console.log('✓',m)}else{fail++;console.log('✗',m)}};
function evalConst(name){const i=src.indexOf('const '+name+' = ');const j=src.indexOf(';\n',i);return eval(src.slice(i+('const '+name+' = ').length,j));}
let B='';try{B=evalConst('MEASURE_BLOCK');}catch(e){}
ok(typeof B==='string'&&B.length>500,'MEASURE_BLOCK 求值成字符串，长度 '+B.length);
['能承接就先承接','不许以「不是」「错了」「问错了」开场','只许问，不许断','先守安全底线','前后一致','比喻有度','同一个核心比喻本场最多用两轮','拿不准的不举','引站内资料为支撑，不为装饰','自检一句再发'].forEach(k=>ok(B.includes(k),'含：'+k));
['SDE','解构卡','承重句','三号位','显露','纠缠','改格'].forEach(t=>ok(!B.includes(t),'不含母体术语：'+t));
ok(/\+ \(\(prof && prof\.term\) \? "" : SDE_FRAME_BLOCK\)\n[^\n]*\n\s*\+ MEASURE_BLOCK\n/.test(src),'注入点紧跟 FRAME 行、独立一行');
ok((src.match(/MEASURE_BLOCK/g)||[]).length===2,'MEASURE_BLOCK 恰好出现两次（定义＋注入）');
console.log(`${pass} passed, ${fail} failed`);process.exit(fail?1:0);
