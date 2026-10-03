import sys, time, json, random
sys.path.insert(0, "src")
import kernel, jmespath

def mkserv(n):
    random.seed(7)
    S = []
    for i in range(n):
        s = {"name": "server-%d" % i,
             "region": random.choice(["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"]),
             "status": "active" if i % 3 else "draining",
             "load": round(random.random(), 3),
             "instances": [{"id": "i-%d-%c" % (i, c), "cpu": round(random.random(), 3),
                            "mem": random.choice([256, 512, 1024, 2048, 4096]),
                            "tags": {"app": "web", "tier": "prod" if i % 2 else "dev"}}
                           for c in "abc"]}
        S.append(s)
    return json.dumps({"servers": S})

for n in [2000, 10000, 20000]:
    DOC = mkserv(n)
    PARSED = json.loads(DOC)
    expr = "servers[?status == `active`].instances[0].id"
    compiled = jmespath.compile(expr)
    for _ in range(2):
        kernel.search(expr, DOC)
        compiled.search(PARSED)
    N = 20
    t0 = time.perf_counter()
    for _ in range(N):
        kernel.search(expr, DOC)
    ta = (time.perf_counter() - t0) / N * 1000
    t0 = time.perf_counter()
    for _ in range(N):
        compiled.search(json.loads(DOC))
    tj = (time.perf_counter() - t0) / N * 1000
    print("n=%6d  doc=%.2fMB  aero=%.1fms  jmespath=%.1fms  aero=%s" % (
        n, len(DOC) / 1e6, ta, tj, "WIN %.2fx" % (tj / ta) if ta < tj else "lose %.2fx" % (ta / tj)), flush=True)
