# VTSTech-GPTBench R6

https://www.vts-tech.org https://github.com/VTSTech/VTSTech-GPTBench
<pre>
usage: VTSTech-GPTBench.py [-h] [--models MODELS] [--delay DELAY] [--verbose] [--warmup]
                           [--no-pull] [--output OUTPUT] [--json-output JSON_OUTPUT]
                           [--mode {instruct,tool,agent,all}]

VTSTech GPT Benchmark – Evaluate tiny LLMs on Ollama

options:
  -h, --help            show this help message and exit
  --models MODELS, -m MODELS
                        Comma-separated list of model names
  --delay DELAY, -d DELAY
                        Sleep delay between tests
  --verbose, -v         Print full raw output
  --warmup              Send warmup ping before each model
  --no-pull             Skip pulling models
  --output OUTPUT, -o OUTPUT
                        Save results to CSV file
  --json-output JSON_OUTPUT, -j JSON_OUTPUT
                        Save full results as JSON
  --mode {instruct,tool,agent,all}, -M {instruct,tool,agent,all}
                        Benchmark mode: instruct, tool, agent or all

Example: python benchmark.py --models llama3.2:1b,qwen2.5:0.5b --mode instruct --verbose</pre>

<pre>
VTSTech-GPTBench R6
https://www.vts-tech.org https://github.com/VTSTech/VTSTech-GPTBench


📚 INSTRUCT BENCHMARK MODE
=======================================================

========================================
🚀 EVALUATING: qwen2.5-coder:0.5b
========================================
Test: S1: List Hidden        ✅  PASS (19.37s)
    └─ Raw: "ls -a"
Test: S2: Disk Free          ✅  PASS (1.05s)
    └─ Raw: "df -h"
Test: S3: Find Text          ✅  PASS (1.43s)
    └─ Raw: "grep -r "error" app.log"
Test: S4: Own Change         ✅  PASS (1.40s)
    └─ Raw: "chown www-data:www-data web"
Test: S5: Port List          ✅  PASS (1.21s)
    └─ Raw: "netstat -tuln"
Test: S6: Process Kill       ✅  PASS (1.16s)
    └─ Raw: "kill 1234"
Test: S7: Create Dir         ✅  PASS (1.15s)
    └─ Raw: "mkdir -p a/b/c"
Test: F1: JSON Array         ✅  PASS (3.49s)
    └─ Raw: "{"list": ["A", "B", "C"]}"
Test: F2: JSON Pair          ✅  PASS (1.66s)
    └─ Raw: "{"status": "OK"}"
Test: F3: CSV Extract        ❌  FAIL (1.83s)
    └─ Raw: "["VTSTech", "101"]"
Test: F4: Lowercase          ✅  PASS (0.80s)
    └─ Raw: "hello"
Test: F5: JSON Nested        ✅  PASS (1.97s)
    └─ Raw: "{"user": {"id": 1}}"
Test: F6: No Spaces          ✅  PASS (0.89s)
    └─ Raw: "VTST"
Test: F7: Hex Color          ❌  FAIL (0.68s)
    └─ Raw: "FF"
Test: L1: Reverse Word       ❌  FAIL (1.18s)
    └─ Raw: "ANIBED"
Test: L2: Math Step          ❌  FAIL (1.78s)
    └─ Raw: "25"
Test: L3: Is Prime           ✅  PASS (1.47s)
    └─ Raw: "Yes"
Test: L4: Max Val            ✅  PASS (1.70s)
    └─ Raw: "99"
Test: L5: Count Chars        ✅  PASS (1.40s)
    └─ Raw: "2"
Test: L6: Simple Logic       ✅  PASS (0.98s)
    └─ Raw: "false"
Test: L7: Word Length        ✅  PASS (0.67s)
    └─ Raw: "6"
Test: C1: No Letter E        ❌  FAIL (0.91s)
    └─ Raw: "Red"
Test: C2: One Word           ✅  PASS (0.72s)
    └─ Raw: "Berlin"
Test: C3: No Numbers         ✅  PASS (0.94s)
    └─ Raw: "Five"
Test: C4: Binary State       ❌  FAIL (0.87s)
    └─ Raw: "false"

📊  Model Summary: qwen2.5-coder:0.5b - Score: 76.00% - Avg Latency: 2.03s

========================================
🚀  EVALUATING: granite4:350m
========================================
Test: S1: List Hidden        ✅  PASS (0.90s)
    └─ Raw: "ls -a"
Test: S2: Disk Free          ✅  PASS (0.79s)
    └─ Raw: "df -h"
Test: S3: Find Text          ❌  FAIL (1.37s)
    └─ Raw: "find . -name 'error'"
Test: S4: Own Change         ✅  PASS (2.20s)
    └─ Raw: "chown -R www-data:www-data /web"
Test: S5: Port List          ❌  FAIL (1.54s)
    └─ Raw: "lso/tcp -l"
Test: S6: Process Kill       ✅  PASS (0.92s)
    └─ Raw: "kill 1234"
Test: S7: Create Dir         ✅  PASS (1.16s)
    └─ Raw: "mkdir -p a/b/c"
Test: F1: JSON Array         ✅  PASS (3.03s)
    └─ Raw: "{"A": "a", "B": "b", "C": "c"}"
Test: F2: JSON Pair          ✅  PASS (1.39s)
    └─ Raw: "{"status": "OK"}"
Test: F3: CSV Extract        ❌  FAIL (1.10s)
    └─ Raw: "VTSTech"
Test: F4: Lowercase          ✅  PASS (0.62s)
    └─ Raw: "hello"
Test: F5: JSON Nested        ✅  PASS (1.97s)
    └─ Raw: "{"User": {"ID": 1}}"
Test: F6: No Spaces          ✅  PASS (1.13s)
    └─ Raw: "Vts"
Test: F7: Hex Color          ✅  PASS (0.99s)
    └─ Raw: "#FFFFFF"
Test: L1: Reverse Word       ❌  FAIL (1.36s)
    └─ Raw: "Nianade"
Test: L2: Math Step          ❌  FAIL (1.30s)
    └─ Raw: "25"
Test: L3: Is Prime           ✅  PASS (0.72s)
    └─ Raw: "No"
Test: L4: Max Val            ✅  PASS (0.74s)
    └─ Raw: "99"
Test: L5: Count Chars        ❌  FAIL (1.14s)
    └─ Raw: "3"
Test: L6: Simple Logic       ✅  PASS (0.81s)
    └─ Raw: "false"
Test: L7: Word Length        ✅  PASS (0.57s)
    └─ Raw: "6"
Test: C1: No Letter E        ❌  FAIL (0.73s)
    └─ Raw: "No"
Test: C2: One Word           ❌  FAIL (0.61s)
    └─ Raw: "Germany"
Test: C3: No Numbers         ❌  FAIL (1.83s)
    └─ Raw: "Invalid: Write the word for the digit '5'."
Test: C4: Binary State       ❌  FAIL (0.71s)
    └─ Raw: "on"

📊  Model Summary: granite4:350m - Score: 60.00% - Avg Latency: 1.19s


                   📊  INSTRUCT BENCHMARK REPORT                   
-----------------------------------------------------------------
Model                          | Score        | Avg Latency  | Tests   
-----------------------------------------------------------------
qwen2.5-coder:0.5b             |      76.00% |        2.03s |     25
granite4:350m                  |      60.00% |        1.19s |     25
-----------------------------------------------------------------

🏆  Best Model: qwen2.5-coder:0.5b - 76.00%
</pre>
