第 533 号补三位一体（学习包＋智能体）流水线，仓库根目录运行：
  python3 tools/book-m533/gen_config.py tools/book-m533/content.json      # -> tools/book_unit/m533.json
  python3 tools/book-m533/build_unit_533.py --config tools/book_unit/m533.json --out-pdf public/books/m/533/learning-pack.pdf
  python3 tools/book-m533/register.py          # keypoints.json + agents.json
  python3 tools/book-m533/agent_page.py        # agent/index.html + 名录卡
  python3 tools/book-m533/patch_catalog.py     # catalog.json 533 条目补字段
  python3 tools/build_book_rag.py 533          # rag.json
  python3 tools/build_bookshelf.py --shelf-only
不做 git 操作，不重建搜索索引，不改书号/ISBN。
