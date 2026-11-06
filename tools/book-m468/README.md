# 第 468 号《一看就不读》出版工具链

副题：AI时代，文字里还读得出人吗——人-AI复合主体的三条成立判据　王德生 著　ISBN 979-8-90690-629-8　US$20.00　tier L0。
由第 551 号工具链改写，版式照第 220、302 号。所有命令在**仓库根目录**运行；不含任何令牌；不做 git 操作。

## 文件

| 文件 | 作用 |
|---|---|
| `meta.py` | 书号、书名、ISBN、定价、版本、题词、tier 的唯一来源 |
| `synth_full.py` | 把 `/home/claude/468-yikanjiubudu/chapters/` 合成 `src/full.md`（插入上编、中编、下编、终编四个编题），并收集〔待核〕到 `待核总表.md` |
| `convert.py` | 读 `src/full.md`，写 `front/00-前置.md`、`parts/01–04.md`、`back/12-后置.md`、`book.md`、`han.json`；序章放前置 |
| `cover.py` | 封面封底（刀工与纠缠图；墨紫底，纯色，不用渐变） |
| `build.py` | 两版 PDF（印刷 170×240、阅读 190×250）＋全文网页 |
| `make_docx.py` | 全书 Word（pandoc） |
| `publish.py` | 装进 `public/books/m/468/`、书目、站点地图、/today/ 新书卡、书号预留档 |
| `gen_config.py` + `build_unit_468.py` | 学习包（13 个单元，每章一个）与出版单元 |
| `register.py` / `agent_page.py` | 登记智能体「老周」、keypoints、智能体页 |
| `content.json` | 智能体、学习任务、承重命题、要点等文案 |
| `run_all.sh` | 一键串起来 |

## 一键重跑

```bash
B=/tmp/b468; mkdir -p $B
python3 tools/book-m468/synth_full.py
bash tools/book-m468/run_all.sh $B             # 本地构建
bash tools/book-m468/run_all.sh $B --publish   # 再上站（改 public/，不做 git）
```

publish 必须先于 build_unit（build_unit 要读全文网页的章锚点）；run_all.sh 已按此顺序排。
