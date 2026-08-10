"""Test role-aware resume parsing, classification, and prompt building.

Run from backend dir: cd backend && .venv\Scripts\python.exe ..\scripts\test_role_aware.py
"""
import sys, json
from pathlib import Path

# Add project root for ai_service imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
# Add backend for models/services imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

# --- Test 1: Role classifier ---
from services.resume_service import classify_role_from_title, get_role_category

print("=" * 60)
print("Test 1: Role classifier (classify_role_from_title)")
print("=" * 60)

tech_titles = [
    "高级后端工程师", "React前端开发", "DevOps运维工程师",
    "Android 开发工程师", "嵌入式系统工程师", "数据工程师",
    "算法工程师", "全栈工程师", "Java架构师", "安全工程师",
]
design_titles = [
    "UI设计师", "UX体验设计师", "品牌视觉设计师",
    "三维设计师", "插画师", "动效设计师",
]
generic_titles = [
    "产品经理", "运营总监", "销售经理", "市场专员", "人事主管",
]

for t in tech_titles:
    result = classify_role_from_title(t)
    status = "OK" if result == "tech" else f"FAIL (got {result})"
    print(f"  {t:20s} -> tech    [{status}]")

for t in design_titles:
    result = classify_role_from_title(t)
    status = "OK" if result == "design" else f"FAIL (got {result})"
    print(f"  {t:20s} -> design  [{status}]")

for t in generic_titles:
    result = classify_role_from_title(t)
    status = "OK" if result == "generic" else f"FAIL (got {result})"
    print(f"  {t:20s} -> generic [{status}]")


# --- Test 2: get_role_category (job_profile vs fallback) ---
print("\n" + "=" * 60)
print("Test 2: get_role_category (priority order)")
print("=" * 60)

class MockJob:
    def __init__(self, title, job_profile):
        self.title = title
        self.job_profile = job_profile

assert get_role_category(MockJob("随便", {"role_category": "design"})) == "design"
print("  job_profile.role_category=design -> design [OK]")

assert get_role_category(MockJob("高级前端工程师", {"weight": {}})) == "tech"
print("  title='高级前端工程师', no role_category -> tech [OK]")

assert get_role_category(MockJob("UI设计师", {"role_category": "invalid"})) == "design"
print("  title='UI设计师', invalid role_category -> design (fallback) [OK]")

assert get_role_category(None) == "generic"
print("  None job -> generic [OK]")


# --- Test 3: Prompt builder ---
from ai_service.analyzers.resume_parser import _build_system_prompt

print("\n" + "=" * 60)
print("Test 3: _build_system_prompt")
print("=" * 60)

tech_prompt = _build_system_prompt("tech")
assert "tech_stack_depth" in tech_prompt
assert "github_username" in tech_prompt
assert "portfolio_url" not in tech_prompt
assert "技术岗位特化" in tech_prompt
print("  tech prompt: OK")

design_prompt = _build_system_prompt("design")
assert "portfolio_url" in design_prompt
assert "design_tools" in design_prompt
assert "tech_stack_depth" not in design_prompt
assert "设计岗位特化" in design_prompt
print("  design prompt: OK")

generic_prompt = _build_system_prompt("generic")
assert "tech_stack_depth" not in generic_prompt
assert "portfolio_url" not in generic_prompt
print("  generic prompt: OK")

default_prompt = _build_system_prompt("generic")
assert "name" in default_prompt and "skills" in default_prompt
print("  backward compat (base fields): OK")


# --- Test 4: MockProvider role detection ---
from ai_service.providers.deepseek import MockProvider

print("\n" + "=" * 60)
print("Test 4: MockProvider role detection")
print("=" * 60)

mock = MockProvider()

tech_result = mock.chat("技术岗位特化解析要求：分析简历", "某后端工程师简历")
tech_data = json.loads(tech_result)
assert "tech_stack_depth" in tech_data
assert tech_data.get("name") == "李四"
print(f"  tech mock: name={tech_data['name']}, has tech_stack_depth [OK]")

design_result = mock.chat("设计岗位特化解析要求：分析简历", "某UI设计师简历")
design_data = json.loads(design_result)
assert "portfolio_url" in design_data
assert design_data.get("name") == "王五"
print(f"  design mock: name={design_data['name']}, has portfolio_url [OK]")

generic_result = mock.chat("专业的简历解析专家", "某候选人简历")
generic_data = json.loads(generic_result)
assert generic_data.get("name") == "张三"
print(f"  generic mock: name={generic_data['name']} [OK]")


# --- Test 5: JD Analyzer _validate ---
from ai_service.analyzers.jd_analyzer import _validate

print("\n" + "=" * 60)
print("Test 5: JD Analyzer _validate with role_category")
print("=" * 60)

valid = {
    "responsibilities": ["a"], "required_skills": ["b"], "skill_tags": ["c"],
    "experience_requirements": {"years_min": 1},
    "weight_distribution": {"a": 50, "b": 50},
}
_validate(valid)
print("  without role_category: OK")

_validate({**valid, "role_category": "tech"})
print("  with role_category=tech: OK")


# --- Test 6: GitHub API (network required) ---
from ai_service.integrations.github import fetch_github_profile

print("\n" + "=" * 60)
print("Test 6: GitHub API")
print("=" * 60)

result = fetch_github_profile("torvalds")
if result:
    print(f"  torvalds: repos={result['public_repos']}, stars={result['total_stars']}, "
          f"languages={result['top_languages']} [OK]")
else:
    print("  torvalds: API unavailable (rate limit/network) [SKIP]")

result = fetch_github_profile("this-user-definitely-does-not-exist-xyz-12345")
assert result is None
print("  invalid user: correctly None [OK]")

result = fetch_github_profile("")
assert result is None
print("  empty string: correctly None [OK]")

print("\n" + "=" * 60)
print("All tests complete!")
print("=" * 60)
