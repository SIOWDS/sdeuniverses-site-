/* /meeting/ 参加会议模拟：名字 ＋ 会议号。跑法：node tools/sim_meeting_namejoin.js */
const fs=require("fs");
const {JSDOM}=require("/home/claude/simenv/node_modules/jsdom");
const html=fs.readFileSync(__dirname+"/../public/meeting/index.html","utf8");
let pass=0,fail=0;
function ok(c,m){c?(pass++,console.log("  ✓ "+m)):(fail++,console.log("  ✗ "+m));}
function mk(pre){
  const dom=new JSDOM(html,{runScripts:"dangerously",url:"https://sdeuniverses.com/meeting/",pretendToBeVisual:true,
    beforeParse(w){ if(pre)try{pre(w)}catch(e){console.log("pre err",e.message)} }});
  const w=dom.window;
  w.fetch=function(u){
    if(String(u).indexOf("roster.json")>-1)return Promise.resolve({json:()=>Promise.resolve({students:[{name:"王德生"},{name:"胡敏"}]})});
    return Promise.resolve({json:()=>Promise.resolve({})});
  };
  w.alert=function(t){w.__alert=t};
  w.Element.prototype.scrollIntoView=function(){};   // jsdom 无此实现
  w.open=function(u){w.__opened=u;return null};
  return w;
}
const A=mk();
setTimeout(()=>{
  const d=A.document,$=id=>d.getElementById(id);
  console.log("① 结构");
  ok(!!$("joinName")&&!!$("meetCode"),"名字框与会议号框都在同一行");
  ok(!$("ma-pw-code"),"密码框已撤掉");
  ok($("ma-in").style.display!=="none","没名字时显示「名字＋会议号」说明");
  ok(A.SDE_MEET_NAME==="","初始无名字");

  console.log("② 只填会议号 → 拦下并指到名字框");
  $("meetCode").value="SDE-Group-3";$("joinName").value="";
  A.joinByCode();
  ok(!A.__opened,"没名字不放行");
  ok($("join-msg").textContent.indexOf("名字")>-1,"提示补名字");
  ok(d.activeElement===$("joinName"),"光标落到名字框");

  console.log("③ 只填名字 → 提示补会议号");
  $("joinName").value="王德生";$("joinName").dispatchEvent(new A.Event("input"));
  $("meetCode").value="";A.joinByCode();
  ok(!A.__opened,"没会议号不放行");
  ok($("join-msg").textContent.indexOf("会议号")>-1,"提示补会议号");
  ok($("ma-name").textContent==="王德生","顶部身份条实时跟着名字框走");

  console.log("④ 名字＋会议号 → 直接进视频教室");
  $("meetCode").value="SDE-Group-3";A.joinByCode();
  ok(String(A.__opened).indexOf("meet.jit.si")>-1,"打开 jitsi 教室");
  ok(decodeURIComponent(String(A.__opened)).indexOf("王德生")>-1,"URL 带上名字作 displayName");
  ok(decodeURIComponent(String(A.__opened)).toLowerCase().indexOf("sde-group-3")>-1,"房间号正确（canonicalRoom 会统一转小写）");
  ok(A.localStorage.getItem("sde_meet_name")==="王德生","名字已记在本机");

  console.log("⑤ 会议列表按钮：名字已在，直接进");
  A.__opened="";A.joinRoom("SDE-Universes-Classroom");
  ok(String(A.__opened).toLowerCase().indexOf("sde-universes-classroom")>-1,"进入教室按钮放行");

  console.log("⑥ 数字号走 Zoom");
  A.__opened="";$("meetCode").value="123 4567 8901";A.joinByCode();
  ok(String(A.__opened).indexOf("zoom.us/j/12345678901")>-1,"9–11 位数字号转 Zoom");

  console.log("⑦ 回车键");
  A.__opened="";$("joinName").value="胡敏";$("meetCode").value="";
  $("joinName").dispatchEvent(new A.KeyboardEvent("keydown",{key:"Enter"}));
  ok(d.activeElement===$("meetCode"),"名字框回车跳到会议号框");
  $("meetCode").value="SDE-Group-1";
  $("meetCode").dispatchEvent(new A.KeyboardEvent("keydown",{key:"Enter"}));
  ok(String(A.__opened).toLowerCase().indexOf("sde-group-1")>-1,"会议号框回车即进");

  console.log("⑧ 换个名字");
  $("ma-signout").click();
  ok(!A.localStorage.getItem("sde_meet_name"),"本机记的名字已清");
  ok($("joinName").value===""&&A.SDE_MEET_NAME==="","名字框清空、身份条回到提示态");

  console.log("⑨ 下次再来：本机记住的名字自动带出");
  const B=mk(w=>w.localStorage.setItem("sde_meet_name","胡敏"));
  setTimeout(()=>{
    const $b=id=>B.document.getElementById(id);
    ok($b("joinName").value==="胡敏","名字框已自动填好");
    ok(B.SDE_MEET_NAME==="胡敏","只需再填会议号即可进入");
    B.__opened="";$b("meetCode").value="SDE-QA-Room";B.joinByCode();
    ok(String(B.__opened).toLowerCase().indexOf("sde-qa-room")>-1,"只填会议号就进去了");

    console.log("⑩ 社区已登录过的人：名字直接带出");
    const C=mk(w=>w.localStorage.setItem("sde_talk_id",JSON.stringify({cred:"sdepw1:x:王德生",name:"王德生",exp:Date.now()+3600000})));
    setTimeout(()=>{
      ok(C.document.getElementById("joinName").value==="王德生","从社区身份带出名字");
      console.log("\n"+(fail?"FAIL "+fail:"全部通过")+" | pass="+pass+" fail="+fail);
      process.exit(fail?1:0);
    },350);
  },350);
},350);
