/* 扩到近二十年的护栏：只检查**已扩过**的面板，未扩的跳过（分批推进中）。
 * 五条：两条幕线俱全／新幕用甲乙丙丁不与既有一二三冲突／有跨二十年那一节／
 *       meta 与尾块口径都已改／既有正文一个字没被动（凭「一、」开头那节仍在）。 */
import fs from "node:fs"; import path from "node:path";
const FR = new URL("../public/frontier/", import.meta.url).pathname;
let pass=0, fail=0, done=0, todo=0;
const ok=(n,c)=>{ if(c) pass++; else { fail++; console.log("  ✗ "+n); } };
for (const d of fs.readdirSync(FR)) {
  const p = path.join(FR, d, "index.html");
  if (!fs.existsSync(p)) continue;
  const t = fs.readFileSync(p, "utf8");
  if (t.indexOf('class="era"') < 0) { todo++; continue; }
  done++;
  const eras = (t.match(/class="era"/g)||[]).length;
  ok(d+" 两条幕线俱全", eras === 2);
  ok(d+" 第一幕在第二幕之前", t.indexOf("上一个十年 · 约 2006")>0 && t.indexOf("上一个十年 · 约 2006") < t.indexOf("这十年 · 约 2016"));
  ok(d+" 新幕用甲乙丙丁编号", /<h2>甲、/.test(t) && /<h2>乙、/.test(t));
  ok(d+" 既有正文未被重编号", /<h2>一、/.test(t) && /<h2>七、|<h2>六、/.test(t));
  ok(d+" 有跨二十年那一节", t.indexOf("◎ 二十年连起来看")>0);
  ok(d+" meta 已改口径", /近二十年 · 两次转向 · 约 [0-9]+ 字/.test(t));
  ok(d+" 尾块已改口径", t.indexOf("近二十年，各主要领域的两次思想转向")>0 && t.indexOf("每领域约 2000 字")<0);
  const body = t.split("<main>").pop().replace(/<[^>]+>/g,"");
  const cj = (body.match(/[\u4e00-\u9fff]/g)||[]).length;
  ok(d+" 全页 ≥2300 汉字（原约 1700）", cj >= 2300);
}
console.log("\n已扩 "+done+" 块 / 未扩 "+todo+" 块；"+pass+" PASS / "+fail+" FAIL");
process.exit(fail?1:0);
