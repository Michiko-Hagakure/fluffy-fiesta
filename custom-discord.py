#!/usr/bin/env python3
import sys
import json
import requests

# Read arguments from the command line
# Wazuh passes: sys.argv[1] = alert file path, sys.argv[3] = hook URL
alert_file_path = sys.argv[1]
hook_url = sys.argv[3] if len(sys.argv) > 3 else sys.argv[2]

# Load JSON data from the alert file safely
# Read the last line to prevent JSONDecodeError caused by Wazuh's NDJSON format
try:
    with open(alert_file_path, 'r') as f:
        lines = f.readlines()
        last_line = lines[-1].strip() if lines else "{}"
        alert_json = json.loads(last_line)
except Exception as e:
    sys.exit(1)

# Get details from the alert JSON with safe fallbacks
alert_level = alert_json.get('rule', {}).get('level', 0)
rule_desc = alert_json.get('rule', {}).get('description', 'No description')
agent_name = alert_json.get('agent', {}).get('name', 'Unknown Agent')
rule_id = alert_json.get('rule', {}).get('id', 'N/A')

# Format message to send to Discord
discord_msg = {
    "content": f"🚨 **WAZUH ALERT DETECTED** 🚨\n"
               f"**Agent/Host:** {agent_name}\n"
               f"**Rule ID:** {rule_id} (Level {alert_level})\n"
               f"**Description:** {rule_desc}"
}

# Post the message to the Discord webhook
try:
    requests.post(hook_url, json=discord_msg, timeout=10)
except Exception as e:
    sys.exit(1)