# -*- coding: utf-8 -*-
import time
import requests
import json
import os
import re
import subprocess
import sys
import argparse
import importlib
import site

# Import modules
from prompts import INSTRUCT_SYSTEM_PROMPT, INSTRUCT_FEW_SHOT, TOOL_SYSTEM_PROMPT, TOOL_FEW_SHOT, PLANNER_SYSTEM_PROMPT, PLANNER_FEW_SHOT
from tests import INSTRUCT_TEST_SUITE, TOOL_TEST_SUITE, AGENT_TEST_SUITE
from tools import ToolRegistry, execute_tool, validate_tool_call, is_tool_call

#def ensure_ollama():
#    try:
#        import ollama
#    except ImportError:
#        print("Ollama library not found. Installing now...")
#        subprocess.check_call([sys.executable, "-m", "pip", "install", "ollama"])
#        print("Successfully installed ollama.")
#        importlib.reload(site)
#
#ensure_ollama()
#import ollama

# ============ CONFIGURATION ============
MODEL_NUM_PREDICT = {
    "llama3.2:1b": 128,
    "llama3.2:3b": 256,
    "gemma3:1b": 256,
    "gemma3:4b": 512,
    "granite3-moe:1b": 256,
    "granite3-moe:3b": 512,
    "qwen2.5:0.5b": 128,
    "qwen2.5:1.5b": 256,
    "qwen2.5-coder:0.5b": 128,
    "qwen2.5-coder:1.5b": 256,
    "granite4:350m": 128,
    "granite4:800m": 256,
    "default": 256
}

BENCHMARK_CONFIG = {
    "sleep_delay": 0.2,
    "models": [
        #"llama3.2:1b", 
        #"granite3-moe:1b",
        #"qwen2.5:0.5b",
        "qwen2.5-coder:0.5b-instruct-q4_k_m",
        "granite4:350m"
    ],
    "options": {
        "temperature": 0,
        "num_ctx": 8192,
        "top_k": 1,
        "min_p": 0.05,
        "repeat_penalty": 1.0,
        "num_gpu": 0,
        "seed": 420,
    }
}
PLANNER_MODEL = "qwen2.5-coder:0.5b-instruct-q4_k_m"
	
# ============ HELPER FUNCTIONS ============
def banner():
    print(f"VTSTech-GPTBench R6")
    print(f"https://www.vts-tech.org https://github.com/VTSTech/VTSTech-GPTBench\n")

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="VTSTech GPT Benchmark – Evaluate tiny LLMs on Ollama",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example: python benchmark.py --models llama3.2:1b,qwen2.5:0.5b --mode instruct --verbose"
    )
    parser.add_argument("--models", "-m", type=str, help="Comma-separated list of model names")
    parser.add_argument("--delay", "-d", type=float, default=0.2, help="Sleep delay between tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print full raw output")
    parser.add_argument("--warmup", action="store_true", help="Send warmup ping before each model")
    parser.add_argument("--no-pull", action="store_true", help="Skip pulling models")
    parser.add_argument("--output", "-o", type=str, help="Save results to CSV file")
    parser.add_argument("--json-output", "-j", type=str, help="Save full results as JSON")
    parser.add_argument("--mode", "-M", choices=["instruct", "tool", "agent", "all"], default="instruct",
                       help="Benchmark mode: instruct, tool, agent or all")
    return parser.parse_args()

def check_server():
    try:
        requests.get("http://127.0.0.1:11434")
        return True
    except:
        return False

def ollama_list():
    resp = requests.get("http://127.0.0.1:11434/api/tags")
    resp.raise_for_status()
    return [m["name"] for m in resp.json()["models"]]

def pull_if_missing(model_name):
    local_models = ollama_list()
    if model_name not in local_models:
        print(f"📥 Pulling {model_name}...")
        payload = {"name": model_name, "stream": False}
        requests.post("http://127.0.0.1:11434/api/pull", json=payload)

def ollama_chat_http(model, messages, options=None, format=None):
    url = "http://127.0.0.1:11434/api/chat"
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "raw": False,
    }
    if options:
        payload["options"] = options
    if format:
        payload["format"] = format
    resp = requests.post(url, json=payload)
    resp.raise_for_status()
    data = resp.json()
    return data["message"]["content"]

