# SDE 结构化知识库 · 九库模式 (v1)

> 从「文章库(相似句检索)」升级为「知识图谱(调用知识)」。
> 九库不是九个搜索索引,是一张互相指向的图。检索 = 定位实体 → 取其邻域子图。
> 库文件在 `public/kb/`,worker 像 loadCorpus 一样 fetch+缓存;实体回链到 manifest.docs 的文档下标。

## 通用实体结构
每条实体统一字段:
```
{
  "id":      "c.show",              // 类型前缀 + slug,全库唯一,[[链接]]与检索都靠它
  "type":    "concept",            // 九类之一
  "name":    "显露 (Show / S)",     // 规范名
  "aliases": ["S维度","显露态","Show"],  // 别名(entity-linking 用)
  "def":     "存在在一定条件下被看见、被维持、被识别的方式;S≠结构,是结构的显露连续谱。", // 一句话
  "body":    "...",                // 可选,较长说明(检索命中时可注入)
  "links":   { "theory":["t.three-eq"], "proposition":["p.s-not-structure"], "scholar":["s.wds"] },
  "sources": [12, 47, 203],        // manifest.docs 下标(rule-mine 回链)
  "coord":   ["s","e1"],           // 可选 SDE 27格坐标
  "seed":    "canon"               // canon=先验权威 / mined=语料挖掘(Phase B)
}
```

## 九库 (`<type>` → 文件)
| 库 | type | 文件 | 装什么 | 种子来源 |
|---|---|---|---|---|
| 概念库 | concept | concepts.json | 每个具名概念:定义+坐标+所属理论+关联概念 | canon 脊梁 + Phase B 挖掘 |
| 命题库 | proposition | propositions.json | 原子判断/断言/否定/批判,连接概念 | canon 若干 + Phase B 主挖 |
| 理论库 | theory | theories.json | 较大理论结构(三大方程/123/六路径/意义三律…) | canon 脊梁 |
| 证据库 | evidence | evidence.json | 支撑材料:实证、跨基底数据、史学镜像、科学事实 | canon 若干 + Phase B |
| 案例库 | case | cases.json | 已做的应用(肺癌发生学、各家解构、慢病/婚姻/几何…) | canon 若干 + Phase B |
| 方法库 | method | methods.json | 可操作流程(四步法/六步法/改姓爪/母题打造/九步制造…) | canon 脊梁 |
| 学者库 | scholar | scholars.json | 王德生 + 被解构/对话的思想家,附其核心概念与被批判点 | canon 脊梁 |
| 争议库 | controversy | controversies.json | 争点:SDE 对某家的批判、家与家之争、开放问题、SDE 立场 | canon 脊梁 |
| 版本库 | version | versions.json | 版本轨迹:先验版本、定名改姓、理论演化、专著版次 | canon 脊梁 |

## 关系图(检索时展开的邻域)
```
concept ──defines──▶ proposition ──belongs──▶ theory
   │                     │                        │
   │                  supported-by             produced-by
   ▼                     ▼                        ▼
 scholar ◀─attributed── evidence     case ──demonstrates──▶ method
   │                                   │
 critiqued-in ──▶ controversy      tracked-in ──▶ version
```

## 检索侧产物(worker 加载)
- `kb-index.json` : `{ "别名lower": ["type","id"], ... }` — 查询→实体的 O(1) 链接表(小、常驻缓存)
- `kb-manifest.json` : 各库计数 + built 时间戳 + 回链统计,供自检与前端展示

## 铁律
1. **KB 是引擎侧内部资料,可带 SDE 术语**;但智能体对用户的**产出**仍走 WDS_CHAT_SYS/改姓爪,库内术语不得原样吐给读者。
2. 回链用**规范名+精选别名**匹配,长度≥2、取区分性强的串;单字触发词禁用(参见 build_search_index 的「转移」血案)。
3. 某实体命中 >60% 文档 = 低区分度,记录但标 `warn:lowdisc`,不给它加检索权重。
4. Phase B 挖掘产物 `seed:"mined"`,与 canon 脊梁合并进同一文件,不覆盖脊梁。
5. 坐标/回链随语料重建同跑(doc 下标会因新文顶位而漂移,参见 sde-coords.json 陷阱)。
