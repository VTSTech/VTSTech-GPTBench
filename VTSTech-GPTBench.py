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
from prompts import INSTRUCT_SYSTEM_PROMPT, INSTRUCT_FEW_SHOT, TOOL_SYSTEM_PROMPT, TOOL_FEW_SHOT, PLANNER_SYSTEM_PROMPT, PLANNER_FEW_SHOT, AGENT_SYSTEM_PROMPT
from tests import INSTRUCT_TEST_SUITE, TOOL_TEST_SUITE, AGENT_TEST_SUITE
from tools import ToolRegistry, execute_tool, validate_tool_call, is_tool_call

# ============ CONFIGURATION ============
MODEL_NUM_PREDICT = {
    "llama3.2:1b": 128,
    "llama3.2:3b": 256,
    "gemma3:1b": 256,
    "gemma3:4b": 512,
    "granite3-moe:1b": 256,
    "granite3-moe:3b": 512,
    "qwen2.5:0.5b": 512,
    "qwen2.5:1.5b": 256,
    "qwen2.5-coder:0.5b": 128,
    "qwen2.5-coder:1.5b": 256,
    "qwen2.5-coder:0.5b-instruct-q4_k_m": 1024,
    "granite4:350m": 1024,
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
EXEC_MODEL = "qwen2.5-coder:0.5b-instruct-q4_k_m"

# ============ TOOL SCHEMA ============
# Tool schemas injected dynamically to prevent model confusion
# Maps the tool name to its strict expected JSON format
TOOL_SCHEMAS = {
    # 1. WEATHER & ENVIRONMENT
    "get_weather": '{"name": "get_weather", "arguments": {"location": "string"}}',
    "get_forecast": '{"name": "get_forecast", "arguments": {"location": "string", "days": "integer"}}',
    "get_air_quality": '{"name": "get_air_quality", "arguments": {"city": "string"}}',
    
    # 2. MATHEMATICS & CALCULATIONS
    "calculator": '{"name": "calculator", "arguments": {"expression": "string"}}',
    "convert_units": '{"name": "convert_units", "arguments": {"value": "number", "from_unit": "string", "to_unit": "string"}}',
    "generate_random_number": '{"name": "generate_random_number", "arguments": {"min_val": "integer", "max_val": "integer"}}',
    "calculate_stats": '{"name": "calculate_stats", "arguments": {"numbers": "array of numbers"}}',
    
    # 3. DATABASE & USER MANAGEMENT
    "find_user": '{"name": "find_user", "arguments": {"name": "string"}}',
    "get_user": '{"name": "get_user", "arguments": {"user_id": "integer"}}',
    "list_users": '{"name": "list_users", "arguments": {"active_only": "boolean"}}',
    "create_user": '{"name": "create_user", "arguments": {"name": "string", "email": "string", "role": "string"}}',
    
    # 4. COMMUNICATION
    "send_email": '{"name": "send_email", "arguments": {"to": "string", "subject": "string", "body": "string"}}',
    "send_sms": '{"name": "send_sms", "arguments": {"phone_number": "string", "message": "string"}}',
    "generate_confirmation_code": '{"name": "generate_confirmation_code", "arguments": {}}',
    
    # 5. FILE SYSTEM
    "create_directory": '{"name": "create_directory", "arguments": {"path": "string"}}',
    "list_files": '{"name": "list_files", "arguments": {"path": "string"}}',
    "read_file": '{"name": "read_file", "arguments": {"path": "string"}}',
    "write_file": '{"name": "write_file", "arguments": {"path": "string", "content": "string"}}',
    "delete_file": '{"name": "delete_file", "arguments": {"path": "string"}}',
    
    # 6. WEB & NETWORK
    "fetch_url": '{"name": "fetch_url", "arguments": {"url": "string"}}',
    "ping_host": '{"name": "ping_host", "arguments": {"host": "string"}}',
    "encode_url": '{"name": "encode_url", "arguments": {"text": "string"}}',
    "decode_url": '{"name": "decode_url", "arguments": {"encoded": "string"}}',
    
    # 7. SECURITY & HASHING
    "hash_text": '{"name": "hash_text", "arguments": {"text": "string", "algorithm": "string"}}',
    "generate_password": '{"name": "generate_password", "arguments": {"length": "integer"}}',
    
    # 8. TIME & DATE
    "current_time": '{"name": "current_time", "arguments": {"timezone": "string"}}',
    "date_calculator": '{"name": "date_calculator", "arguments": {"start_date": "string", "days_to_add": "integer"}}',
    "timezone_converter": '{"name": "timezone_converter", "arguments": {"time_str": "string", "from_tz": "string", "to_tz": "string"}}',
    
    # ALIAS MAPPINGS (In case the planner outputs an alias instead of the canonical name)
    "calc": '{"name": "calculator", "arguments": {"expression": "string"}}',
    "mkdir": '{"name": "create_directory", "arguments": {"path": "string"}}',
    "email": '{"name": "send_email", "arguments": {"to": "string", "subject": "string", "body": "string"}}',
    "weather": '{"name": "get_weather", "arguments": {"location": "string"}}'
}
# ============ HELPER FUNCTIONS ============
def banner():
    print(f"VTSTech-GPTBench R7")
    print(f"https://www.vts-tech.org https://github.com/VTSTech/VTSTech-GPTBench\n")

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="VTSTech-GPTBench – Evaluate tiny LLMs on Ollama",
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
    parser.add_argument("--mode", "-M", choices=["instruct", "tool", "agent", "run-tools", "all"], default="instruct",
                       help="Benchmark mode: instruct, tool, agent, run-tools or all")
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
        "options": {
            "temperature": 0,
            "num_predict": MODEL_NUM_PREDICT.get(model, 256)
        }        
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

		# Force decoding of unicode escapes if the model outputted literal backslashes
    try:
        # This converts literal \u00b0 strings into the actual character
        text = text
    except:
        pass
    return text    
    # Keep only printable characters
    text = "".join(char for char in text if char.isprintable())
    text = text.strip()
    
    # Remove surrounding quotes
    if (text.startswith('"') and text.endswith('"')) or \
       (text.startswith("'") and text.endswith("'")) or \
       (text.startswith('`') and text.endswith('`')):
        text = text[1:-1]
    
    return text.strip()
    
def robust_execute(t_name, t_args):
    """Execute a tool with flexible argument mapping."""
    if t_args is None:
        t_args = {}

    # Unwrap nested 'input' (some models wrap arguments)
    if isinstance(t_args, dict) and "input" in t_args:
        t_args = t_args["input"]

    # Tool‑specific argument normalization
    if t_name == "find_user":
        # ToolRegistry.find_user expects 'email'
        if "email" not in t_args:
            if "username" in t_args:
                t_args["email"] = t_args["username"]
                del t_args["username"]
            elif "name" in t_args:
                # Last resort: treat name as email (may fail, but better than nothing)
                t_args["email"] = t_args["name"]
                del t_args["name"]
            elif "user_id" in t_args:
                # Can't find user by ID with find_user; convert to get_user?
                # We'll just pass and let execute_tool fail.
                pass

    elif t_name == "get_user":
        # ToolRegistry.get_user expects 'user_id' (int)
        if "user_id" not in t_args:
            if "id" in t_args:
                try:
                    t_args["user_id"] = int(t_args["id"])
                except:
                    t_args["user_id"] = t_args["id"]
                del t_args["id"]
            elif "userid" in t_args:
                try:
                    t_args["user_id"] = int(t_args["userid"])
                except:
                    t_args["user_id"] = t_args["userid"]
                del t_args["userid"]

    elif t_name == "get_weather":
        # Expects 'location'
        if "location" not in t_args:
            if "city" in t_args:
                t_args["location"] = t_args["city"]
                del t_args["city"]
            elif "place" in t_args:
                t_args["location"] = t_args["place"]
                del t_args["place"]

    elif t_name == "get_air_quality":
        # Expects 'city'
        if "city" not in t_args:
            if "location" in t_args:
                t_args["city"] = t_args["location"]
                del t_args["location"]

    elif t_name == "generate_password":
        # Expects 'length' (int)
        if "length" not in t_args:
            t_args["length"] = 12
        else:
            try:
                t_args["length"] = int(t_args["length"])
            except:
                t_args["length"] = 12

    elif t_name == "encode_url":
		    if "url" in t_args and "text" not in t_args:
		        t_args["text"] = t_args["url"]
		        del t_args["url"]
    elif t_name == "random_number":
		    t_name = "generate_random_number"
		    
    return execute_tool(t_name, t_args)

def get_available_tools_list():
    # Gets all static methods from ToolRegistry that don't start with _
    return [func for func in dir(ToolRegistry) if not func.startswith("_") 
            and callable(getattr(ToolRegistry, func))]

def run_all_tools_logic():
    """Iterates through ToolRegistry and executes every tool with sample data."""
    print(f"\n🛠️  EXECUTING ALL REGISTERED TOOLS")
    print("-" * 45)
    
    # Unified sample data mapping
    sample_data = {
        "get_weather": {"location": "London"},
        "get_temperature": {"location": "London"}, # Alias
        "get_forecast": {"location": "New York", "days": 3},
        "get_air_quality": {"city": "Tokyo"},
        "calculator": {"expression": "sqrt(144) + 10"},
        "calc": {"expression": "10 + 10"}, # Alias
        "convert_units": {"value": 100, "from_unit": "miles", "to_unit": "kilometers"},
        "generate_random_number": {"min_val": 1, "max_val": 50},
        "calculate_stats": {"numbers": [10, 20, 30, 40, 50]},
        "create_directory": {"path": "test_bench_dir"},
        "create_folder": {"path": "test_folder"}, # Alias
        "mkdir": {"path": "test_mkdir"}, # Alias
        "list_files": {"path": "."},
        "read_file": {"path": "tools.py"},
        "write_file": {"path": "test.txt", "content": "Hello Bench"},
        "delete_file": {"path": "test.txt"},
        "get_user": {"user_id": 1},
        "find_user": {"name": "John Doe"}, # Changed from query
        "create_user": {"name": "VTSTech", "email": "nospam@vts-tech.org"},
        "send_email": {"to": "test@example.com", "subject": "Bench", "body": "Hello"},
        "email": {"to": "test@example.com", "subject": "Bench", "body": "Hello"}, # Alias
        "send_sms": {"phone_number": "555-0199", "message": "Test SMS"},
        "current_time": {},
        "date_calculator": {"base_date": "2026-02-13", "days": 30},
        "timezone_converter": {"time_str": "14:30", "from_tz": "EST", "to_tz": "PST"},
        "hash_text": {"text": "password123", "algorithm": "sha256"},
        "generate_password": {"length": 12},
        "decode_url": {"encoded": "https%3A%2F%2Fvts-tech.org"},
        "encode_url": {"text": "https://vts-tech.org"},
        "fetch_url": {"url": "https://wttr.in/London?format=3"},
        "ping_host": {"host": "8.8.8.8"}
    }

    methods = [m for m in dir(ToolRegistry) if not m.startswith('_') and callable(getattr(ToolRegistry, m))]

    for method_name in methods:
        # Skip class methods or internal stuff
        if method_name in ['execute_tool', 'validate_tool_call']: continue
        
        print(f"Running {method_name:<25}", end=" -> ", flush=True)
        try:
            func = getattr(ToolRegistry, method_name)
            args = sample_data.get(method_name, {})
            
            # Use inspect to only pass valid arguments if you want to be extra safe
            result = func(**args)
            print(f"✅ SUCCESS\n{result}")
        except Exception as e:
            print(f"❌ FAILED: {str(e)}")    
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
                print(f"    └─ Raw: \"{raw_display}\"".encode('utf-8').decode('unicode_escape'))
            
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
                
def evaluate_model_agent(model, planner, args):
    """Executes a multi-step ReAct-style workflow."""    
    passed_count = 0
    total_time = 0
    test_results = []
    
    print(f"\n🚀 EVALUATING AGENT: [Planner: {planner}] [Tools/Synthesis: {model}]")
    print("-" * 55)

    for test in AGENT_TEST_SUITE:
        print(f"Agent Task: {test['name']:<25}", end=" ", flush=True)
        start_time = time.perf_counter()
        
        try:
            # --- STEP 1: PLANNING ---
            plan_msg = [
                {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
                {"role": "user", "content": test['prompt']}
            ]
            
            raw_plan = ollama_chat_http(planner, plan_msg, format="json")
            if args.verbose: print(f"\n[debug] raw_plan: {raw_plan}".encode('utf-8').decode('unicode_escape'))
            
            # THE LIST ENFORCER: Force the planner output into a clean list
            try:
                plan_data = json.loads(sanitize_output(raw_plan))
                if isinstance(plan_data, dict):
                    steps = list(plan_data.keys())
                elif isinstance(plan_data, list):
                    steps = plan_data
                else:
                    steps = [str(plan_data)]
            except:
                steps = []
            
            # --- STEP 2: PROGRESSIVE EXECUTION ---
            context_so_far = []
            
            for step_tool in steps:
                schema_hint = TOOL_SCHEMAS.get(step_tool, '{"name": "tool_name", "arguments": {}}')
                context_str = json.dumps(context_so_far, ensure_ascii=False)
                # We feed the context so far into the next tool call
                exec_msg = [
                {"role": "system", "content": f"{TOOL_SYSTEM_PROMPT}\nREQUIRED SCHEMA: {TOOL_SCHEMAS.get(step_tool)}"},
                {"role": "user", "content": f"TASK: {test['prompt']}\n\nPREVIOUS RESULTS: {context_str}\n\nAction: Generate the JSON call for '{step_tool}'. Use data from PREVIOUS RESULTS if needed."}
                ]
                
                tool_call_raw = ollama_chat_http(model, exec_msg)
                cleaned_call = sanitize_output(tool_call_raw)
                if args.verbose: print(f"[debug] tool_call_raw: {cleaned_call}".encode('utf-8').decode('unicode_escape'))
                
                if is_tool_call(cleaned_call):
                    try:
                        call_data = json.loads(cleaned_call)
                        t_name = call_data.get("name", step_tool)
                        t_args = call_data.get("arguments", {})
                        
                        # Use our new robust mapping wrapper
                        output = robust_execute(t_name, t_args)
                        context_so_far.append({"tool": t_name, "result": output})
                    except Exception as e:
                        context_so_far.append({"tool": step_tool, "error": str(e)})
                else:
                    context_so_far.append({"tool": step_tool, "response": cleaned_call})

            # --- STEP 3: FINAL SYNTHESIS ---
            synthesis_input = f"User Request: {test['prompt']}\nExecution Results: {json.dumps(context_so_far)}"
            synthesis_msg = [
                {"role": "system", "content": AGENT_SYSTEM_PROMPT},
                {"role": "user", "content": synthesis_input}
            ]
            
            final_answer = ollama_chat_http(model, synthesis_msg)
            if args.verbose: print(f"[debug] final_answer: {final_answer}".encode('utf-8').decode('unicode_escape'))
            
            # --- STEP 4: VALIDATION ---
            is_pass = test["validator"](final_answer)
            
            duration = time.perf_counter() - start_time
            total_time += duration
            if is_pass: passed_count += 1
            
            test_results.append({
                "model": model, "test": test['name'], "pass": is_pass, "latency": duration
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
                tool_result = robust_execute(tool_name, tool_args)
                
                # Add tool call and result to conversation
                messages = [
                    {"role": "system", "content": TOOL_SYSTEM_PROMPT},
                    {"role": "user", "content": test['prompt']},
                    {"role": "assistant", "content": raw_content.strip()},
                    {
                        "role": "tool",
                        "content": json.dumps(tool_result) if isinstance(tool_result, dict) else str(tool_result),
                        "name": tool_name
                    },
                    # Force natural language response
                    {"role": "user", "content": "Now answer the original request in plain English using the tool result."}
                ]               
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
                    print(f"\n      ├─ Tool Call: {tool_name}({tool_args})".encode('utf-8').decode('unicode_escape'))
                    print(f"      ├─ Tool Result: {json.dumps(tool_result)[:250]}".encode('utf-8').decode('unicode_escape'))
                    print(f"      └─ Final: {content[:250]}".encode('utf-8').decode('unicode_escape'))
            
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

    if args.mode in ["all", "agent"]:
        print("\n🛠️  AGENT BENCHMARK MODE")
        print("=======================================================")
        agent_results = []
        result = evaluate_model_agent(EXEC_MODEL, PLANNER_MODEL, args)
        agent_results.append(result)
        print_agent_report(agent_results)
                        
    if args.mode in ["instruct", "all"]:
        print_instruct_report(instruct_results)
    
    if args.mode in ["tool", "all"]:
        print_tool_report(tool_results)

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
    print("\n\n" + "📊 AGENT BENCHMARK REPORT".center(65))
    print("-" * 65)
    print(f"{'Model':<30} | {'Score':<12} | {'Avg Latency':<12} | {'Tests':<8}")
    print("-" * 65)
    for model, score, lat, res in sorted(results, key=lambda x: x[1], reverse=True):
        print(f"{model:<30} | {score:>10.2f}% | {lat:>11.2f}s | {len(res):>6}")
    print("-" * 65)
        	
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
            
    if args.mode == "run-tools":
        run_all_tools_logic()
        sys.exit(0)
    
    run_benchmark(args)