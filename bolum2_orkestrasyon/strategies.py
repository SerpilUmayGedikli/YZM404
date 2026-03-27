from .agent import Agent

def solo(task):
    a = Agent("SoloAgent","generalist")
    r = a.respond(task)
    return r, [{"agent":a.name,"role":a.role,"message":r}]

def solo_self_refine(task):
    a = Agent("Refiner","generalist")
    r1 = a.respond(task)
    r2 = a.respond("Refine: "+r1)
    return r2, [{"agent":a.name,"role":a.role,"message":r1},{"agent":a.name,"role":a.role,"message":r2}]

def sequential_chain(task):
    a1 = Agent("Planner","planner")
    a2 = Agent("Writer","writer")
    r1 = a1.respond(task); r2 = a2.respond(r1)
    return r2, [{"agent":a1.name,"role":a1.role,"message":r1},{"agent":a2.name,"role":a2.role,"message":r2}]

def hierarchical(task):
    lead = Agent("Lead","supervisor"); w1=Agent("W1","analyst"); w2=Agent("W2","builder")
    p = lead.respond("Plan "+task); x = w1.respond(p); y = w2.respond(p); f = lead.respond(x+" "+y)
    return f,[{"agent":lead.name,"role":lead.role,"message":p},{"agent":w1.name,"role":w1.role,"message":x},{"agent":w2.name,"role":w2.role,"message":y},{"agent":lead.name,"role":lead.role,"message":f}]

def debate(task):
    a=Agent("Pro","proponent"); b=Agent("Con","opponent"); j=Agent("Judge","arbitrator")
    p=a.respond(task); c=b.respond(task); f=j.respond(p+" | "+c)
    return f,[{"agent":a.name,"role":a.role,"message":p},{"agent":b.name,"role":b.role,"message":c},{"agent":j.name,"role":j.role,"message":f}]

def majority_voting(task):
    agents=[Agent("V1","voter"),Agent("V2","voter"),Agent("V3","voter")]
    msgs=[{"agent":a.name,"role":a.role,"message":a.respond(task)} for a in agents]
    return msgs[0]["message"], msgs
