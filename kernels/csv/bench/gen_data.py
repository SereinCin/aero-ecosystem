#!/usr/bin/env python3
"""Generate deterministic CSV rows for the Aero batch benchmark.
Usage: python gen_data.py [rows] [output]
"""
import random
import sys

def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    out = sys.argv[2] if len(sys.argv) > 2 else "data.csv"
    random.seed(42)
    with open(out, "w") as f:
        for i in range(n):
            price = random.randint(0, 99999)
            qty = random.randint(1, 99)
            active = 1 if random.random() < 0.5 else 0
            f.write(f"{i},{price},{qty},{active}\n")

if __name__ == "__main__":
    main()
