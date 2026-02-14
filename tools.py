# -*- coding: utf-8 -*-
# tools.py - Expanded Tool Registry with 25+ Real Tools

import os
import json
import math
import time
import random
import hashlib
import urllib.parse
from datetime import datetime, timedelta
import subprocess
import tempfile
import shutil
import re

class ToolRegistry:
    """Registry of actual callable tools - 25+ tools across 8 categories."""
    # ============ 1. WEATHER & ENVIRONMENT ============
    @staticmethod
    def get_weather(location, unit="celsius"):
        """Fetch real-time weather from wttr.in (free, no API key)."""
        try:
            import requests
            response = requests.get(
                f"https://wttr.in/{location}?format=%t+%C+%w+%h",
                timeout=10
            )
            if response.status_code == 200:
                parts = response.text.strip().split()
                temp = parts[0]
                condition = " ".join(parts[1:-2]) if len(parts) > 3 else "unknown"
                wind = parts[-2] if len(parts) > 2 else "?"
                humidity = parts[-1] if len(parts) > 1 else "?"
                
                return {
                    "location": location,
                    "temperature": temp,
                    "condition": condition,
                    "wind": wind,
                    "humidity": humidity,
                    "unit": unit,
                    "source": "wttr.in",
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            pass
        
        # Fallback simulation
        conditions = ["sunny", "cloudy", "rainy", "clear", "partly cloudy", "mist", "overcast", "stormy"]
        temps_c = random.randint(-5, 35)
        temps_f = int(temps_c * 9/5 + 32)
        
        return {
            "location": location,
            "temperature": f"{temps_c}°C" if unit == "celsius" else f"{temps_f}°F",
            "condition": random.choice(conditions),
            "wind": f"{random.randint(5, 30)} km/h",
            "humidity": f"{random.randint(30, 95)}%",
            "unit": unit,
            "source": "simulated",
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def get_forecast(location, days=5):
        """Get weather forecast for multiple days."""
        forecast = []
        for i in range(days):
            date = (datetime.now() + timedelta(days=i+1)).strftime("%Y-%m-%d")
            conditions = ["sunny", "cloudy", "rainy", "partly cloudy", "clear"]
            forecast.append({
                "date": date,
                "temperature_high": f"{random.randint(15, 30)}°C",
                "temperature_low": f"{random.randint(5, 15)}°C",
                "condition": random.choice(conditions),
                "precipitation": f"{random.randint(0, 80)}%"
            })
        
        return {
            "location": location,
            "forecast": forecast,
            "days": days,
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def get_air_quality(city):
        """Get air quality index (simulated)."""
        aqi_ranges = {
            "good": (0, 50),
            "moderate": (51, 100),
            "unhealthy_sensitive": (101, 150),
            "unhealthy": (151, 200),
            "very_unhealthy": (201, 300),
            "hazardous": (301, 500)
        }
        
        aqi = random.randint(20, 200)
        for level, (low, high) in aqi_ranges.items():
            if low <= aqi <= high:
                status = level.replace("_", " ")
                break
        
        pollutants = {
            "pm2.5": random.randint(5, 50),
            "pm10": random.randint(10, 100),
            "o3": random.randint(10, 100),
            "no2": random.randint(5, 60),
            "so2": random.randint(1, 30)
        }
        
        return {
            "city": city,
            "aqi": aqi,
            "status": status,
            "pollutants": pollutants,
            "dominant_pollutant": max(pollutants, key=pollutants.get),
            "timestamp": datetime.now().isoformat()
        }
    
    # ============ 2. MATHEMATICS & CALCULATIONS ============
    
    @staticmethod
    def calculator(expression):
        """Safe mathematical expression evaluator."""
        allowed_names = {
            k: v for k, v in math.__dict__.items() 
            if not k.startswith("__")
        }
        allowed_names.update({
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
            "sum": sum,
            "pow": pow,
            "sqrt": math.sqrt,
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "log": math.log,
            "log10": math.log10,
            "exp": math.exp,
            "pi": math.pi,
            "e": math.e
        })
        
        try:
            code = compile(expression, "<string>", "eval")
            
            for name in code.co_names:
                if name not in allowed_names:
                    raise NameError(f"Use of '{name}' not allowed")
            
            result = eval(code, {"__builtins__": {}}, allowed_names)
            
            return {
                "expression": expression,
                "result": result,
                "status": "success"
            }
        except Exception as e:
            return {
                "expression": expression,
                "error": str(e),
                "status": "error"
            }
    
    @staticmethod
    def convert_units(value, from_unit, to_unit):
        """Convert between different units."""
        conversions = {
            # Length
            ("meters", "feet"): lambda x: x * 3.28084,
            ("feet", "meters"): lambda x: x / 3.28084,
            ("kilometers", "miles"): lambda x: x * 0.621371,
            ("miles", "kilometers"): lambda x: x / 0.621371,
            ("inches", "cm"): lambda x: x * 2.54,
            ("cm", "inches"): lambda x: x / 2.54,
            # Weight
            ("kg", "lbs"): lambda x: x * 2.20462,
            ("lbs", "kg"): lambda x: x / 2.20462,
            # Temperature
            ("celsius", "fahrenheit"): lambda x: (x * 9/5) + 32,
            ("fahrenheit", "celsius"): lambda x: (x - 32) * 5/9,
            # Volume
            ("liters", "gallons"): lambda x: x * 0.264172,
            ("gallons", "liters"): lambda x: x / 0.264172,
        }
        
        key = (from_unit.lower(), to_unit.lower())
        if key in conversions:
            result = conversions[key](float(value))
            return {
                "value": value,
                "from_unit": from_unit,
                "to_unit": to_unit,
                "result": round(result, 4),
                "status": "success"
            }
        else:
            return {
                "error": f"Conversion from {from_unit} to {to_unit} not supported",
                "status": "error"
            }
    
    @staticmethod
    def generate_random_number(min_val=0, max_val=100):
        """Generate a random number between min and max."""
        return {
            "min": min_val,
            "max": max_val,
            "random": random.randint(min_val, max_val),
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def calculate_stats(numbers):
        """Calculate statistics for a list of numbers."""
        if isinstance(numbers, str):
            numbers = [float(x.strip()) for x in numbers.split(",")]
        
        n = len(numbers)
        if n == 0:
            return {"error": "Empty list"}
        
        mean = sum(numbers) / n
        variance = sum((x - mean) ** 2 for x in numbers) / n
        std_dev = variance ** 0.5
        
        numbers.sort()
        
        return {
            "count": n,
            "sum": sum(numbers),
            "mean": round(mean, 4),
            "median": numbers[n//2] if n % 2 else (numbers[n//2-1] + numbers[n//2])/2,
            "mode": max(set(numbers), key=numbers.count) if n > 1 else numbers[0],
            "min": min(numbers),
            "max": max(numbers),
            "range": max(numbers) - min(numbers),
            "variance": round(variance, 4),
            "std_deviation": round(std_dev, 4)
        }
    
    # ============ 3. DATABASE & USER MANAGEMENT ============
    
    _mock_users = {
        "john@example.com": {
            "user_id": 42,
            "name": "John Doe",
            "email": "john@example.com",
            "role": "developer",
            "department": "Engineering",
            "joined": "2023-01-15",
            "active": True,
            "projects": ["Project A", "Project C"]
        },
        "jane@example.com": {
            "user_id": 43,
            "name": "Jane Smith",
            "email": "jane@example.com",
            "role": "manager",
            "department": "Product",
            "joined": "2022-11-01",
            "active": True,
            "projects": ["Project B", "Project D"]
        },
        "alice@company.com": {
            "user_id": 44,
            "name": "Alice Johnson",
            "email": "alice@company.com",
            "role": "director",
            "department": "Executive",
            "joined": "2021-06-20",
            "active": True,
            "projects": ["All Projects"]
        },
        "bob@example.com": {
            "user_id": 45,
            "name": "Bob Wilson",
            "email": "bob@example.com",
            "role": "designer",
            "department": "Design",
            "joined": "2023-03-10",
            "active": False,
            "projects": ["Project C"]
        }
    }
    
    @staticmethod
    def find_user(email):
        """Look up user by email."""
        user = ToolRegistry._mock_users.get(email)
        if user:
            return {"status": "found", "user": user}
        return {"status": "not_found", "email": email}
    
    @staticmethod
    def get_user(user_id):
        """Look up user by ID."""
        if isinstance(user_id, str) and user_id.isdigit():
            user_id = int(user_id)
        
        for user in ToolRegistry._mock_users.values():
            if user["user_id"] == user_id:
                return {"status": "found", "user": user}
        
        return {"status": "not_found", "user_id": user_id}
    
    @staticmethod
    def list_users(active_only=True):
        """List all users."""
        users = list(ToolRegistry._mock_users.values())
        if active_only:
            users = [u for u in users if u["active"]]
        
        return {
            "total_users": len(users),
            "users": users,
            "active_only": active_only
        }
    
    @staticmethod
    def create_user(name, email, role="contributor"):
        """Create a new user (simulated)."""
        new_id = max([u["user_id"] for u in ToolRegistry._mock_users.values()]) + 1
        
        new_user = {
            "user_id": new_id,
            "name": name,
            "email": email,
            "role": role,
            "department": "New",
            "joined": datetime.now().strftime("%Y-%m-%d"),
            "active": True,
            "projects": []
        }
        
        ToolRegistry._mock_users[email] = new_user
        
        return {
            "status": "created",
            "user": new_user
        }
    
    # ============ 4. COMMUNICATION ============
    
    @staticmethod
    def send_email(to, subject, body, cc=None, bcc=None):
        """Simulate email sending with CC/BCC support."""
        print(f"\n      📧 SIMULATED EMAIL:")
        print(f"      To: {to}")
        if cc:
            print(f"      CC: {cc}")
        if bcc:
            print(f"      BCC: {bcc}")
        print(f"      Subject: {subject}")
        print(f"      Body: {body}")
        
        return {
            "status": "sent",
            "to": to,
            "cc": cc,
            "bcc": bcc,
            "subject": subject,
            "timestamp": datetime.now().isoformat(),
            "message_id": f"msg_{int(time.time())}_{random.randint(1000, 9999)}"
        }
    
    @staticmethod
    def generate_confirmation_code():
        """Generate a random confirmation code."""
        code = ''.join(random.choices('ABCDEFGHJKLMNPQRSTUVWXYZ23456789', k=8))
        return {
            "code": code,
            "expires_in": "15 minutes",
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def send_sms(phone_number, message):
        """Simulate SMS sending."""
        print(f"\n      📱 SIMULATED SMS:")
        print(f"      To: {phone_number}")
        print(f"      Message: {message}")
        
        return {
            "status": "sent",
            "to": phone_number,
            "message_length": len(message),
            "timestamp": datetime.now().isoformat()
        }
    
    # ============ 5. FILE SYSTEM ============
    
    @staticmethod
    def create_directory(path):
        """Create a directory on the filesystem."""
        try:
            path = os.path.expanduser(path)
            os.makedirs(path, exist_ok=True)
            
            return {
                "status": "created",
                "path": path,
                "exists": os.path.exists(path),
                "is_directory": os.path.isdir(path),
                "permissions": oct(os.stat(path).st_mode)[-3:] if os.path.exists(path) else None
            }
        except Exception as e:
            return {
                "status": "error",
                "path": path,
                "error": str(e)
            }
    
    @staticmethod
    def list_files(path=".", pattern=None):
        """List files in a directory, optionally filtered by pattern."""
        try:
            path = os.path.expanduser(path)
            files = os.listdir(path)
            
            if pattern:
                import fnmatch
                files = [f for f in files if fnmatch.fnmatch(f, pattern)]
            
            file_details = []
            for f in sorted(files)[:50]:  # Limit to 50 files
                full_path = os.path.join(path, f)
                try:
                    stat = os.stat(full_path)
                    file_details.append({
                        "name": f,
                        "type": "directory" if os.path.isdir(full_path) else "file",
                        "size": stat.st_size,
                        "size_human": ToolRegistry._human_readable_size(stat.st_size),
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "permissions": oct(stat.st_mode)[-3:]
                    })
                except:
                    pass
            
            return {
                "path": path,
                "files": file_details,
                "count": len(file_details),
                "total_items": len(os.listdir(path)),
                "status": "success"
            }
        except Exception as e:
            return {
                "path": path,
                "error": str(e),
                "status": "error"
            }
    
    @staticmethod
    def _human_readable_size(size):
        """Convert bytes to human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"
    
    @staticmethod
    def read_file(path, encoding="utf-8", max_lines=50):
        """Read a text file."""
        try:
            path = os.path.expanduser(path)
            with open(path, 'r', encoding=encoding) as f:
                lines = f.readlines()
            
            content = ''.join(lines[:max_lines])
            truncated = len(lines) > max_lines
            
            return {
                "path": path,
                "exists": True,
                "size": os.path.getsize(path),
                "lines": len(lines),
                "content": content,
                "truncated": truncated,
                "status": "success"
            }
        except Exception as e:
            return {
                "path": path,
                "error": str(e),
                "status": "error"
            }
    
    @staticmethod
    def write_file(path, content, append=False):
        """Write or append to a file."""
        try:
            path = os.path.expanduser(path)
            mode = 'a' if append else 'w'
            with open(path, mode, encoding='utf-8') as f:
                f.write(content)
            
            return {
                "path": path,
                "operation": "append" if append else "write",
                "bytes_written": len(content),
                "status": "success"
            }
        except Exception as e:
            return {
                "path": path,
                "error": str(e),
                "status": "error"
            }
    
    @staticmethod
    def delete_file(path):
        """Delete a file (use with caution!)."""
        try:
            path = os.path.expanduser(path)
            if os.path.isfile(path):
                os.remove(path)
                return {
                    "path": path,
                    "deleted": True,
                    "status": "success"
                }
            else:
                return {
                    "path": path,
                    "error": "Not a file or does not exist",
                    "status": "error"
                }
        except Exception as e:
            return {
                "path": path,
                "error": str(e),
                "status": "error"
            }
    
    # ============ 6. WEB & NETWORK ============
    
    @staticmethod
    def fetch_url(url, timeout=10):
        """Fetch content from a URL."""
        try:
            import requests
            headers = {
                'User-Agent': 'VTSTech-Benchmark/1.0'
            }
            response = requests.get(url, timeout=timeout, headers=headers)
            
            return {
                "url": url,
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "content_length": len(response.text),
                "content_preview": response.text[:500],
                "encoding": response.encoding,
                "status": "success"
            }
        except Exception as e:
            return {
                "url": url,
                "error": str(e),
                "status": "error"
            }
    
    @staticmethod
    def ping_host(host):
        """Ping a host (simulated)."""
        latencies = [random.randint(10, 100) for _ in range(4)]
        return {
            "host": host,
            "packets_sent": 4,
            "packets_received": random.randint(3, 4),
            "latency_ms": latencies,
            "average_latency": sum(latencies) / len(latencies),
            "status": "alive" if random.random() > 0.1 else "timeout",
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def encode_url(text):
        """URL encode a string."""
        return {
            "original": text,
            "encoded": urllib.parse.quote(text),
            "scheme": "url_encoding"
        }
    
    @staticmethod
    def decode_url(encoded):
        """URL decode a string."""
        return {
            "encoded": encoded,
            "decoded": urllib.parse.unquote(encoded),
            "scheme": "url_decoding"
        }
    
    # ============ 7. SECURITY & HASHING ============
    
    @staticmethod
    def hash_text(text, algorithm="sha256"):
        """Generate hash of text."""
        algorithms = {
            "md5": hashlib.md5,
            "sha1": hashlib.sha1,
            "sha256": hashlib.sha256,
            "sha512": hashlib.sha512
        }
        
        algo = algorithms.get(algorithm.lower(), hashlib.sha256)
        hash_obj = algo(text.encode())
        
        return {
            "text": text[:50] + "..." if len(text) > 50 else text,
            "algorithm": algorithm,
            "hash": hash_obj.hexdigest(),
            "hash_length": len(hash_obj.hexdigest())
        }
    
    @staticmethod
    def generate_password(length=12):
        """Generate a secure random password."""
        lowercase = 'abcdefghijklmnopqrstuvwxyz'
        uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        digits = '0123456789'
        symbols = '!@#$%^&*'
        
        all_chars = lowercase + uppercase + digits + symbols
        
        password = [
            random.choice(lowercase),
            random.choice(uppercase),
            random.choice(digits),
            random.choice(symbols)
        ]
        
        password += random.choices(all_chars, k=length-4)
        random.shuffle(password)
        
        password_str = ''.join(password)
        
        return {
            "password": password_str,
            "length": length,
            "strength": "strong" if length >= 12 else "moderate",
            "timestamp": datetime.now().isoformat()
        }
    
    # ============ 8. TIME & DATE ============
    
    @staticmethod
    def current_time(timezone="UTC"):
        """Get current date and time."""
        now = datetime.now()
        return {
            "timezone": timezone,
            "datetime": now.isoformat(),
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "timestamp": time.time(),
            "unix_timestamp": int(time.time()),
            "day_of_week": now.strftime("%A"),
            "day_of_year": now.timetuple().tm_yday,
            "week_number": now.isocalendar()[1]
        }
    
    @staticmethod
    def date_calculator(start_date, days_to_add=0, days_to_subtract=0):
        """Calculate dates by adding/subtracting days."""
        try:
            start = datetime.fromisoformat(start_date)
            
            if days_to_add:
                result = start + timedelta(days=days_to_add)
                operation = f"add {days_to_add} days"
            elif days_to_subtract:
                result = start - timedelta(days=days_to_subtract)
                operation = f"subtract {days_to_subtract} days"
            else:
                result = start
                operation = "no change"
            
            return {
                "start_date": start_date,
                "operation": operation,
                "result_date": result.isoformat(),
                "result_date_formatted": result.strftime("%B %d, %Y"),
                "days_difference": (result - start).days
            }
        except Exception as e:
            return {
                "start_date": start_date,
                "error": str(e),
                "status": "error"
            }
    
    @staticmethod
    def timezone_converter(time_str, from_tz, to_tz):
        """Convert time between timezones (simulated)."""
        offsets = {
            "UTC": 0,
            "EST": -5,
            "EDT": -4,
            "CST": -6,
            "CDT": -5,
            "MST": -7,
            "MDT": -6,
            "PST": -8,
            "PDT": -7,
            "GMT": 0,
            "CET": 1,
            "CEST": 2,
            "IST": 5.5,
            "JST": 9,
            "AEST": 10,
            "AEDT": 11
        }
        
        from_offset = offsets.get(from_tz.upper(), 0)
        to_offset = offsets.get(to_tz.upper(), 0)
        
        offset_diff = to_offset - from_offset
        
        # Parse time
        try:
            from datetime import time as dttime
            t = datetime.strptime(time_str, "%H:%M").time()
            dt = datetime.combine(datetime.today(), t)
            dt += timedelta(hours=offset_diff)
            converted_time = dt.strftime("%H:%M")
            
            return {
                "original_time": time_str,
                "original_timezone": from_tz,
                "converted_time": converted_time,
                "converted_timezone": to_tz,
                "offset_hours": offset_diff,
                "status": "success"
            }
        except Exception as e:
            return {
                "error": str(e),
                "status": "error"
            }


# ============ TOOL EXECUTION & VALIDATION ============

def execute_tool(tool_name, arguments):
    """Execute a tool by name with given arguments."""
    try:
        tool_func = getattr(ToolRegistry, tool_name)
        result = tool_func(**arguments)
        return result
    except AttributeError:
        return {"error": f"Tool '{tool_name}' not found"}
    except TypeError as e:
        return {"error": f"Invalid arguments for {tool_name}: {str(e)}"}
    except Exception as e:
        return {"error": str(e)}

def get_all_tools():
    """Return a list of all available tools with their signatures."""
    tools = []
    for attr_name in dir(ToolRegistry):
        attr = getattr(ToolRegistry, attr_name)
        if callable(attr) and not attr_name.startswith("_"):
            import inspect
            sig = inspect.signature(attr)
            tools.append({
                "name": attr_name,
                "signature": str(sig),
                "doc": attr.__doc__.strip() if attr.__doc__ else ""
            })
    return sorted(tools, key=lambda x: x["name"])

def validate_tool_call(response, expected_name, expected_args):
    """Validate that a response contains the expected tool call."""
    try:
        cleaned = response.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r'^```json\n?|```$', '', cleaned)
        
        data = json.loads(cleaned)
        
        # Extract tool name and arguments (various formats)
        if "tool_calls" in data:
            tool_call = data["tool_calls"][0]
            if tool_call.get("type") == "function":
                name = tool_call["function"]["name"]
                args = json.loads(tool_call["function"]["arguments"])
        elif "name" in data and "arguments" in data:
            name = data["name"]
            args = data["arguments"]
        elif "function" in data and "params" in data:
            name = data["function"]
            args = data["params"]
        else:
            return False
        
        # Check tool name
        if name != expected_name:
            return False
        
        # Flexible argument matching
        for key, expected_value in expected_args.items():
            if key not in args:
                return False
            
            actual = args[key]
            
            # Type coercion for integers
            if isinstance(expected_value, int):
                try:
                    actual = int(actual)
                except (ValueError, TypeError):
                    return False
            
            # Type coercion for floats
            elif isinstance(expected_value, float):
                try:
                    actual = float(actual)
                except (ValueError, TypeError):
                    return False
            
            # String matching - allow contains for certain fields
            if key in ["body", "subject", "message", "content"]:
                if expected_value.lower() not in str(actual).lower():
                    return False
            elif actual != expected_value:
                return False
        
        return True
        
    except Exception:
        return False

def is_tool_call(response):
    """Check if a response appears to be a tool call."""
    try:
        cleaned = response.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r'^```json\n?|```$', '', cleaned)
        
        data = json.loads(cleaned)
        return "tool_calls" in data or "name" in data or "function" in data
    except Exception:
        return False

ToolRegistry.create_folder = ToolRegistry.create_directory
ToolRegistry.mkdir = ToolRegistry.create_directory
ToolRegistry.get_temperature = ToolRegistry.get_weather
ToolRegistry.email = ToolRegistry.send_email
ToolRegistry.calc = ToolRegistry.calculator