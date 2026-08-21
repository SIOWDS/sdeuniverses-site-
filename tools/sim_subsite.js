// 复现 worker.js 11296 附近的分站分流逻辑（与源码逐字一致的那两行）
const SUBSITES = { health: "/sites/health", lang: "/sites/lang" };
const EXIST = new Set(["/sites/lang/index.html","/sites/health/index.html","/sites/health/all/index.html",
  "/index.html","/students/hu-zhiying/index.html","/books/m/62/index.html","/assets/sde-talk.js"]);
function assetExists(p){ return EXIST.has(p) || EXIST.has(p.replace(/\/$/,"/index.html")); }
function route(host, pathname){
  const subHost = host.toLowerCase();
  const subPrefix = /\.sdeuniverses\.com$/.test(subHost) ? (SUBSITES[subHost.split(".")[0]] || null) : null;
  let served=null, fellBack=false;
  if (subPrefix && pathname.indexOf(subPrefix + "/") !== 0){
    const cand = subPrefix + pathname;
    if (assetExists(cand)) served = cand;
  }
  if(!served){ served = pathname; fellBack = !!subPrefix; }
  return {served, fellBack, canonical: fellBack ? "https://sdeuniverses.com"+pathname : null};
}
const cases=[
 ["lang.sdeuniverses.com","/","/sites/lang/",false],
 ["lang.sdeuniverses.com","/students/hu-zhiying/","/students/hu-zhiying/",true],
 ["lang.sdeuniverses.com","/books/m/62/","/books/m/62/",true],
 ["lang.sdeuniverses.com","/assets/sde-talk.js","/assets/sde-talk.js",true],
 ["lang.sdeuniverses.com","/sites/lang/","/sites/lang/",true],
 ["health.sdeuniverses.com","/","/sites/health/",false],
 ["sdeuniverses.com","/","/",false],
 ["www.sdeuniverses.com","/","/",true],   // www 不在表里 → subPrefix null → 主站, fellBack false 期望
 ["evil.example.com","/","/",false],
];
let pass=0,fail=0;
for(const [h,p,want,wantFell] of cases){
  const r=route(h,p);
  const ok = r.served===want && (h.split(".")[0] in SUBSITES ? r.fellBack===wantFell : true);
  console.log((ok?"PASS":"FAIL"),h,p,"→",r.served,"fellBack="+r.fellBack);
  ok?pass++:fail++;
}
console.log("pass",pass,"fail",fail);
if(fail) process.exit(1);
