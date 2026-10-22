"""Verify the deployed 451 publication, exact assets and shelf entries."""
import hashlib,json,time,urllib.request,urllib.error,os,re
from pathlib import Path
items=json.loads((Path(__file__).parent/"live-manifest.json").read_text())
root=Path(__file__).resolve().parents[2]
base="https://sdeuniverses.com"
stamp=os.environ.get("GITHUB_SHA","m451")
def fetch(path, headers=None):
    req=urllib.request.Request(base+path+"?m451verify="+stamp,headers={"User-Agent":"SDE-Publication-Verification",**(headers or {})})
    with urllib.request.urlopen(req,timeout=45) as r:
        return r.status,r.headers,r.read()
def html_body(data):
    # Exclude the known Cloudflare Web Analytics script. The measured edge
    # response also adds one newline before </body>; normalize only that
    # final whitespace in both source manifests and received HTML.
    cleaned, beacon_count=re.subn(rb"(?is)<script\b(?=[^>]*\bsrc=[\"']https://static\.cloudflareinsights\.com/beacon\.min\.js[^\"']*[\"'])[^>]*>.*?</script\s*>",b"",data)
    match=re.search(rb"(?is)<body\b[^>]*>.*?</body\s*>",cleaned)
    body=re.sub(rb"[ \t\r\n]+(?=</body\s*>$)",b"",match.group(),flags=re.I) if match else None
    return body,beacon_count

def html_diagnostic(item, received_body, beacon_count):
    source=root/"public"/item["path"].lstrip("/")
    expected_body=None
    if source.is_file():
        expected_body,_=html_body(source.read_bytes())
    info={"path":item["path"],"sourcePath":str(source.relative_to(root)),
          "sourceExists":source.is_file(),"beaconCount":beacon_count,
          "manifestExpectedBodySha256":item["htmlBodySha256"],
          "expectedBodyBytes":len(expected_body) if expected_body is not None else None,
          "actualBodyBytes":len(received_body) if received_body is not None else None,
          "expectedBodySha256":hashlib.sha256(expected_body).hexdigest() if expected_body is not None else None,
          "actualBodySha256":hashlib.sha256(received_body).hexdigest() if received_body is not None else None}
    if expected_body is not None and received_body is not None:
        byte_offset=next((i for i,(a,b) in enumerate(zip(expected_body,received_body)) if a!=b),min(len(expected_body),len(received_body)))
        expected_text=expected_body.decode("utf-8",errors="replace")
        actual_text=received_body.decode("utf-8",errors="replace")
        char_offset=next((i for i,(a,b) in enumerate(zip(expected_text,actual_text)) if a!=b),min(len(expected_text),len(actual_text)))
        lo=max(0,char_offset-80);hi=char_offset+81
        info.update({"firstDifferentByte":byte_offset,"firstDifferentCharacter":char_offset,
                     "expectedContext":expected_text[lo:hi],"actualContext":actual_text[lo:hi],
                     "expectedBodyCharacters":len(expected_text),"actualBodyCharacters":len(actual_text)})
    return info

last_diagnostic_signature=None
deadline=time.time()+900
while True:
    try:
        result=[]
        diagnostic=None
        for x in items:
            status,headers,data=fetch(x["path"])
            assert status==200, x["path"]
            if x.get("htmlBodySha256"):
                body,beacon_count=html_body(data)
                if body is None or hashlib.sha256(body).hexdigest()!=x["htmlBodySha256"]:
                    diagnostic=html_diagnostic(x,body,beacon_count)
                    raise AssertionError("HTML body not current: "+x["path"])
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
        failure={"success":False,"error":str(e),"assets":result,"realModelTested":False,
                 "htmlDiagnostic":diagnostic}
        Path("m451-live-result.json").write_text(json.dumps(failure,ensure_ascii=False,indent=2)+"\n")
        print("Waiting for deployment:",str(e),flush=True)
        if diagnostic is not None:
            signature=json.dumps(diagnostic,ensure_ascii=False,sort_keys=True)
            if signature!=last_diagnostic_signature:
                print("HTML_DIAGNOSTIC:",signature,flush=True)
                last_diagnostic_signature=signature
        if time.time()>=deadline: raise
        time.sleep(20)
