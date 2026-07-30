#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
涌现档前端三处修复（2026-07-30，配合 patch_ask_stream_first.py）

① 平台级 503 会把 Cloudflare 那张 HTML 错误页整块塞进错误消息里，读者只看到一堆标签
   （「HTTP 503 <!DOCTYPE html> <!--[if lt IE 7]>…」）。加 errText() 把它翻成一句人话。
② 三路碰撞与三次盲评的失败原本被彻底吞掉（catch 是空的、p.total=0），
   屏幕上只剩一个 ✗，背后其实可能死了好几次。现在逐条记名、显示在候选典范上方。
③ 综合提炼（synth）是整条链上唯一没有重试的一环，而它恰恰跑在最后、最贵、最容易撞上限。
   给它一次自动重试（成文那边 paperHalf 早就有）。

用法：python3 tools/patch_emerge_errors.py [--apply]
"""
import io, sys

P = "public/search/index.html"
h = io.open(P, encoding="utf-8").read()
orig = h
n = 0


def rep(old, new, cnt=1):
    global h, n
    assert h.count(old) == cnt, "锚点命中 %d 次（应为 %d）：%r" % (h.count(old), cnt, old[:90])
    h = h.replace(old, new, cnt)
    n += 1


# ── ① errText：把平台错误页翻成人话 ──
rep(
    "/* 一台通用的 SSE 收集器：碰撞、盲评、综合提炼三环共用，不再各写一份 pump */",
    """/* 出错原因要能读，才谈得上让人决定重试。平台把调用按资源上限掐掉时返回的是 Cloudflare
   自己的 HTML 错误页，整页塞进 message 里，读者只看见一串标签——那不叫报错，那叫失踪。 */
