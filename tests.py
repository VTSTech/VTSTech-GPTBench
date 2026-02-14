# -*- coding: utf-8 -*-
import re
from tools import validate_tool_call, is_tool_call

# ============ REGEX PATTERNS ============
RE_HEX_COLOR = re.compile(r'#?[0-9A-Fa-f]{6}\b|#?[0-9A-Fa-f]{3}\b')
RE_NUMBER_30 = re.compile(r'\b30\b')
RE_NUMBER_99 = re.compile(r'\b99\b')
RE_NUMBER_2 = re.compile(r'\b2\b')
RE_NUMBER_6 = re.compile(r'\b6\b')

# ============ INSTRUCT TEST SUITE ============
INSTRUCT_TEST_SUITE = [
    # ----- SHELL COMMANDS -----
    {"name": "S1: List Hidden", "prompt": "Linux command to list all files including hidden.",
     "validator": lambda x: any(cmd in x for cmd in ["ls -a", "ls -A", "ls -la", "ls -al", "ls -1a"])},
    
    {"name": "S2: Disk Free", "prompt": "Linux command to show human readable disk space.",
     "validator": lambda x: "df" in x.lower() and any(flag in x for flag in ["-h", "-H", "-k", "--human"])},
    
    {"name": "S3: Find Text", "prompt": "Linux command to search for the word 'error' in file 'app.log'.",
     "validator": lambda x: any(cmd in x.lower() for cmd in ["grep", "find"]) and "error" in x.lower()},
    
    {"name": "S4: Own Change", "prompt": "Linux command to change owner of 'web' to 'www-data'.",
     "validator": lambda x: "chown" in x and "www-data" in x and ("web" in x or "/var/www/html" in x or "/web" in x)},
    
    {"name": "S5: Port List", "prompt": "Linux command to list all open ports and the processes using them.",
     "validator": lambda x: any(cmd in x for cmd in ["netstat", "ss", "lsof"])},
    
    {"name": "S6: Process Kill", "prompt": "Linux command to kill process ID 1234.",
     "validator": lambda x: "kill" in x and "1234" in x},
    
    {"name": "S7: Create Dir", "prompt": "Linux command to create nested folders 'a/b/c'.",
     "validator": lambda x: "mkdir" in x and "a/b/c" in x},
    
    # ----- JSON FORMATTING -----
    {"name": "F1: JSON Array", "prompt": "List 'A, B, C' as a JSON array.",
     "validator": lambda x: ("A" in x and "B" in x and "C" in x) and 
                            (x.strip().startswith("[") or x.strip().startswith("{"))},
    
    {"name": "F2: JSON Pair", "prompt": "JSON object: 'Status: OK'.",
     "validator": lambda x: "status" in x.lower() and "ok" in x.lower() and ('{' in x or '"' in x)},
    
    {"name": "F3: CSV Extract", "prompt": "Extract 2nd column from CSV: 'Name,ID\\nVTSTech,101'",
     "validator": lambda x: "101" in x and "Name" not in x and "VTSTech" not in x},
    
    {"name": "F4: Lowercase", "prompt": "Convert 'HELLO' to lowercase.",
     "validator": lambda x: "hello" in x.lower().replace("<|system|>", "").strip()},
    
    {"name": "F5: JSON Nested", "prompt": "JSON: 'User' has 'ID' 1.",
     "validator": lambda x: '"user"' in x.lower() and '"id"' in x.lower() and '1' in x},
    
    {"name": "F6: No Spaces", "prompt": "Remove spaces from 'V T S'.",
     "validator": lambda x: "VTS" in x.upper().replace(" ", "").replace("<|SYSTEM|>", "")},
    
    {"name": "F7: Hex Color", "prompt": "Hex code for white.",
     "validator": lambda x: RE_HEX_COLOR.search(x) is not None},
    
    # ----- LOGIC & MATH -----
    {"name": "L1: Reverse Word", "prompt": "Reverse the word 'D-E-B-I-A-N'. Output only the result.",
     "validator": lambda x: x.strip().upper().replace("-", "").replace(" ", "") == "NAIBED"},
    
    {"name": "L2: Math Step", "prompt": "Calculate Step 1: 50 / 2 = [?]. Step 2: [Result] + 5 = [?]. Output only the final number.",
     "validator": lambda x: RE_NUMBER_30.search(x) is not None},
    
    {"name": "L3: Is Prime", "prompt": "Is 7 a prime number? (Yes/No).",
     "validator": lambda x: x.strip().lower()[:3] in ["yes", "no"]},
    
    {"name": "L4: Max Val", "prompt": "Largest of: 12, 99, 4.",
     "validator": lambda x: RE_NUMBER_99.search(x) is not None},
    
    {"name": "L5: Count Chars", "prompt": "Count the number of times the letter 's' appears in: s | t | a | t | u | s. Result only.",
     "validator": lambda x: RE_NUMBER_2.search(x) is not None},
    
    {"name": "L6: Simple Logic", "prompt": "If A is true and B is false, what is A AND B?",
     "validator": lambda x: "false" in x.lower()},
    
    {"name": "L7: Word Length", "prompt": "Length of 'Python'.",
     "validator": lambda x: RE_NUMBER_6.search(x) is not None},
    
    # ----- CONSTRAINTS -----
    {"name": "C1: No Letter E", "prompt": "Name a color that does not contain the letter 'e'.",
     "validator": lambda x: 'e' not in x.lower() and any(
         c in x.lower() for c in [
             "gray", "pink", "cyan", "brown", "gold", "tan",
             "sand", "lime", "coral", "ivory", "indigo", "navy",
             "blu", "aqua"
         ]
     )},
    
    {"name": "C2: One Word", "prompt": "Capital of Germany (1 word).",
     "validator": lambda x: "berlin" in x.lower()},
    
    {"name": "C3: No Numbers", "prompt": "Write the word for the digit '5'. No digits allowed.",
     "validator": lambda x: "five" in x.lower() and "5" not in x},
    
    {"name": "C4: Binary State", "prompt": "Light is switched twice. Initial: Off. Final?",
     "validator": lambda x: "off" in x.lower()},
]

