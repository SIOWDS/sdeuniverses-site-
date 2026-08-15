#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ChatSDE「一轮回空」的两处修补（幂等，可重复跑）

背景（2026-08-15 用户交来一份导出的对话 PDF）：连着三轮回空——
  ① 一轮写着「只想、没写（已思考 4273 字）」＝思考把 max_tokens 吃光；
  ② 两轮写着「连思考也没有」＝流被中途切断，页面分不出是谁断的。
而导出的 PDF 只取 .wdsm-a，服务端所有 note（含「正在关掉思考重答一次…」）
**在导出稿里全部丢失** ⇒ 事后无从判断到底走到哪一步死的。

两处改动：
 A. src/worker.js —— 思考额度看门狗：思考吃掉六成预算而正文仍 0 字，
    就地掐掉这一遍、直接进「关思考重答」，不再白等它撞线（那一两分钟正是
    流被平台掐死的窗口；isolate 资源上限共享，掐断时连 error 都发不出）。
 B. public/wds-mode.js —— 空答分三种死法说话，且诊断行写进 .wdsm-a
    （只有写在正文里，导出 PDF 才带得走 ＝ 下次能拿到证据）。
"""
import re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
W = ROOT / "src" / "worker.js"
M = ROOT / "public" / "wds-mode.js"
changed = []


def sub1(text, old, new, tag):
    """严格一处替换；已改过则跳过。"""
    if new in text:
        print("  · 已在位，跳过：" + tag)
        return text, False
    n = text.count(old)
    assert n == 1, "锚点 %s 命中 %d 次（要求 1）" % (tag, n)
    print("  ✎ " + tag)
    changed.append(tag)
    return text.replace(old, new), True


# ── A. worker：思考额度看门狗 ────────────────────────────────────────────
w = W.read_text(encoding="utf-8")

A1_OLD = """            const _cd = { lines: 0, finish: "", head: "", usage: null, err: false, status: upstream.status };
"""
A1_NEW = """            const _cd = { lines: 0, finish: "", head: "", usage: null, err: false, status: upstream.status, cutThink: 0 };
            /* 【思考额度看门狗】思考与正文吃同一份 max_tokens。等它把额度想光再兜底，
               要白等一两分钟——而那一两分钟正是流被平台无声掐死的窗口（isolate 的资源
               上限是共享的，掐断时连 error 都发不出，页面只看到「什么都没有」）。
               所以不等它撞线：思考吃掉六成、正文仍一个字没有，就地掐掉这一遍，直接走
               下面那一遍关思考的。
               ⚠ 线不是拍一个百分比——**判据是「剩下的额度还够不够写一段答」**：一段像样的
               回答约 1000 汉字（约 600 token）⇒ 留 1200 token 的余量，其余都可以拿去想。
               按百分比给（0.6）会在标准档 2600 这种小预算上过早开刀。 */
            /* ⚠ 单位换算是这条线的命门：**思考字数 ≠ token 数**。2026-08-15 真跑实测
               deepseek-v4-flash 的中文推理 **1 token ≈ 1.7 汉字**（1673 字/972 tok、123 字/76 tok）。
               按 1:1 拿字数去比预算，等于把闸门定在真实用量的六成上——第一版 `tokWant-1500`
               在标准档就把一次本来写得出来的回答掐了（真跑：想了 1101 字＝约 640 tok、
               预算 2600 还剩三分之二，却已被判"想光了"）。 */
            const _thinkCap = Math.round(Math.max(1000, tokWant - 1200) * 1.7);
