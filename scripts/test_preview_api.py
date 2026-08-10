import httpx

# Test 1: diploma preview
r = httpx.get("http://localhost:8000/api/employees/1/file", params={"type": "diploma"})
print("Diploma preview:", r.status_code)
print("Content-Type:", r.headers.get("content-type"))
print("Content:", r.text[:80])

# Test 2: id_card not found
r = httpx.get("http://localhost:8000/api/employees/1/file", params={"type": "id_card"})
print("\nID card (no file):", r.status_code, "(expected 404)")

# Test 3: invalid type
r = httpx.get("http://localhost:8000/api/employees/1/file", params={"type": "invalid"})
print("Invalid type:", r.status_code, "(expected 400)")

# Test 4: bad employee
r = httpx.get("http://localhost:8000/api/employees/99999/file", params={"type": "diploma"})
print("Bad employee:", r.status_code, "(expected 404)")

print("\nAll tests complete!")
