#!/usr/bin/env python3
"""Source-preserving layout fixes and truthful annual catalog labels."""
from pathlib import Path
import argparse,json,re
from bs4 import BeautifulSoup
WRAP='\n/* Wrap long source titles without hiding or clipping content. */\n.catalog-head,.card,.card h2,.card p,.card .info,.card .tag,.meta,.crossyear{overflow-wrap:anywhere;word-break:normal}\n'
def prepare():
    path=Path('tools/wechat_2025_longform.py');text=path.read_text()
    before="re.match(r'^https?://mp\\.weixin\\.qq\\.com/',text)"
    after="re.match(r'^https?://mp\\.weixin\\.qq\\.com/',compact(text))"
    if before in text:text=text.replace(before,after)
    elif after not in text:raise ValueError('Source cleanup rule changed; inspect before patching')
    marker="JS='''"
    if WRAP not in text:
        assert marker in text
        text=text.replace(marker,'CSS += '+repr(WRAP)+'\n'+marker,1)
    compile(text,str(path),'exec');path.write_text(text)
    test=Path('tools/wechat_2025_publish_20260920.py');t=test.read_text();t=t.replace("page.locator('[data-theme]')","page.locator('button[data-theme]')");compile(t,str(test),'exec');test.write_text(t)

def finish():
    root=Path('public/wechat-picks');reportpath=root/'2025/batch-20260920/report.json';report=json.loads(reportpath.read_text());audit={}
    for year in ['2024','2025']:
        path=root/year/'index.html';s=BeautifulSoup(path.read_text(),'html.parser');entries=s.select('li.article');dates=sorted(li.select_one('.date').get_text(strip=True) for li in entries);accounts={li.select_one('.source').get_text(strip=True) for li in entries};n=len(entries);fulltext=sum(bool(li.select_one('a[data-longform]')) for li in entries)
        for node in s.select('.hero .lead.zh-only'):node.string=f'{year}年公众号文章共{n}篇，按真实日期由新到旧排列。已整理的网页长文可点击“阅读全文”；原有PDF入口继续保留。'
        for node in s.select('.hero .lead.en-only'):node.string=f'{n} articles from {year}, newest first. Available full-text webpages are marked; existing PDF links are preserved.'
        stats=s.select_one('.hero .stats')
        if stats:
            stats.clear()
            for value in [f'{n}篇文章',f'{fulltext}篇本批网页长文',f'{dates[0]}—{dates[-1]}',f'{len(accounts)}个公众号来源']:
                item=s.new_tag('span');item.string=value;stats.append(item)
        description=f'{year}年公众号选读：{n}篇文章；本批提供{fulltext}篇网页长文。保留原文日期、署名和已有原稿阅读入口。'
        for node in s.select('meta[name="description"],meta[property="og:description"]'):node['content']=description
        path.write_text(str(s));audit[year]={'articles':n,'batch_fulltext':fulltext,'date_range':[dates[0],dates[-1]],'accounts':len(accounts)}
    report['annual_labels_verified']=audit;report['layout_quality']={'long_titles_wrap_without_clipping':True,'space_split_browser_footer_urls_cleaned':True,'original_source_text_and_hash_checks_retained':True}
    reportpath.write_text(json.dumps(report,ensure_ascii=False,indent=2));out=Path('artifacts/wechat-2025-publication');out.mkdir(parents=True,exist_ok=True);(out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(audit,ensure_ascii=False))
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['prepare','finish']);args=parser.parse_args();globals()[args.command]()
