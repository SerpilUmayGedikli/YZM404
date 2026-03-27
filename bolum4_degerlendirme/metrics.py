import json, pathlib, statistics

def oqs(text): return min(10, max(1, len(text.split())//8 + 1))

def normalize(vals):
    mn,mx=min(vals),max(vals)
    if mx==mn: return [0.5]*len(vals)
    return [(v-mn)/(mx-mn) for v in vals]

def compute():
    p=pathlib.Path("bolum4_degerlendirme/results/benchmark_results.json")
    data=json.loads(p.read_text(encoding="utf-8"))
    by={}
    for r in data: by.setdefault(r["strategy"],[]).append(r)

    rows=[]
    for s,arr in by.items():
        tsr=1.0
        te=statistics.mean(x["total_tokens"] for x in arr)
        wcl=statistics.mean(x["elapsed_time"] for x in arr)
        q=statistics.mean(oqs(x["final_answer"]) for x in arr)
        rows.append({"strategy":s,"TSR":tsr,"TE":te,"WCL":wcl,"OQS":q})

    TSRn=normalize([r["TSR"] for r in rows]); OQSn=normalize([r["OQS"] for r in rows]); TEn=normalize([r["TE"] for r in rows]); WCLn=normalize([r["WCL"] for r in rows])
    for i,r in enumerate(rows):
        r["CEI_balanced"]=0.25*TSRn[i]+0.25*OQSn[i]-0.25*TEn[i]-0.25*WCLn[i]
        r["CEI_quality"]=0.4*TSRn[i]+0.3*OQSn[i]-0.15*TEn[i]-0.15*WCLn[i]
        r["CEI_cost"]=0.2*TSRn[i]+0.2*OQSn[i]-0.3*TEn[i]-0.3*WCLn[i]
        succ=max(1,int(len(by[r["strategy"]])*r["TSR"]))
        r["Cost_per_success_USD"]=(r["TE"]*0.00001)/succ

    out=pathlib.Path("bolum4_degerlendirme/results/metrics_summary.json")
    out.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Metrikler yazıldı:", out)

if __name__=="__main__":
    compute()
