#!/usr/bin/env python3
import os
import sys
import subprocess
import datetime
import requests
from dotenv import load_dotenv

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPTS_DIR)
LOG_FILE = os.path.join(PROJECT_DIR, "launch_instance.log")
SUCCESS_FILE = os.path.join(PROJECT_DIR, "INSTANCE_CREATED")
ENV_FILE = os.path.join(PROJECT_DIR, "oci.env")

# Load environment variables
if os.path.exists(ENV_FILE):
    load_dotenv(ENV_FILE)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
TELEGRAM_USER_ID = os.getenv("TELEGRAM_USER_ID", "").strip()

def get_process_status():
    try:
        res = subprocess.run(["pgrep", "-f", "python3 main.py"], capture_output=True, text=True)
        return "🟢 Running (Active)" if res.returncode == 0 else "🔴 Stopped"
    except Exception:
        return "Unknown"

def get_sys_info():
    try:
        load = os.getloadavg()
        return f"{load[0]:.2f}, {load[1]:.2f}"
    except Exception:
        return "N/A"

def parse_log():
    if not os.path.exists(LOG_FILE):
        return 0, "No log file found", "N/A"
    
    with open(LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    
    attempts = sum(1 for line in lines if "Command: launch_instance" in line)
    
    last_msg = "No output recorded yet"
    last_time = "N/A"
    for line in reversed(lines):
        if "Output: " in line:
            last_msg = line.strip().replace("Output: ", "")
            break
            
    for line in reversed(lines):
        if " - INFO - Command: launch_instance" in line:
            parts = line.split(" - INFO - ")
            if parts:
                last_time = parts[0].strip()
            break

    return attempts, last_msg, last_time

def main():
    if not TELEGRAM_TOKEN or not TELEGRAM_USER_ID:
        print("Missing TELEGRAM_TOKEN or TELEGRAM_USER_ID in oci.env or environment.")
        return

    is_created = os.path.exists(SUCCESS_FILE)
    attempts, last_msg, last_time = parse_log()
    proc_status = get_process_status()
    load_avg = get_sys_info()
    now_utc = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    if is_created:
        with open(SUCCESS_FILE, "r") as f:
            details = f.read()
        text = (
            "🎉 *ARM INSTANCE CREATED!*\n\n"
            f"Details:\n```\n{details}\n```\n"
            "Check OCI Console to access your new instance!"
        )
    else:
        text = (
            "📊 *OCI Instance Creation — Status Report*\n\n"
            f"• *Process Status:* {proc_status}\n"
            f"• *Total Attempts:* `{attempts}`\n"
            f"• *Last Attempt Time:* `{last_time}`\n"
            f"• *Last Result:* `{last_msg[:80]}`\n"
            f"• *Load Average:* `{load_avg}`\n"
            "• *Loop Interval:* Retrying every 90 seconds\n\n"
            f"🕒 Report generated at `{now_utc}`"
        )

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_USER_ID,
        "text": text,
        "parse_mode": "Markdown"
    }

    try:
        resp = requests.post(url, json=payload, timeout=15)
        print(f"Notification sent: {resp.status_code}")
    except Exception as e:
        print(f"Error sending notification: {e}")

if __name__ == "__main__":
    main()
