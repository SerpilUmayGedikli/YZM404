import json, time, pathlib
from dataclasses import dataclass
from . import strategies as S

LOG_DIR = pathlib.Path("logs"); LOG_DIR.mkdir(exist_ok=True)

@dataclass
class OrchestratorResult:
    final_answer: str
    agent_logs: list
    total_tokens: int
    elapsed_time: float

def _tokens(text): return max(1,len(text.split()))

def run_strategy(strategy: str, task: str) -> OrchestratorResult:
    fn = {
        "solo": S.solo,
        "solo_self_refine": S.solo_self_refine,
        "sequential_chain": S.sequential_chain,
        "hierarchical": S.hierarchical,
        "debate": S.debate,
        "majority_voting": S.majority_voting
    }[strategy]
    t0=time.time(); final_answer, logs=fn(task); elapsed=time.time()-t0
    total_tokens = _tokens(task) + sum(_tokens(x["message"]) for x in logs)
    out={"strategy":strategy,"task":task,"rounds":logs,"final_answer":final_answer,"total_tokens":total_tokens,"elapsed_time_sec":elapsed}
    p=LOG_DIR/f"{strategy}_{int(time.time()*1000)}.json"; p.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
    return OrchestratorResult(final_answer, logs, total_tokens, elapsed)

if __name__ == "__main__":
    print(run_strategy("debate","Çoklu ajan sistemlerini değerlendir").final_answer)