# ============ TOOL TEST SUITE ============
TOOL_TEST_SUITE = [
    {
        "name": "TC1: Current Weather",
        "prompt": "What's the weather in London?",
        "expects_tool": True,
        "validator": lambda x: any(term in x.lower() for term in ["°c", "°f", "temperature", "cloudy", "sunny", "rain"])
    },
    {
        "name": "TC2: Weather with Units", 
        "prompt": "Temperature in Paris in celsius",
        "expects_tool": True,
        "validator": lambda x: "°c" in x.lower() or "celsius" in x.lower()
    },
    {
        "name": "TC3: Basic Math",
        "prompt": "Calculate 15 * 7",
        "expects_tool": True,
        "validator": lambda x: re.search(r'\b105\b', x) is not None
    },
    {
        "name": "TC4: Complex Math",
        "prompt": "What's the square root of 144?",
        "expects_tool": True,
        "validator": lambda x: re.search(r'\b12\b', x) is not None
    },
    {
        "name": "TC5: User Lookup",
        "prompt": "Find user with email john@example.com",
        "expects_tool": True,
        "validator": lambda x: "John Doe" in x
    },
    {
        "name": "TC6: User by ID",
        "prompt": "Get profile for user 42",
        "expects_tool": True,
        "validator": lambda x: "John Doe" in x
    },
    {
        "name": "TC7: Send Email",
        "prompt": "Email alice@company.com saying 'Meeting at 3pm'",
        "expects_tool": True,
        "validator": lambda x: "sent" in x.lower() or "success" in x.lower() or "email" in x.lower()
    },
    {
        "name": "TC8: File Operation",
        "prompt": "Create directory /tmp/benchmark_test",
        "expects_tool": True,
        "validator": lambda x: any(term in str(x).lower() for term in ["created", "success", "tmp"])
    },
    {
        "name": "TC9: No Tool Needed",
        "prompt": "What's the capital of France?",
        "expects_tool": False,
        "validator": lambda x: "Paris" in x and not is_tool_call(x)
    },
    {
        "name": "TC10: Ambiguous Query",
        "prompt": "Can you help me?",
        "expects_tool": False,
        "validator": lambda x: ("help" in x.lower() or "assist" in x.lower()) and not is_tool_call(x)
    },
        # Weather & Environment
    {
        "name": "TC11: Weather Forecast",
        "prompt": "What's the weather forecast for Paris for the next 3 days?",
        "expects_tool": True,
        "validator": lambda x: "forecast" in x.lower() or "day" in x.lower() or "°c" in x.lower()
    },
    {
        "name": "TC12: Air Quality",
        "prompt": "What's the air quality in London?",
        "expects_tool": True,
        "validator": lambda x: "aqi" in x.lower() or "air quality" in x.lower() or "pm2.5" in x.lower()
    },
    
    # Math & Stats
    {
        "name": "TC13: Unit Conversion",
        "prompt": "Convert 100 kilometers to miles",
        "expects_tool": True,
        "validator": lambda x: "62.1" in x or "miles" in x.lower()
    },
    {
        "name": "TC14: Statistics",
        "prompt": "Calculate stats for 5, 10, 15, 20, 25",
        "expects_tool": True,
        "validator": lambda x: "mean" in x.lower() or "average" in x.lower() or "15" in x
    },
    {
        "name": "TC15: Random Number",
        "prompt": "Give me a random number between 1 and 100",
        "expects_tool": True,
        "validator": lambda x: any(c.isdigit() for c in x) and "1" in x and "100" in x
    },
    
    # User Management
    {
        "name": "TC16: List Users",
        "prompt": "Show me all active users",
        "expects_tool": True,
        "validator": lambda x: "John" in x or "Jane" in x or "Alice" in x
    },
    {
        "name": "TC17: Create User",
        "prompt": "Create a new user named Sarah Jones with email sarah@example.com",
        "expects_tool": True,
        "validator": lambda x: "created" in x.lower() or "sarah" in x.lower()
    },
    
    # File System
    {
        "name": "TC18: List Files",
        "prompt": "What files are in the current directory?",
        "expects_tool": True,
        "validator": lambda x: any(ext in x.lower() for ext in [".py", ".md", ".txt", "file", "directory"])
    },
    {
        "name": "TC19: Read File",
        "prompt": "Read the file README.md",
        "expects_tool": True,
        "validator": lambda x: len(x) > 20  # Should return actual content
    },
    
    # Web & Network
    {
        "name": "TC20: Fetch URL",
        "prompt": "Fetch the content from https://example.com",
        "expects_tool": True,
        "validator": lambda x: "Example Domain" in x or "html" in x.lower()
    },
    {
        "name": "TC21: Encode URL",
        "prompt": "URL encode this string: hello world!",
        "expects_tool": True,
        "validator": lambda x: "hello%20world%21" in x or "%20" in x
    },
    
    # Security
    {
        "name": "TC22: Hash Text",
        "prompt": "Generate SHA256 hash of 'password123'",
        "expects_tool": True,
        "validator": lambda x: "8d969e" in str(x)  # SHA256 of 'password123'
    },
    {
        "name": "TC23: Generate Password",
        "prompt": "Generate a strong password",
        "expects_tool": True,
        "validator": lambda x: any(c.isupper() for c in x) and any(c.isdigit() for c in x) and any(c in "!@#$%^&*" for c in x)
    },
    
    # Time & Date
    {
        "name": "TC24: Date Calculator",
        "prompt": "What date is 30 days from 2026-02-13?",
        "expects_tool": True,
        "validator": lambda x: "2026-03-15" in x or "March 15" in x
    },
    {
        "name": "TC25: Timezone Converter",
        "prompt": "Convert 14:30 from EST to PST",
        "expects_tool": True,
        "validator": lambda x: "11:30" in x or "12:30" in x
    }    
]

AGENT_TEST_SUITE = [
    {
        "name": "A1: Weather Conversion",
        "prompt": "Get the weather for London and convert to Fahrenheit.",
        "validator": lambda x: any(term in str(x).lower() for term in ["london", "fahrenheit", "105", "\\u00b0f"])
    },
    {
        "name": "A2: User Email",
        "prompt": "Find user john@example.com and email him 'Hello'",
        "validator": lambda x: "john@example.com" in str(x) and "sent" in str(x).lower()
    },
    {
        "name": "A3: Secure User Email",
        "prompt": "Find user 42, generate a 12-char password for them, and email it.",
        "steps": ["get_user", "generate_password", "send_email"],
        "validator": lambda x: all(k in str(x).lower() for k in ["user_id\": 42", "password", "send_email"])
    }
]