#!/usr/bin/env python3
import argparse
import json
import sys

import requests


def parse_args():
    parser = argparse.ArgumentParser(description="Send a Wazuh alert to a Discord webhook.")
    parser.add_argument("alert_file", nargs="?", help="Path to the alert JSON file")
    parser.add_argument("hook_url", nargs="?", help="Discord webhook URL")
    parser.add_argument("--alert-file", dest="alert_file_flag", help="Path to the alert JSON file")
    parser.add_argument("--hook-url", dest="hook_url_flag", help="Discord webhook URL")
    return parser.parse_args()


def load_alert(alert_file_path):
    try:
        with open(alert_file_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
        if not lines:
            return {}
        return json.loads(lines[-1])
    except (OSError, ValueError, json.JSONDecodeError):
        raise ValueError(f"Unable to read/parse alert file: {alert_file_path}")


def main():
    args = parse_args()
    alert_file_path = args.alert_file_flag or args.alert_file
    hook_url = args.hook_url_flag or args.hook_url

    if not alert_file_path or not hook_url:
        print("Usage: custom-discord.py <alert_file> <hook_url>", file=sys.stderr)
        sys.exit(2)

    try:
        alert_json = load_alert(alert_file_path)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

    alert_level = alert_json.get("rule", {}).get("level", 0)
    rule_desc = alert_json.get("rule", {}).get("description", "No description")
    agent_name = alert_json.get("agent", {}).get("name", "Unknown Agent")
    rule_id = alert_json.get("rule", {}).get("id", "N/A")

    discord_msg = {
        "content": (
            "🚨 **WAZUH ALERT DETECTED** 🚨\n"
            f"**Agent/Host:** {agent_name}\n"
            f"**Rule ID:** {rule_id} (Level {alert_level})\n"
            f"**Description:** {rule_desc}"
        )
    }

    try:
        response = requests.post(hook_url, json=discord_msg, timeout=10)
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"Failed to send Discord alert: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()