"""Repair common LLM JSON formatting errors to reduce retry API calls."""
import json
import re


def repair_json(text: str) -> str:
    """Fix common JSON formatting mistakes from LLM output, then return cleaned text."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    # Find the outermost {} or [] bounds — discard text outside
    text = _extract_json_envelope(text)

    # Remove trailing commas before } or ]
    text = re.sub(r",(\s*[}\]])", r"\1", text)

    # Replace all single quotes with double quotes for JSON compatibility.
    # Safe for Chinese LLM output (apostrophes are extremely rare in Chinese text).
    text = text.replace("'", '"')

    # Fix unescaped newlines inside string values (LLM sometimes puts literal newlines)
    # This is tricky — we do it by scanning for unbalanced quotes, but skip for now

    return text


def _extract_json_envelope(text: str) -> str:
    """Extract the first complete JSON object or array from text, ignoring surrounding content."""
    # Try to find { ... } or [ ... ] balanced pair
    for start_char, end_char in [("{", "}"), ("[", "]")]:
        start = text.find(start_char)
        if start == -1:
            continue
        depth = 0
        in_string = False
        escape = False
        for i in range(start, len(text)):
            c = text[i]
            if escape:
                escape = False
                continue
            if c == "\\":
                escape = True
                continue
            if c == '"' and not escape:
                in_string = not in_string
                continue
            if in_string:
                continue
            if c == start_char:
                depth += 1
            elif c == end_char:
                depth -= 1
                if depth == 0:
                    return text[start:i + 1]
    return text


def parse_json(text: str) -> dict:
    """Parse JSON with repair attempts. Returns parsed dict or raises ValueError."""
    cleaned = repair_json(text)

    errors = []
    for attempt in range(3):
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            errors.append(str(e))
            if attempt == 0:
                # Try stripping all whitespace and re-cleaning
                cleaned = repair_json(text)
            elif attempt == 1:
                # Last resort: try to fix unbalanced braces
                cleaned = _balance_braces(cleaned)

    raise ValueError(f"JSON repair failed after 3 attempts: {'; '.join(errors)}\nText: {text[:300]}")


def _balance_braces(text: str) -> str:
    """Append missing closing braces/brackets."""
    opens = text.count("{") + text.count("[")
    closes = text.count("}") + text.count("]")
    if opens > closes:
        # Try to infer what's missing by looking at the last open bracket
        stack = []
        for c in text:
            if c in "{[":
                stack.append(c)
            elif c in "}]":
                if stack and ((c == "}" and stack[-1] == "{") or (c == "]" and stack[-1] == "[")):
                    stack.pop()
        for c in reversed(stack):
            text += "}" if c == "{" else "]"
    return text
