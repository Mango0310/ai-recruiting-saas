"""Webhook notification service for Feishu/WeCom/custom webhooks.

Configuration via .env:
  WEBHOOK_URL — webhook endpoint URL (empty = disabled)
  WEBHOOK_TYPE — "feishu" | "wecom" | "custom" (default: "feishu")
"""

import os
from datetime import datetime
from typing import Optional

import httpx

WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
WEBHOOK_TYPE = os.getenv("WEBHOOK_TYPE", "feishu")


def is_enabled() -> bool:
    return bool(WEBHOOK_URL.strip())


def _build_feishu_payload(title: str, content: str, level: str = "info") -> dict:
    """Build a Feishu card message."""
    color_map = {"urgent": "red", "warning": "orange", "info": "blue"}
    color = color_map.get(level, "blue")

    return {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"content": title, "tag": "plain_text"},
                "template": color,
            },
            "elements": [
                {"tag": "markdown", "content": content},
                {
                    "tag": "note",
                    "elements": [
                        {"tag": "plain_text", "content": f"AI招聘系统 · {datetime.now().strftime('%Y-%m-%d %H:%M')}"}
                    ],
                },
            ],
        },
    }


def _build_wecom_payload(title: str, content: str, level: str = "info") -> dict:
    """Build a WeCom markdown message."""
    level_emoji = {"urgent": "🔴", "warning": "🟡", "info": "🔵"}
    emoji = level_emoji.get(level, "🔵")
    markdown = f"## {emoji} {title}\n\n{content}\n\n> AI招聘系统 · {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    return {"msgtype": "markdown", "markdown": {"content": markdown}}


def _build_custom_payload(title: str, content: str, level: str = "info") -> dict:
    """Build a generic JSON payload."""
    return {
        "title": title,
        "content": content,
        "level": level,
        "source": "ai-recruiting-saas",
        "timestamp": datetime.now().isoformat(),
    }


def _build_payload(title: str, content: str, level: str = "info") -> dict:
    if WEBHOOK_TYPE == "wecom":
        return _build_wecom_payload(title, content, level)
    elif WEBHOOK_TYPE == "custom":
        return _build_custom_payload(title, content, level)
    else:  # feishu
        return _build_feishu_payload(title, content, level)


def send(title: str, content: str, level: str = "info") -> bool:
    """Send a notification via webhook. Returns True on success, False on failure. Never raises."""
    if not is_enabled():
        return False

    payload = _build_payload(title, content, level)
    try:
        r = httpx.post(WEBHOOK_URL, json=payload, timeout=15)
        return r.status_code in (200, 201, 204)
    except Exception:
        return False


# ── Pre-built notification templates ──

def notify_probation_alert(employees: list) -> bool:
    """Notify about employees with probation alerts."""
    if not employees:
        return True

    urgent = [e for e in employees if e.probation_alert == "overdue"]
    warning_7d = [e for e in employees if e.probation_alert == "urgent"]
    warning_14d = [e for e in employees if e.probation_alert == "upcoming"]

    lines = []

    if urgent:
        lines.append(f"**逾期未转正 ({len(urgent)}人)**：")
        for e in urgent:
            lines.append(f"- {e.name}（{e.position}）· 试用期已于 {e.probation_end_date} 到期，请尽快处理转正")
        lines.append("")

    if warning_7d:
        lines.append(f"**7天内到期 ({len(warning_7d)}人)**：")
        for e in warning_7d:
            days = e.days_until_probation_end
            lines.append(f"- {e.name}（{e.position}）· 还剩 {days} 天，需在7天内完成转正评估")
        lines.append("")

    if warning_14d:
        lines.append(f"**14天内到期 ({len(warning_14d)}人)**：")
        for e in warning_14d:
            days = e.days_until_probation_end
            lines.append(f"- {e.name}（{e.position}）· 还剩 {days} 天")

    level = "urgent" if urgent else ("warning" if warning_7d else "info")
    title = f"转正预警 · {datetime.now().strftime('%m月%d日')}"
    return send(title, "\n".join(lines), level)


def notify_new_employee(employee_name: str, position: str, department: str, onboard_link: str = "") -> bool:
    """Notify when a new employee is onboarded."""
    lines = [
        f"**姓名**: {employee_name}",
        f"**岗位**: {position}",
        f"**部门**: {department or '—'}",
    ]
    if onboard_link:
        lines.append("")
        lines.append(f"[入职登记链接]({onboard_link})（发给员工填写个人信息）")

    return send("新员工入职", "\n".join(lines), "info")


def notify_new_candidate(candidate_name: str, job_title: str, conclusion: str) -> bool:
    """Notify when a new candidate is uploaded and analyzed."""
    lines = [
        f"**候选人**: {candidate_name}",
        f"**投递岗位**: {job_title}",
        f"**AI分析结论**: {conclusion}",
    ]
    return send("新候选人入库", "\n".join(lines), "info")
