#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""补三处深挖模拟查出来的真缺口。

① **「编辑产物」改成文格不回写终稿**（forge 与 confluence 同病）：
   三处红字都写着"用「编辑产物」手改掉术语残留""或用「编辑产物」自行补全"，
   而 edit 只写 ST.out[id]，ST.article 原样不动 —— 交出去的 Word / 发布包 / 横幅
   用的还是没改过的那一版。**照着提示做，做了等于没做**，且没有任何迹象告诉他。
② 打磨格重跑会把输出框越堆越多（每跑一次多插一个 .out）。
③ 成文重跑之后 ST.polished 还留着 true，交付横幅会谎称"已打磨"。

用法：python3 tools/patch_edit_writeback.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FORGE = os.path.join(ROOT, "tools", "forge", "forge.template.html")
CONF = os.path.join(ROOT, "tools", "confluence", "confluence.template.html")

OLD_EDIT = """      if(p.editing){ ST.out[id] = p.ta.value; p.out.textContent = ST.out[id]; p.editing=false; p.ta.remove(); b.textContent='编辑产物'; }"""

NEW_EDIT = """      if(p.editing){
        ST.out[id] = p.ta.value; p.out.textContent = ST.out[id]; p.editing=false; p.ta.remove(); b.textContent='编辑产物';
        /* 成文格的产物就是终稿本身——只写 ST.out.write 而不回写 ST.article，
           交出去的 Word／发布包用的仍是没改过的那一版，而红字偏偏一直在劝人
           「用编辑产物手改」。照着做了等于没做，且没有任何迹象告诉他。 */
        if(id==='write'){
          ST.article = ST.out.write;
          const wc = ST.article.replace(/\\s/g,'').length;
          const t = termHits(ST.article), tr = traceHits(ST.article), hs = t.concat(tr);
          ST.termFix = hs.length ? hs : null;
          setStat('write', '✓ '+wc+' 字（手改）'+(hs.length ? ('　⚠ 仍有残留：'+hs.join('、')) : '　术语零残留 · 无工艺痕迹'), 'done');
        }
      }"""


def patch(path, name, extra=False):
    h = open(path, encoding="utf-8").read()
    assert h.count(OLD_EDIT) == 1, "%s：找不到 edit 存回那一段" % name
    h = h.replace(OLD_EDIT, NEW_EDIT, 1)

    if extra:
        # ② 打磨格重跑：先清掉上一次插的那个框，再插新的
        old = ("  const box = document.createElement('div'); box.className='out'; box.style.marginTop='8px';\n"
               "  p.out.parentNode.insertBefore(box, p.out.nextSibling);")
        assert h.count(old) == 1, "找不到打磨格插框那一段"
        h = h.replace(old,
                      "  p.el.querySelectorAll('.out').forEach((el,i)=>{ if(i>0) el.remove(); });   // 重跑不叠框\n"
                      "  const box = document.createElement('div'); box.className='out'; box.style.marginTop='8px';\n"
                      "  p.out.parentNode.insertBefore(box, p.out.nextSibling);", 1)

        # ③ 重新写过就不算打磨过
        old2 = ("async function doWrite(){\n  const id='write', p=panels[id];\n  openStage(id);")
        assert h.count(old2) == 1, "找不到 doWrite 开头"
        h = h.replace(old2, old2 + "\n  ST.polished = false;   // 重新写过就不算打磨过，别让横幅谎称已打磨", 1)

        # 打磨成功后，成文格显示的也要换成终稿（一份正文只该有一个当家的）
        old3 = "  ST.article = txt;\n  ST.out.write = txt;\n  ST.polished = true;"
        assert h.count(old3) == 1, "找不到打磨采用稿那一段"
        h = h.replace(old3,
                      "  ST.article = txt;\n  ST.out.write = txt;\n  ST.polished = true;\n"
                      "  // 正文只认一个当家的：成文格的显示与产物一并换成终稿，\n"
                      "  // 否则「编辑产物」打开的是终稿、面板上却还印着初稿。\n"
                      "  try{ panels.write.out.textContent = txt; }catch(e){ }", 1)

    open(path, "w", encoding="utf-8").write(h)
    print("patched:", name)


def main():
    patch(FORGE, "forge.template.html")
    patch(CONF, "confluence.template.html", extra=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
