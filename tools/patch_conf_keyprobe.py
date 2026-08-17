# -*- coding: utf-8 -*-
# 学科通融机接 API Key 有效性检测（共享 sde-keyprobe.js，探测与真跑共用同一套管道函数）
import re
p = '/home/claude/site/public/taste/confluence/index.html'
s = open(p, encoding='utf-8').read()
orig = s


def rep(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:70])
    s = s.replace(old, new)


# ① 引资产（放在页尾脚本之前，与另外五台同一个 ?v= 戳）
rep("""<script src="/taste/assets/sde-handoff.js?v=20260817c"></script>""",
    """<script src="/taste/assets/sde-keyprobe.js?v=20260817c"></script>
<script>
/* Key 有效性检测：按钮由 SDEKeyProbe 注入。
   纪律（与另外五台逐字相同）：**探测与真跑共用同一套 chatHeaders / apiUrl / buildPayload / 中转**——
   探测走一条自己的路，就会出现"检测通过而真跑失败"或反过来，那比不检测更坏。
   三个 Key 都要挂：主基底那把（跑十八道工序），以及两处只用于联网检索的智谱 Key
   （C 模式一处、D 模式一处）——后两把此前无从自检，只能等取材那一格失败才知道不通。 */
(function(){
  function go(){
    if(!window.SDEKeyProbe) return;
    try{
      var hooks = {
        buildPayload: buildPayload, chatHeaders: chatHeaders, apiUrl: apiUrl,
        isOverseas: (typeof isOverseas === 'function') ? isOverseas : function(){ return false; },
        proxyUrl: (typeof PROXY_URL !== 'undefined') ? PROXY_URL : '/api/llm-proxy'
      };
      SDEKeyProbe.attach([
        { key:'apiKey', sel:'modelSel' },   /* 主基底：型号跟着下拉走 */
        { key:'cSkey',  model:'glm:flash' },/* 检索用的智谱 Key（问题驱动模式） */
        { key:'dSkey',  model:'glm:flash' } /* 检索用的智谱 Key（站外三领域模式） */
      ], hooks);
    }catch(e){ /* 检测是附加件，装不上也绝不能影响正常跑 */ }
  }
  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', go); else go();
})();
</script>
<script src="/taste/assets/sde-handoff.js?v=20260817c"></script>""")

open(p, 'w', encoding='utf-8').write(s)
print('%d → %d 字节（+%d）' % (len(orig.encode()), len(s.encode()), len(s.encode())-len(orig.encode())))