"""
w, _ = sub1(w, A1_OLD, A1_NEW, "worker: _cd 加 cutThink ＋ 思考额度线 _thinkCap")

A2_OLD = """                if (d.content) { clk.firstFrame(); if (_st) _st.out += d.content.length; outText += d.content; controller.enqueue(_sseBytes({ t: "token", v: d.content })); }
              }
            }
            } catch (e) {"""
A2_NEW = """                if (d.content) { clk.firstFrame(); if (_st) _st.out += d.content.length; outText += d.content; controller.enqueue(_sseBytes({ t: "token", v: d.content })); }
                if (!outText && _st && _st.think > _thinkCap) { _cd.cutThink = _st.think; break; }
              }
              if (_cd.cutThink) { try { await reader.cancel(); } catch (e0) {} break; }
            }
            } catch (e) {"""
w, _ = sub1(w, A2_OLD, A2_NEW, "worker: 读流循环里掐断只想不写的那一遍")

A3_OLD = """              controller.enqueue(_sseBytes({ t: "note", v: "这一答只出了思考、正文 0 字，正在关掉思考重答一次…" }));"""
A3_NEW = """              controller.enqueue(_sseBytes({ t: "note", v: _cd.cutThink
                ? ("这一答已经想了 " + _cd.cutThink + " 字、正文还是 0 字——不等它想完了，现在关掉思考重答一次…")
                : "这一答只出了思考、正文 0 字，正在关掉思考重答一次…" }));"""
w, _ = sub1(w, A3_OLD, A3_NEW, "worker: 兜底那一句区分「撞线」与「被看门狗掐断」")

A4_OLD = """                + (_cd.head ? (" · 首帧「" + _cd.head.replace(/\\s+/g, " ").slice(0, 80) + "」") : "");"""
A4_NEW = """                + (_cd.cutThink ? (" · 思考过线被掐（线 " + _thinkCap + "）") : "")
                + (_cd.head ? (" · 首帧「" + _cd.head.replace(/\\s+/g, " ").slice(0, 80) + "」") : "");"""
w, _ = sub1(w, A4_OLD, A4_NEW, "worker: 诊断串写明是否被看门狗掐断")

W.write_text(w, encoding="utf-8")

# ── B. wds-mode：空答三分诊断，且写进正文 ───────────────────────────────
m = M.read_text(encoding="utf-8")

B1_OLD = """      errDead: "连接像是断了（也许想太久被中间层切了）。稍后再问，你这句我记着。","""
B1_NEW = """      errCut: "这一轮没走完就断了——不是基底没写，是整个请求在半路被平台掐断（服务端连一句错都来不及说）。点「重答」再来一次；老是这样就把顶部切到「标准」档，或新开一场。",
      errDead: "连接像是断了（也许想太久被中间层切了）。稍后再问，你这句我记着。","""
m, _ = sub1(m, B1_OLD, B1_NEW, "wds-mode: 中文加 errCut")

B2_OLD = """      errDead: "The connection dropped — it may have thought too long and been cut. Try again in a moment; your question is still here.","""
B2_NEW = """      errCut: "This turn was cut off mid-flight — the model isn't silent, the stream was severed (most likely the server was killed by the platform, so it never got to report an error). Hit Retry; if it keeps happening, switch the top mode to Standard or start a fresh session.",
      errDead: "The connection dropped — it may have thought too long and been cut. Try again in a moment; your question is still here.","""
m, _ = sub1(m, B2_OLD, B2_NEW, "wds-mode: 英文加 errCut")

B3_OLD = """      qFull: "队列最多 10 条", qNext: "下一句：","""
B3_NEW = """      qFull: "队列最多 10 条", qNext: "下一句：",
      dgLine: "〔诊断〕第 {sec} 秒 · 收到 {fr} 帧 · 思考 {th} 字 · {st}{end}",
      dgAt1: "最后停在「", dgAt2: "」 · ", dgOk: "流正常收尾", dgCut: "流被截断（没收到收尾标记）","""
m, _ = sub1(m, B3_OLD, B3_NEW, "wds-mode: 中文加诊断词条")

B4_OLD = """      qFull: "10 queued messages max", qNext: "Next: ","""
B4_NEW = """      qFull: "10 queued messages max", qNext: "Next: ",
      dgLine: "[diag] cut at {sec}s · {fr} frames · {th} chars of reasoning · {st}{end}",
      dgAt1: "last stage \\u201c", dgAt2: "\\u201d · ", dgOk: "stream closed normally", dgCut: "stream was cut (no end marker)","""
m, _ = sub1(m, B4_OLD, B4_NEW, "wds-mode: 英文加诊断词条")

B5_OLD = """    var wd = null, timedOut = false;   // 存活看门狗:靠心跳字节喂,45s 无字节判定连接已死
"""
B5_NEW = """    var wd = null, timedOut = false;   // 存活看门狗:靠心跳字节喂,45s 无字节判定连接已死
    /* 空答取证：三种死法（思考吃光额度／流被中途切断／上游报错）走的下一步完全不同，
       混成一句「没生出来」等于什么都没说。这四个读数是**客户端唯一还留得住的证据**——
       服务端 note 挂在 cell.turn 上，导出 PDF 只取 .wdsm-a，一导出全丢。 */
    var tStart = Date.now(), frames = 0, sawDone = false, lastBeat = null;
"""
m, _ = sub1(m, B5_OLD, B5_NEW, "wds-mode: send() 里加四个取证读数")

B6_OLD = """    function endUI() {"""
B6_NEW = """    /* 诊断行**贴进 .wdsm-a**（不是 cell.turn）：只有写在正文里，导出 PDF 才带得走。
       上一次排障就是栽在这儿——用户交来的导出稿里一条服务端 note 都没有。 */
    function emptyDiag() {
      var st = (lastBeat && lastBeat.stage) ? (t("dgAt1") + lastBeat.stage + t("dgAt2")) : "";
      var d = el("div", null, tx("dgLine", {
        sec: (lastBeat && lastBeat.sec) || Math.round((Date.now() - tStart) / 1000), fr: frames,
        th: thinkTxt.length, st: st, end: sawDone ? t("dgOk") : t("dgCut"),
      }));
      d.style.cssText = "color:#8B7B5E;font-size:12px;line-height:1.6;margin:10px 0 0";
      cell.a.appendChild(d);
    }
    function endUI() {"""
m, _ = sub1(m, B6_OLD, B6_NEW, "wds-mode: 加 emptyDiag()")

B7_OLD = """          } else if (timedOut) {
            cell.a.className = "wdsm-a plain wdsm-err";
            cell.a.textContent = t("errDead");
          } else if (stoppedByUser) {"""
B7_NEW = """          } else if (timedOut) {
            cell.a.className = "wdsm-a plain wdsm-err";
            cell.a.textContent = t("errDead");
            emptyDiag();
          } else if (stoppedByUser) {"""
m, _ = sub1(m, B7_OLD, B7_NEW, "wds-mode: 连接判死那一支也留诊断")

B8_OLD = """            cell.a.className = "wdsm-a plain wdsm-err";
            cell.a.textContent = thinkTxt ? (t("errEmpty") + thinkTxt.length + t("errEmptyEnd")) : t("errEmptyNo");
            var rrow = el("div", null, "");"""
B8_NEW = """            cell.a.className = "wdsm-a plain wdsm-err";
            /* 分三种死法说话。**没收到 [DONE] ＝ 流被截断**，这时候说「基底把额度想光了」
               是冤枉它：服务端可能早就写完了，是这条流没送到。 */
            cell.a.textContent = !sawDone
              ? t("errCut")
              : (thinkTxt ? (t("errEmpty") + thinkTxt.length + t("errEmptyEnd")) : t("errEmptyNo"));
            emptyDiag();
            var rrow = el("div", null, "");"""
m, _ = sub1(m, B8_OLD, B8_NEW, "wds-mode: 空答分三种死法")

B9_OLD = """              if (p === "[DONE]") return finish();
              var j; try { j = JSON.parse(p); } catch (e) { continue; }"""
B9_NEW = """              if (p === "[DONE]") { sawDone = true; return finish(); }
              var j; try { j = JSON.parse(p); } catch (e) { continue; }
              frames++;"""
m, _ = sub1(m, B9_OLD, B9_NEW, "wds-mode: 记下 [DONE] 与帧数")

B10_OLD = """                if (!answer && cell.think) cell.thinkL.textContent = t("thinking") + " " + (bv.sec || 0) + "s · " + (bv.think || 0) + (bv.stage ? " · " + bv.stage : "");"""
B10_NEW = """                lastBeat = bv;                                   // 最后一次心跳报的阶段＝死在哪一步的唯一线索
                if (!answer && cell.think) cell.thinkL.textContent = t("thinking") + " " + (bv.sec || 0) + "s · " + (bv.think || 0) + (bv.stage ? " · " + bv.stage : "");"""
m, _ = sub1(m, B10_OLD, B10_NEW, "wds-mode: 记下最后一次心跳的阶段")

M.write_text(m, encoding="utf-8")
print("\n改了 %d 处" % len(changed))
