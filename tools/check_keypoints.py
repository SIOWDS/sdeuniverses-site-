import json,sys,re,os
D=os.environ.get("KP_DIR","public/books/m")
bad=[]
for n in sys.argv[1:]:
    f=f"{D}/{n}.json" if "KP_DIR" in os.environ else f"{D}/{n}/keypoints.json"
    if not os.path.exists(f): bad.append((n,"missing"));continue
    try: d=json.load(open(f,encoding="utf-8"))
    except Exception as e: bad.append((n,"json "+str(e)[:40]));continue
    it=d.get("items",[])
    L=[len(re.sub(r"\s","",x.get("x",""))) for x in it]
    if len(it)<10: bad.append((n,"count %d"%len(it)))
    short=[l for l in L if l<170]
    if short: bad.append((n,"short %s"%short))
    if any(not x.get("t") or not x.get("ch") for x in it): bad.append((n,"field"))
print("checked",len(sys.argv)-1,"bad",bad)