function errText(e){
  var m=String((e&&e.message)||e||'');
  if(/^HTTP 503/.test(m)) return '服务端 503（平台资源上限——通常是同一分钟里连打太多次重活）。等十几秒再点一次即可。';
  if(/^HTTP 5\\d\\d/.test(m)) return '服务端 '+m.slice(5,8)+'，请稍后重试。';
  if(/^HTTP 4\\d\\d/.test(m)) return '请求被拒（'+m.slice(5,8)+'）：'+m.slice(9).replace(/<[^>]*>/g,' ').replace(/\\s+/g,' ').slice(0,120);
  return m.replace(/<[^>]*>/g,' ').replace(/\\s+/g,' ').slice(0,180);
}
/* 一台通用的 SSE 收集器：碰撞、盲评、综合提炼三环共用，不再各写一份 pump */""",
)

# ── sseCollect 转发服务端的进度提示（出流护栏加了 status 事件，前端得接住） ──
rep(
    """            if(j.t==='token'){ acc+=j.v; if(onStat) onStat(acc.length,false); }
            else if(j.t==='think'){ if(onStat) onStat(acc.length,true); }""",
    """            if(j.t==='token'){ acc+=j.v; if(onStat) onStat(acc.length,false); }
            else if(j.t==='think'){ if(onStat) onStat(acc.length,true); }
            /* 服务端「先出流再干活」之后，检索/装内功那十几秒里会先发 status——接住它，
               否则读者盯着一条不动的状态行，以为死了。 */
            else if(j.t==='status'){ if(onStat) onStat(acc.length,false,j.v); }""",
)

# ── ② 失败逐条记名 ──
rep(
    "var emerging=false, emergeUsed=[], paradigms=[];",
    "var emerging=false, emergeUsed=[], paradigms=[], emergeFails=[];",
)

rep(
    """function renderParadigms(sel){
  var o='';""",
    """function renderParadigms(sel){
  var o='';
  /* 失败也是现场的一部分：哪一路死了、死于什么，必须留在页面上——
     否则三路里死两路，读者只看见"少了两张卡"，以为本来就该是一张。 */
  if(emergeFails.length){
    o+='<div style="border:1px solid #C08A5E;border-radius:11px;padding:10px 13px;margin-bottom:10px;background:var(--card);font-size:0.78rem;color:var(--text2);line-height:1.7">'
      +'<b style="color:#A85B2B">本次有 '+emergeFails.length+' 处未跑通</b><br>'+emergeFails.map(esc).join('<br>')+'</div>';
  }""",
)

rep(
    """      +(p.verdict?'<div style="font-size:0.77rem;color:var(--text2);line-height:1.65;margin-top:6px">'+esc(String(p.verdict).slice(0,240))+'</div>':'')""",
    """      +(p.verdict?'<div style="font-size:0.77rem;color:var(--text2);line-height:1.65;margin-top:6px">'+esc(String(p.verdict).slice(0,240))+'</div>':'')
      +(p.err?'<div style="font-size:0.75rem;color:#A85B2B;margin-top:6px">创新检查未完成：'+esc(p.err)+'（本卡按 0 分参与择优）</div>':'')""",
)

rep(
    """  emerging=true;
  var btn=document.getElementById('btnEmerge'); btn.disabled=true;""",
    """  emerging=true;
  emergeFails=[];
  var btn=document.getElementById('btnEmerge'); btn.disabled=true;""",
)

rep(
    """      return sseCollect({mode:'collide',q:oq,origin:oq,views:vt,way:w},function(n,think){
        stat.textContent=(think?'🧠 ':'🌀 ')+'第 '+(ix+1)+'/3 路碰撞（'+wayName(w)+'）'+(think?'·深度思考中':'·已产出 '+n+' 字')+'…';
      }).then(function(t){
        t=String(t||'').trim();
        if(t.length>200){ paradigms.push({way:w,text:t}); renderParadigms(-1); }
      },function(){ /* 单路失败不拖垮另外两路 */ });""",
    """      return sseCollect({mode:'collide',q:oq,origin:oq,views:vt,way:w},function(n,think,msg){
        stat.textContent=(think?'🧠 ':'🌀 ')+'第 '+(ix+1)+'/3 路碰撞（'+wayName(w)+'）'
          +(msg?'·'+msg:(think?'·深度思考中':'·已产出 '+n+' 字'))+'…';
      }).then(function(t){
        t=String(t||'').trim();
        if(t.length>200){ paradigms.push({way:w,text:t}); renderParadigms(-1); }
        else { emergeFails.push('第 '+(ix+1)+' 路（'+wayName(w)+'）产出过短（'+t.length+' 字），已弃'); renderParadigms(-1); }
      },function(err){
        /* 单路失败不拖垮另外两路——但也不再吞掉。吞掉的后果是屏幕上只剩一个 ✗，
           而那个 ✗ 出自最后一环，读者以为是提炼坏了，其实前面已经死了两路。 */
        emergeFails.push('第 '+(ix+1)+' 路（'+wayName(w)+'）失败：'+errText(err));
        renderParadigms(-1);
      });""",
)

rep(
    """        return sseCollect({mode:'iq',q:oq,text:p.text},function(n){
          stat.textContent='🎯 创新检查 '+(ix+1)+'/'+paradigms.length+'…（'+n+' 字）';
        }).then(function(raw){""",
    """        return sseCollect({mode:'iq',q:oq,text:p.text},function(n,think,msg){
          stat.textContent='🎯 创新检查 '+(ix+1)+'/'+paradigms.length+(msg?'…'+msg:'…（'+n+' 字）');
        }).then(function(raw){""",
)

rep(
    """          }catch(e){ p.total=0; }
          renderParadigms(-1);
        },function(){ p.total=0; });""",
    """          }catch(e){ p.total=0; p.err='评分卡解析失败（基底没按 JSON 交卷）'; }
          renderParadigms(-1);
        },function(err){ p.total=0; p.err=errText(err); renderParadigms(-1); });""",
)

# ── ③ 综合提炼：一次自动重试 ──
rep(
    """    return sseCollect({mode:'synth',q:oq,origin:oq,hist:buildHist(true),winner:paradigms[best].text,others:others,cards:cards},
      function(n,think){ if(!think) bstat.textContent='🧬 最终综合提炼中…（'+n+' 字）'; })
      .then(function(t){""",
    """    /* 综合提炼是整条链上最后、最贵的一环，此前也是唯一没有重试的一环：它一挂，
       前面十几次调用（十轮问对＋三路碰撞＋三次盲评）就全白跑。给它一次自动重试。 */
    var synthOnce=function(attempt){
      return sseCollect({mode:'synth',q:oq,origin:oq,hist:buildHist(true),winner:paradigms[best].text,others:others,cards:cards},
        function(n,think,msg){ if(!think) bstat.textContent='🧬 最终综合提炼中'+(attempt>1?'（第 '+attempt+' 次尝试）':'')+(msg?'·'+msg:'…（'+n+' 字）'); })
        .catch(function(err){
          if(attempt>=2) throw err;
          bstat.textContent='… 综合提炼出错（'+errText(err)+'）正在重试…';
          return new Promise(function(r){ setTimeout(r,4000); }).then(function(){ return synthOnce(attempt+1); });
        });
    };
    return synthOnce(1)
      .then(function(t){""",
)

# ── 收尾的错误显示：一律走 errText ──
rep(
    """  }).catch(function(e){
    stat.textContent='✗ '+(e.message||String(e));
  }).finally(function(){ emerging=false; btn.disabled=false; });""",
    """  }).catch(function(e){
    stat.textContent='✗ '+errText(e);
    renderParadigms(paradigms.length?0:-1);
  }).finally(function(){ emerging=false; btn.disabled=false; });""",
)

rep(
    """  }).catch(function(e){
    box.className='ans';
    stat.textContent='✗ 提炼失败：'+(e.message||String(e));""",
    """  }).catch(function(e){
    box.className='ans';
    stat.textContent='✗ 提炼失败：'+errText(e);""",
)

rep(
    "  briefKind='distill'; paradigms=[]; emergeUsed=[];",
    "  briefKind='distill'; paradigms=[]; emergeUsed=[]; emergeFails=[];",
)

print("patched %d anchors, %d -> %d bytes" % (n, len(orig), len(h)))
if "--apply" in sys.argv:
    io.open(P, "w", encoding="utf-8").write(h)
    print("written:", P)
else:
    print("(dry run; 加 --apply 才写盘)")
