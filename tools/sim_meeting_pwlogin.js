/* /meeting/ 身份条模拟：社区名字＋密码。跑法：node tools/sim_meeting_pwlogin.js */
const fs=require("fs");
const {JSDOM}=require("/home/claude/simenv/node_modules/jsdom");
const html=fs.readFileSync(__dirname+"/../public/meeting/index.html","utf8");
let pass=0,fail=0;
function ok(c,m){c?(pass++,console.log("  ✓ "+m)):(fail++,console.log("  ✗ "+m));}
const dom=new JSDOM(html,{runScripts:"dangerously",url:"https://sdeuniverses.com/meeting/",pretendToBeVisual:true});
const w=dom.window,d=w.document;
let apiCalls=[];
w.fetch=function(u,o){
  apiCalls.push([u,o&&o.body]);
  if(String(u).indexOf("/api/im")>-1){
    const b=JSON.parse(o.body), bad=/^sdepw1:wrong:/.test(b.credential);
    return Promise.resolve({json:()=>Promise.resolve(bad?{ok:false,msg:"进不去，请检查名字和密码。"}:{ok:true,me:{name:"王德生",uid:"aabbccddeeff"}})});
  }
  if(String(u).indexOf("roster.json")>-1)return Promise.resolve({json:()=>Promise.resolve({students:[{name:"王德生"},{name:"胡敏"}]})});
  return Promise.resolve({json:()=>Promise.resolve({})});
};
w.alert=function(){};
w.Element.prototype.scrollIntoView=function(){};   // jsdom 无此实现，桩掉
w.open=function(u){w.__opened=u;return null};
const $=id=>d.getElementById(id);
setTimeout(()=>{
  console.log("① 初始（未登录）");
  ok(!!$("ma-pw"),"名字+密码输入行存在");
  ok($("ma-pw").style.display==="flex","未登录时输入行显示");
  ok($("ma-out").style.display==="none","未登录时不显示已进入条");
  ok($("ma-gsi").style.display==="none","Google 按钮位已隐藏");
  ok($("ma-msg").textContent.indexOf("加载失败")===-1,"不再弹 Google 组件加载失败");
  ok(w.SDE_MEET_NAME==="","未登录时 SDE_MEET_NAME 为空");
  console.log("② 未登录点进入教室 → 拦下并提示");
  w.joinRoom("SDE-Universes-Classroom");
  ok(!w.__opened,"未登录不放行");
  ok($("ma-msg").textContent.indexOf("社区名字和密码")>-1,"提示语已改为社区名字和密码");
  console.log("③ 空字段守门");
  $("ma-pw-go").click();
  ok($("ma-msg").textContent==="先填名字。","空名字被拦");
  $("ma-pw-name").value="王德生";$("ma-pw-go").click();
  ok($("ma-msg").textContent==="请输入密码。","空密码被拦");
  console.log("④ 密码错");
  $("ma-pw-code").value="wrong";apiCalls=[];$("ma-pw-go").click();
  setTimeout(()=>{
    ok($("ma-msg").textContent.indexOf("检查名字和密码")>-1,"密码错给出可读提示");
    ok(w.SDE_MEET_NAME==="","密码错不写入身份");
    console.log("⑤ 正确进入");
    $("ma-pw-code").value="right";$("ma-pw-go").click();
    setTimeout(()=>{
      const body=JSON.parse(apiCalls[apiCalls.length-1][1]);
      ok(body.op==="hello","调用 /api/im op=hello");
      ok(body.credential==="sdepw1:right:王德生","凭证格式 sdepw1:<密码>:<名字>");
      ok(w.SDE_MEET_NAME==="王德生","SDE_MEET_NAME 已就位");
      ok($("ma-out").style.display==="block"&&$("ma-pw").style.display==="none","切到已进入态");
      ok($("ma-name").textContent==="王德生","显示服务端返回的名录名");
      const ss=JSON.parse(w.sessionStorage.getItem("sde_gauth")||"null");
      const ls=JSON.parse(w.localStorage.getItem("sde_talk_id")||"null");
      ok(ss&&ss.cred==="sdepw1:right:王德生"&&ss.exp>Date.now(),"sessionStorage sde_gauth 已写（与社区共用）");
      ok(ls&&ls.cred===ss.cred,"localStorage sde_talk_id 副本已写（跨标签页）");
      ok($("ma-pw-code").value==="","密码框已清空");
      console.log("⑥ 带名字进教室");
      w.__opened="";w.joinRoom("SDE-Universes-Classroom");
      ok(String(w.__opened).indexOf("meet.jit.si")>-1,"放行到 jitsi");
      ok(decodeURIComponent(String(w.__opened)).indexOf("王德生")>-1,"URL 带上社区名字作 displayName");
      console.log("⑦ 退出");
      $("ma-signout").click();
      ok(!w.sessionStorage.getItem("sde_gauth")&&!w.localStorage.getItem("sde_talk_id"),"两处身份都清掉");
      ok(w.SDE_MEET_NAME===""&&$("ma-pw").style.display==="flex","回到未登录态");
      console.log("⑧ 跨标签页回填");
      w.localStorage.setItem("sde_talk_id",JSON.stringify({cred:"sdepw1:right:胡敏",name:"胡敏",exp:Date.now()+3600000}));
      w.dispatchEvent(new w.Event("focus"));
      setTimeout(()=>{
        ok(w.SDE_MEET_NAME==="胡敏","从 localStorage 副本回填成功");
        ok(!!w.sessionStorage.getItem("sde_gauth"),"并写回 sessionStorage");
        console.log("\n"+(fail?"FAIL "+fail:"全部通过")+" | pass="+pass+" fail="+fail);
        process.exit(fail?1:0);
      },60);
    },80);
  },80);
},400);
