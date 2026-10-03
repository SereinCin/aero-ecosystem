import sys, time, json, random
sys.path.insert(0, "src")
import kernel, jmespath

random.seed(7)
SERVERS = []
for i in range(2000):
    s = {"name": "server-%d" % i,
         "region": random.choice(["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"]),
         "status": "active" if i % 3 else "draining",
         "load": round(random.random(), 3),
         "instances": [{"id": "i-%d-%c" % (i, c), "cpu": round(random.random(), 3),
                        "mem": random.choice([256, 512, 1024, 2048, 4096]),
                        "tags": {"app": "web", "tier": "prod" if i % 2 else "dev"}}
                       for c in "abc"]}
    SERVERS.append(s)
DOC = json.dumps({"servers": SERVERS})
PARSED = json.loads(DOC)

expr = "servers[?status == `active`].instances[0].id"
compiled = jmespath.compile(expr)
for _ in range(5):
    kernel.search(expr, DOC)
    compiled.search(PARSED)

# batch: many queries on the SAME doc (aero re-parses expr+doc; jmespath reuses compiled AST)
N = 200
t0 = time.perf_counter()
for _ in range(N):
    kernel.search(expr, DOC)
ta = (time.perf_counter() - t0) / N * 1000
t0 = time.perf_counter()
for _ in range(N):
    compiled.search(PARSED)
tj = (time.perf_counter() - t0) / N * 1000
print("batch 200 queries on one doc:")
print("  aero     %.3f ms/q" % ta)
print("  jmespath %.3f ms/q" % tj)
print("  ratio    %.2fx" % (tj / ta))

# one-shot: fresh load each query (aero = parse+eval+ser; jmespath = json.loads+eval)
N = 50
t0 = time.perf_counter()
for _ in range(N):
    kernel.search(expr, DOC)
ta = (time.perf_counter() - t0) / N * 1000
t0 = time.perf_counter()
for _ in range(N):
    compiled.search(json.loads(DOC))
tj = (time.perf_counter() - t0) / N * 1000
print("one-shot 50 queries (fresh doc each):")
print("  aero     %.3f ms/q" % ta)
print("  jmespath %.3f ms/q" % tj)
print("  ratio    %.2fx" % (tj / ta))
