import csv, json, pathlib
from bolum2_orkestrasyon.orchestrator import run_strategy

STRATS=["solo","solo_self_refine","sequential_chain","hierarchical","debate","majority_voting"]

def run_benchmark():
    tasks=json.loads(pathlib.Path("bolum3_benchmark/tasks.json").read_text(encoding="utf-8"))
    results=[]
    for t in tasks:
        for s in STRATS:
            r=run_strategy(s,t["prompt"])
            results.append({
                "task_id":t["task_id"],"tier":t["tier"],"strategy":s,
                "final_answer":r.final_answer,"total_tokens":r.total_tokens,"elapsed_time":r.elapsed_time
            })
    out=pathlib.Path("bolum4_degerlendirme/results"); out.mkdir(parents=True,exist_ok=True)
    (out/"benchmark_results.json").write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding="utf-8")
    with (out/"benchmark_results.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=results[0].keys()); w.writeheader(); w.writerows(results)
    print("Benchmark tamamlandı.")

if __name__=="__main__":
    run_benchmark()
