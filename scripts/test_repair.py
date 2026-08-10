import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ai_service.json_repair import parse_json, repair_json

# Test 1: trailing comma
t1 = '{"name": "test", "skills": ["a", "b"],}'
print("Test 1 (trailing comma):", parse_json(t1)["skills"])

# Test 2: single-quoted keys
t2 = """{'name': 'test', 'skills': ['a', 'b']}"""
print("Test 2 (single quotes):", parse_json(t2)["name"])

# Test 3: markdown fences
t3 = '```json\n{"name": "test"}\n```'
print("Test 3 (markdown):", parse_json(t3)["name"])

# Test 4: extra text around JSON
t4 = 'Here is the result: {"name": "test", "skills": []} Hope this helps!'
print("Test 4 (extra text):", parse_json(t4)["name"])

# Test 5: valid JSON passes through
t5 = '{"name": "test", "skills": ["a"]}'
print("Test 5 (valid):", parse_json(t5)["name"])

# Test 6: truncated JSON with missing closing brace
t6 = '{"name": "test", "skills": ["a"'
print("Test 6 (truncated):", parse_json(t6)["name"])

print("\nAll repair tests passed!")
