"""Verify the deployed 451 publication, exact assets and shelf entries."""
import hashlib,json,time,urllib.request,urllib.error,os,re
from pathlib import Path
items=json.loads((Path(__file__).parent/"live-manifest.json").read_text())
base="https://sdeuniverses.com"
stamp=os.environ.get("GITHUB_SHA","m451")
def fetch(path, headers=None):
    req=urllib.request.Request(base+path+"?m451verify="+stamp,headers={"User-Agent":"SDE-Publication-Verification",**(headers or {})})
    with urllib.request.urlopen(req,timeout=45) as r:
        return r.status,r.headers,r.read()
deadline=time.time()+900
while True:
    try:
        result=[]
        for x in items:
            status,headers,data=fetch(x["path"])
            assert status==200, x["path"]
            if x.get("htmlBodySha256"):
                body=re.search(rb"(?is)<body\b[^>]*>.*?</body\s*>",data)
                assert body and hashlib.sha256(body.group()).hexdigest()==x["htmlBodySha256"], "HTML body not current: "+x["path"]
                title=re.search(r"(?is)<title[^>]*>(.*?)</title>",data.decode("utf-8"))
                assert title and title.group(1)==x["title"], "HTML title differs: "+x["path"]
            else:
                assert len(data)==x["bytes"] and hashlib.sha256(data).hexdigest()==x["sha256"], "Asset not current: "+x["path"]
            result.append({"path":x["path"],"status":status,"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest(),"comparison":"html-body-and-title" if x.get("htmlBodySha256") else "exact-bytes","servedFrom":headers.get("x-served-from","assets")})
        for p in ["/books/","/monographs/","/sites/read/library/","/books/agent/","/today/"]:
            status,_,data=fetch(p)
            text=data.decode("utf-8")
            assert status==200 and "/books/m/451/" in text and "发生的时差" in text,p
            result.append({"path":p,"status":status,"book451":True})
        for x in items:
            if x["path"].endswith(".pdf"):
                status,headers,data=fetch(x["path"],{"Range":"bytes=0-1023"})
                assert status==206 and len(data)==1024 and data.startswith(b"%PDF-"),"PDF Range failed: "+x["path"]
        Path("m451-live-result.json").write_text(json.dumps({"success":True,"assets":result,"pdfRangeTests":3,"realModelTested":False},ensure_ascii=False,indent=2)+"\n")
        print("PASS:",len(items),"verified assets (HTML body/title and other exact bytes); five entrances; three PDF byte-range checks.")
        break
    except Exception as e:
        print("Waiting for deployment:",str(e),flush=True)
        if time.time()>=deadline: raise
        time.sleep(20)
