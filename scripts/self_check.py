"""Self-check: verify all modules, endpoints, and logic work correctly."""
import sys, json, time
from pathlib import Path

PROJECT = Path(r"D:\honor share\ai-recruiting-saas")
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "backend"))

print("=" * 60)
print("SELF-CHECK — ai-recruiting-saas")
print("=" * 60)

errors = []
warnings = []

# --- 1. Module imports ---
print("\n[1/6] Module imports...")
modules = {
    "ai_service.json_repair": PROJECT / "ai_service/json_repair.py",
    "ai_service.base": PROJECT / "ai_service/base.py",
    "ai_service.analyzers.resume_parser": PROJECT / "ai_service/analyzers/resume_parser.py",
    "ai_service.analyzers.matcher": PROJECT / "ai_service/analyzers/matcher.py",
    "ai_service.analyzers.jd_analyzer": PROJECT / "ai_service/analyzers/jd_analyzer.py",
    "ai_service.providers.deepseek": PROJECT / "ai_service/providers/deepseek.py",
    "ai_service.integrations.github": PROJECT / "ai_service/integrations/github.py",
    "services.resume_service": PROJECT / "backend/services/resume_service.py",
    "services.jd_service": PROJECT / "backend/services/jd_service.py",
    "models.employee": PROJECT / "backend/models/employee.py",
    "models.job": PROJECT / "backend/models/job.py",
}

for name, path in modules.items():
    if not path.exists():
        errors.append(f"MISSING: {path}")
        continue
    try:
        __import__(name)
        print(f"  OK  {name}")
    except Exception as e:
        errors.append(f"IMPORT FAIL: {name} — {e}")

# --- 2. Resume parser role-aware ---
print("\n[2/6] Resume parser role-aware...")
from ai_service.analyzers.resume_parser import _build_system_prompt, parse_resume

for rc in ["tech", "design", "generic"]:
    prompt = _build_system_prompt(rc)
    if rc == "tech":
        if "tech_stack_depth" not in prompt:
            errors.append(f"tech prompt missing tech_stack_depth")
        if "portfolio_url" in prompt:
            errors.append("tech prompt should NOT have portfolio_url")
    elif rc == "design":
        if "portfolio_url" not in prompt:
            errors.append("design prompt missing portfolio_url")
        if "tech_stack_depth" in prompt:
            errors.append("design prompt should NOT have tech_stack_depth")
    elif rc == "generic":
        if "tech_stack_depth" in prompt or "portfolio_url" in prompt:
            errors.append("generic prompt has role-specific fields")
print("  OK  all role prompts correct")

# Signature check
import inspect
sig = inspect.signature(parse_resume)
if "role_category" not in sig.parameters:
    errors.append("parse_resume missing role_category parameter")
if sig.parameters["role_category"].default != "generic":
    warnings.append("parse_resume role_category default should be 'generic'")
print(f"  OK  parse_resume signature: {sig}")

# --- 3. Role classifier ---
print("\n[3/6] Role classifier...")
from services.resume_service import classify_role_from_title, get_role_category, ROLE_KEYWORDS

tests = [
    ("高级后端工程师", "tech"),
    ("React前端开发", "tech"),
    ("Java架构师", "tech"),
    ("Go后端开发", "tech"),
    ("UI设计师", "design"),
    ("UX体验设计师", "design"),
    ("品牌设计师", "design"),
    ("产品经理", "generic"),
    ("运营总监", "generic"),
    ("销售经理", "generic"),
]
for title, expected in tests:
    result = classify_role_from_title(title)
    if result != expected:
        errors.append(f"classify_role_from_title('{title}') = '{result}', expected '{expected}'")
print(f"  OK  {len(tests)} title tests passed")

# get_role_category edge cases
class MockJob:
    def __init__(self, title, profile):
        self.title = title
        self.job_profile = profile

assert get_role_category(MockJob("x", {"role_category": "tech"})) == "tech"
assert get_role_category(MockJob("前端工程师", {})) == "tech"
assert get_role_category(MockJob("UI设计师", {"role_category": None})) == "design"
assert get_role_category(MockJob("产品经理", {})) == "generic"
assert get_role_category(None) == "generic"
print("  OK  get_role_category edge cases")

