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

Example: python benchmark.py --models llama3.2:1b,qwen2.5:0.5b --mode instruct --verbose<pre>