def sanitize_output(text):
    """Clean model output of special tokens and formatting."""
    # Remove think blocks (DeepSeek)
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    
    # Remove chat template tokens
    stop_tokens = ["<|system|>", "<|user|>", "<|assistant|>", "<|end|>", "</s>"]
    for token in stop_tokens:
        text = text.replace(token, "")
    
    # Remove markdown code blocks
    text = re.sub(r'```[a-z]*\n?', '', text)
    text = text.replace('```', '')
    
    # Remove ANSI escape codes
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    text = ansi_escape.sub('', text)
    
    # Keep only printable characters
    text = "".join(char for char in text if char.isprintable())
    text = text.strip()
    
    # Remove surrounding quotes
    if (text.startswith('"') and text.endswith('"')) or \
       (text.startswith("'") and text.endswith("'")) or \
       (text.startswith('`') and text.endswith('`')):
        text = text[1:-1]
    
    return text.strip()

# ============ EVALUATION FUNCTIONS ============
def evaluate_model_instruct(model, args):
    print(f"\n{'='*40}")
    print(f"🚀 EVALUATING: {model}")
    print(f"{'='*40}")
    
    passed_count = 0
    total_time = 0
    results = []
    
    options = BENCHMARK_CONFIG["options"].copy()
    options["num_predict"] = MODEL_NUM_PREDICT.get(model, MODEL_NUM_PREDICT["default"])
    
    if args.warmup:
        print(f"   🔥 Warmup ping...", end=" ", flush=True)
        try:
            ollama_chat_http(
                model=model,
                messages=[{"role": "user", "content": "ping"}],
                options={"num_predict": 1}
            )
            print("done")
        except Exception as e:
            print(f"failed ({e})")
    
    for test in INSTRUCT_TEST_SUITE:
        print(f"Test: {test['name']:<22}", end=" ", flush=True)
        
        is_json_test = "JSON" in test['name'] or "JSON" in test['prompt']
        messages = [{"role": "system", "content": INSTRUCT_SYSTEM_PROMPT}] + INSTRUCT_FEW_SHOT + [
            {"role": "user", "content": test['prompt']}
        ]
        
        if args.delay > 0:
            print(f"(Wait {args.delay}s..)", end=" ", flush=True)
            time.sleep(args.delay)
        
        start = time.perf_counter()
        try:
            format_json = "json" if is_json_test else None
            raw_content = ollama_chat_http(
                model=model,
                messages=messages,
                options=options,
                format=format_json
            )
            duration = time.perf_counter() - start
            content = sanitize_output(raw_content)
            
            is_pass = test["validator"](content)
            
            status = "✅ PASS" if is_pass else "❌ FAIL"
            print(f"{status} ({duration:.2f}s)")
            
            if args.verbose:
                raw_display = raw_content.replace('\n', ' ')
                if len(raw_display) > 200:
                    raw_display = raw_display[:200] + "…"
                print(f"    └─ Raw: \"{raw_display}\"")
            
            if is_pass:
                passed_count += 1
            total_time += duration
            
            results.append({
                "model": model,
                "test": test['name'],
                "pass": is_pass,
                "latency": duration,
                "raw": raw_content,
                "sanitized": content
            })
            
            if args.output:
                import csv
                file_exists = os.path.isfile(args.output)
                with open(args.output, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    if not file_exists:
                        writer.writerow(["Mode", "Model", "Test", "Pass", "Latency", "Raw"])
                    writer.writerow(["instruct", model, test['name'], is_pass, f"{duration:.2f}", raw_content])
                    
        except Exception as e:
            print(f"⚠️ ERROR: {e}")
    
    score = (passed_count / len(INSTRUCT_TEST_SUITE)) * 100
    avg_lat = total_time / len(INSTRUCT_TEST_SUITE)
    
    print(f"\n📊 Model Summary: {model} - Score: {score:.2f}% - Avg Latency: {avg_lat:.2f}s")
    
    return model, score, avg_lat, results

def get_available_tools_list():
    # Gets all static methods from ToolRegistry that don't start with _
    return [func for func in dir(ToolRegistry) if not func.startswith("_") 
            and callable(getattr(ToolRegistry, func))]
            
def evaluate_model_agent(model, planner, args):
    """
    Executes a multi-step workflow. 
    1. Planner (Instruct) breaks down task.
    2. Executor (Tool) performs steps.
    """    
    passed_count = 0
    total_time = 0
    test_results = []
    
    # We use a higher-tier 'planner' for the logic and the benchmarked 'model' for execution
    print(f"\n🚀 EVALUATING AGENT: [Planner: {planner}] [Tools: {model}]")
    print("-" * 55)

    for test in AGENT_TEST_SUITE:
        print(f"Agent Task: {test['name']:<25}", end=" ", flush=True)
        start_time = time.perf_counter()
        
        try:
            # --- STEP 1: PLANNING ---
            # Using the 'planner' model to generate a sequence of sub-tasks
            plan_msg = [
                {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
                {"role": "user", "content": test['prompt']}
            ]
            
            raw_plan = ollama_chat_http(planner, plan_msg, format="json")
            steps = json.loads(sanitize_output(raw_plan))
            
            # --- STEP 2: EXECUTION ---
            # The benchmarked 'model' now performs each step using tools
            context = ""
            
            # Handle if planner returns a dict instead of a list
            step_items = steps.items() if isinstance(steps, dict) else enumerate(steps)

            for key, val in step_items:
                # If list: key is index, val is step string. If dict: key is step name, val is details.
                step_desc = val if isinstance(steps, list) else key
                plan_details = val # Data associated with the step
                
                exec_msg = [
                    {"role": "system", "content": TOOL_SYSTEM_PROMPT},
                    {"role": "user", "content": f"PLAN DATA: {plan_details}\nACTION: Execute the tool for '{step_desc}' using the PLAN DATA."}
                ]
                
                # Model decides which tool to call
                tool_call_raw = ollama_chat_http(model, exec_msg)
                cleaned_call = sanitize_output(tool_call_raw)
                
                if is_tool_call(cleaned_call):
                    try:
                        # Parse the JSON tool call
                        call_data = json.loads(cleaned_call) if isinstance(cleaned_call, str) else cleaned_call
                        
                        # Standardize formats: "name"/"arguments", "tool"/"parameters", or "function" nested
                        t_name = call_data.get("name") or call_data.get("tool") or \
                                 call_data.get("function", {}).get("name") or list(call_data.keys())[0]
                        t_args = call_data.get("arguments") or call_data.get("parameters") or \
                                 call_data.get("function", {}).get("arguments") or call_data.get(t_name)

                        # Ensure t_args is a dictionary
                        if isinstance(t_args, list):
                            # Map list items to the known tool's first argument
                            if t_name == "create_directory": t_args = {"path": t_args[0]}
                        elif isinstance(t_args, str):
                            try: t_args = json.loads(t_args)
                            except: pass

                        # Execute the tool and update context
                        tool_output = execute_tool(t_name, t_args)
                        context += f"\nStep '{step_desc}': Result was {json.dumps(tool_output)}"
                        
                    except Exception as e:
                        context += f"\nStep '{step_desc}': Execution Error: {str(e)}"
                else:
                    # Record raw response if model fails to call a tool
                    context += f"\nStep '{step_desc}': {cleaned_call}"

            # --- STEP 3: VALIDATION ---
            is_pass = test["validator"](context)
            
            duration = time.perf_counter() - start_time
            total_time += duration
            if is_pass: passed_count += 1
            
            test_results.append({
                "model": model,
                "test": test['name'],
                "pass": is_pass,
                "latency": duration,
                "context": context
            })
            
            print(f"{'✅ PASS' if is_pass else '❌ FAIL'} ({duration:.2f}s)")
            
        except Exception as e:
            print(f"⚠️ ERROR: {e}")

    score = (passed_count / len(AGENT_TEST_SUITE)) * 100 if AGENT_TEST_SUITE else 0
    avg_lat = total_time / len(AGENT_TEST_SUITE) if AGENT_TEST_SUITE else 0
    
    return (model, score, avg_lat, test_results)
    
def evaluate_model_tool(model, args):
    print(f"\n{'='*40}")
    print(f"🚀 TOOL BENCHMARK: {model}")
    print(f"{'='*40}")
    
    passed_count = 0
    total_time = 0
    results = []
    
    options = BENCHMARK_CONFIG["options"].copy()
    options["num_predict"] = MODEL_NUM_PREDICT.get(model, MODEL_NUM_PREDICT["default"])
    
    if args.warmup:
        print(f"   🔥 Warmup ping...", end=" ", flush=True)
        try:
            ollama_chat_http(
                model=model,
                messages=[{"role": "user", "content": "ping"}],
                options={"num_predict": 1}
            )
            print("done")
        except Exception as e:
            print(f"failed ({e})")
    
    for test in TOOL_TEST_SUITE:
        print(f"Test: {test['name']:<22}", end=" ", flush=True)
        
        messages = [{"role": "system", "content": TOOL_SYSTEM_PROMPT}] + TOOL_FEW_SHOT + [
            {"role": "user", "content": test['prompt']}
        ]
        
        if args.delay > 0:
            print(f"(Wait {args.delay}s..)", end=" ", flush=True)
            time.sleep(args.delay)
        
        start = time.perf_counter()
        
        try:
            # Turn 1: Model calls tool
            raw_content = ollama_chat_http(
                model=model,
                messages=messages,
                options=options,
                format=None
            )
            
            # Parse tool call
            tool_name, tool_args = None, None
            try:
                cleaned = raw_content.strip()
                if cleaned.startswith("```"):
                    cleaned = re.sub(r'^```json\n?|```$', '', cleaned)
                data = json.loads(cleaned)
                
                if "tool_calls" in data:
                    tool_call = data["tool_calls"][0]
                    tool_name = tool_call["function"]["name"]
                    tool_args = json.loads(tool_call["function"]["arguments"])
                elif "name" in data and "arguments" in data:
                    tool_name = data["name"]
                    tool_args = data["arguments"]
                elif "function" in data and "params" in data:
                    tool_name = data["function"]
                    tool_args = data["params"]
            except:
                pass
            
            # Check if tool call was expected
            if test.get("expects_tool", False):
                if not tool_name:
                    duration = time.perf_counter() - start
                    print(f"❌ FAIL (no tool call) ({duration:.2f}s)")
                    if args.verbose:
                        print(f"    └─ Raw: \"{raw_content[:200]}\"")
                    continue
                
                # Execute the real tool
                tool_result = execute_tool(tool_name, tool_args)
                
                # Add tool call and result to conversation
                messages.append({"role": "assistant", "content": raw_content.strip()})
                messages.append({
                    "role": "tool",
                    "content": json.dumps(tool_result) if isinstance(tool_result, dict) else str(tool_result),
                    "name": tool_name
                })
                
                # Turn 2: Model responds with natural language
                final_response = ollama_chat_http(
                    model=model,
                    messages=messages,
                    options=options,
                    format=None
                )
                
                duration = time.perf_counter() - start
                content = sanitize_output(final_response)
                
                # Validate using test's validator
                is_pass = test["validator"](content)
                
                if args.verbose:
                    print(f"\n      ├─ Tool Call: {tool_name}({tool_args})")
                    print(f"      ├─ Tool Result: {json.dumps(tool_result)[:100]}")
                    print(f"      └─ Final: {content[:100]}")
            
            else:
                # No tool expected - direct answer
                duration = time.perf_counter() - start
                content = sanitize_output(raw_content)
                is_pass = test["validator"](content) and not is_tool_call(raw_content)
            
            status = "✅ PASS" if is_pass else "❌ FAIL"
            print(f"{status} ({duration:.2f}s)")
            
            if is_pass:
                passed_count += 1
            total_time += duration
            
            results.append({
                "model": model,
                "test": test['name'],
                "pass": is_pass,
                "latency": duration,
                "tool_call": raw_content if test.get("expects_tool", False) else None,
                "tool_result": tool_result if test.get("expects_tool", False) else None,
                "final_response": final_response if test.get("expects_tool", False) else raw_content,
                "sanitized": content
            })
            
            if args.output:
                import csv
                file_exists = os.path.isfile(args.output)
                with open(args.output, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    if not file_exists:
                        writer.writerow(["Mode", "Model", "Test", "Pass", "Latency", "Tool Call", "Final Response"])
                    writer.writerow([
                        "tool", model, test['name'], is_pass, f"{duration:.2f}",
                        raw_content if test.get("expects_tool", False) else "",
                        final_response if test.get("expects_tool", False) else raw_content
                    ])
                    
        except Exception as e:
            print(f"⚠️ ERROR: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
    
    score = (passed_count / len(TOOL_TEST_SUITE)) * 100
    avg_lat = total_time / len(TOOL_TEST_SUITE)
    
    print(f"\n📊 Model Summary: {model} - Score: {score:.2f}% - Avg Latency: {avg_lat:.2f}s")
    
    return model, score, avg_lat, results

def run_benchmark(args):
    instruct_results = []
    tool_results = []
    agent_results = []
    
    models = BENCHMARK_CONFIG["models"]
    if args.models:
        models = [m.strip() for m in args.models.split(",")]
    
    if args.mode in ["instruct", "all"]:
        print("\n📚 INSTRUCT BENCHMARK MODE")
        print("=" * 55)
        
        for model in models:
            result = evaluate_model_instruct(model, args)
            instruct_results.append(result)
            
            if args.json_output:
                with open(f"{args.json_output}_instruct.json", 'w') as f:
                    json.dump([r[3] for r in instruct_results], f, indent=2)
    
    if args.mode in ["tool", "all"]:
        print("\n🛠️  TOOL BENCHMARK MODE")
        print("=" * 55)
        
        for model in models:
            result = evaluate_model_tool(model, args)
            tool_results.append(result)
            
            if args.json_output:
                with open(f"{args.json_output}_tool.json", 'w') as f:
                    json.dump([r[3] for r in tool_results], f, indent=2)

    if args.mode in ["agent", "all"]:
        print("\n🛠️  AGENT BENCHMARK MODE")
        print("=" * 55)
        
        for model in models:
            result = evaluate_model_agent(model, PLANNER_MODEL, args)
            agent_results.append(result)
            if args.json_output:
                with open(f"{args.json_output}_agent.json", 'w') as f:
                    json.dump([r[3] for r in agent_results], f, indent=2)
                        
    if args.mode in ["instruct", "all"]:
        print_instruct_report(instruct_results)
    
    if args.mode in ["tool", "all"]:
        print_tool_report(tool_results)
        
    if args.mode in ["agent", "all"]:
        print_agent_report(agent_results)

def print_instruct_report(results):
    print("\n\n" + "📊 INSTRUCT BENCHMARK REPORT".center(65))
    print("-" * 65)
    print(f"{'Model':<30} | {'Score':<12} | {'Avg Latency':<12} | {'Tests':<8}")
    print("-" * 65)
    
    for model, score, lat, res in sorted(results, key=lambda x: x[1], reverse=True):
        print(f"{model:<30} | {score:>10.2f}% | {lat:>11.2f}s | {len(res):>6}")
    
    print("-" * 65)
    
    if results:
        best_model = max(results, key=lambda x: x[1])
        print(f"\n🏆 Best Model: {best_model[0]} - {best_model[1]:.2f}%")

def print_tool_report(results):
    print("\n\n" + "🛠️  TOOL BENCHMARK REPORT".center(65))
    print("-" * 65)
    print(f"{'Model':<30} | {'Score':<12} | {'Avg Latency':<12} | {'Tests':<8}")
    print("-" * 65)
    
    for model, score, lat, res in sorted(results, key=lambda x: x[1], reverse=True):
        print(f"{model:<30} | {score:>10.2f}% | {lat:>11.2f}s | {len(res):>6}")
    
    print("-" * 65)
    
    if results:
        best_model = max(results, key=lambda x: x[1])
        print(f"\n🏆 Best Model: {best_model[0]} - {best_model[1]:.2f}%")

def print_agent_report(results):
    """Prints the final summary report for Agent Mode evaluation."""
    print("\n\n" + "📊 AGENT BENCHMARK REPORT".center(65))
    print("-" * 65)
    print(f"{'Model':<30} | {'Score':<12} | {'Avg Latency':<12} | {'Tests':<8}")
    print("-" * 65)
    
    # Sort by score descending
    for model, score, lat, res in sorted(results, key=lambda x: x[1], reverse=True):
        print(f"{model:<30} | {score:>10.2f}% | {lat:>11.2f}s | {len(res):>6}")
    
    print("-" * 65)
    
    if results:
        best_model = max(results, key=lambda x: x[1])
        print(f"\n🏆 Best Agent Performer: {best_model[0]} - {best_model[1]:.2f}%")
        	
if __name__ == "__main__":
    banner()
    args = parse_arguments()
    
    if not check_server():
        print("❌ Ollama server not running at http://127.0.0.1:11434")
        sys.exit(1)
    
    if not args.no_pull:
        models = args.models.split(",") if args.models else BENCHMARK_CONFIG["models"]
        for m in models:
            pull_if_missing(m.strip())
    else:
        print("⏭️  Skipping model pulls")
    
    run_benchmark(args)