# Verify keyword coverage
if "后端" not in ROLE_KEYWORDS["tech"]:
    errors.append("ROLE_KEYWORDS missing 后端")
if "前端" not in ROLE_KEYWORDS["tech"]:
    errors.append("ROLE_KEYWORDS missing 前端")
if "UI" not in ROLE_KEYWORDS["design"]:
    errors.append("ROLE_KEYWORDS missing UI")
print("  OK  keyword coverage check")

# --- 4. JSON repair ---
print("\n[4/6] JSON repair...")
from ai_service.json_repair import parse_json as rj_parse

repair_tests = [
    ('{"name": "test", "skills": ["a", "b"],}', {"name": "test"}),
    ('{"name": "test"}', {"name": "test"}),
    ('```json\n{"name": "test"}\n```', {"name": "test"}),
    ('prefix {"name": "test"} suffix', {"name": "test"}),
]
for text, expected in repair_tests:
    try:
        result = rj_parse(text)
        for k, v in expected.items():
            if result.get(k) != v:
                errors.append(f"JSON repair: expected {k}={v}, got {result.get(k)}")
    except Exception as e:
        errors.append(f"JSON repair failed on '{text[:50]}': {e}")
print(f"  OK  {len(repair_tests)} JSON repair tests")

# --- 5. MockProvider routing ---
print("\n[5/6] MockProvider routing...")
from ai_service.providers.deepseek import MockProvider
mock = MockProvider()

# Tech resume
r = json.loads(mock.chat("技术岗位特化解析：简历文本分析", "简历内容"))
if r.get("name") != "李四" or "tech_stack_depth" not in r:
    errors.append(f"MockProvider tech route: got name={r.get('name')}, tech_stack_depth={'PRESENT' if 'tech_stack_depth' in r else 'MISSING'}")

# Design resume
r = json.loads(mock.chat("设计岗位特化解析：简历文本分析", "简历内容"))
if r.get("name") != "王五" or "portfolio_url" not in r:
    errors.append(f"MockProvider design route: got name={r.get('name')}, portfolio_url={'PRESENT' if 'portfolio_url' in r else 'MISSING'}")

# Generic resume
r = json.loads(mock.chat("简历解析专家分析简历", "简历内容"))
if r.get("name") != "张三":
    errors.append(f"MockProvider generic route: got name={r.get('name')}")

# Job profile
r = json.loads(mock.chat("extract from JD: analyze this job", "岗位描述"))
if r.get("role_category") != "tech":
    errors.append(f"MockProvider job_profile missing role_category")
print("  OK  all MockProvider routes")

# --- 6. API endpoints ---
print("\n[6/6] API endpoints...")
import httpx
BASE = "http://localhost:8000"

endpoints = [
    ("GET", "/api/dashboard/stats", 200),
    ("GET", "/api/jobs", 200),
    ("GET", "/api/employees", 200),
    ("GET", "/api/employees/stats", 200),
    ("GET", "/api/talent-pool", 200),
    # File preview
    ("GET", "/api/employees/1/file?type=diploma", 200),
    ("GET", "/api/employees/1/file?type=id_card", 404),
    ("GET", "/api/employees/99999/file?type=diploma", 404),
    ("GET", "/api/employees/1/file?type=invalid", 400),
]

for method, path, expected_status in endpoints:
    try:
        r = httpx.request(method, f"{BASE}{path}", timeout=10)
        if r.status_code != expected_status:
            errors.append(f"API {method} {path}: expected {expected_status}, got {r.status_code}")
    except Exception as e:
        errors.append(f"API {method} {path}: connection error — {e}")
print(f"  OK  {len(endpoints)} endpoint checks")

# --- Summary ---
print("\n" + "=" * 60)
if errors:
    print(f"ERRORS ({len(errors)}):")
    for e in errors:
        print(f"  ❌ {e}")
if warnings:
    print(f"WARNINGS ({len(warnings)}):")
    for w in warnings:
        print(f"  ⚠ {w}")

if not errors and not warnings:
    print("ALL CHECKS PASSED ✅")
elif not errors:
    print("PASSED WITH WARNINGS ⚠")
else:
    print(f"FAILED — {len(errors)} errors")
print("=" * 60)
