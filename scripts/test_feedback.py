import httpx, json

r = httpx.get("http://localhost:8000/api/employees/1/feedback-loop", timeout=60)
print(f"Status: {r.status_code}")
data = r.json()
fb = data["feedback"]
print(f"Accuracy: {fb['prediction_accuracy']}")
print(f"Quality: {fb['hiring_quality']}")
print(f"Assessment: {fb['overall_assessment'][:150]}")
print(f"Lesson: {fb['lesson']}")
computed = fb["computed"]
print(f"Computed: ai_star={computed['ai_star']}, probation_avg={computed['probation_avg']}")
print(f"Validated strengths: {fb['validated_strengths']}")
print(f"Missed risks: {fb['missed_risks']}")
