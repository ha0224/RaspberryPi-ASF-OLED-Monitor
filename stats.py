#!/usr/bin/env python3

from luma.core.interface.serial import i2c
from luma.oled.device import sh1106
from luma.core.render import canvas
from PIL import ImageFont

import psutil
import time
import subprocess
import re


# OLED setup
serial = i2c(port=1, address=0x3C)
device = sh1106(serial)

# Brightness (to protect OLED lifespan)
device.contrast(120)

font = ImageFont.load_default()


# Server list
# If the Raspberry Pi running ASF and the Raspberry Pi with the OLED display
# are on the same local network, you can use their local IP addresses here.
servers = {
    "Server-1": "YOUR SERVER IP_1",
    "Server-2": "YOUR SERVER IP_2",
    "Server-3": "YOUR SERVER IP_3"
}

offset = 0


# SSH configuration
SSH_TARGET = "YOUR PI NAME@YOUR PI IP"
SSH_PORT = "YOUR PORT NUMBER"
SSH_OPTS = [
    "ssh",
    "-p", SSH_PORT,
    "-o", "BatchMode=yes",
    "-o", "ConnectTimeout=2",
    SSH_TARGET
]


# Get local IP address
def get_ip():
    try:
        ip_list = subprocess.check_output("hostname -I", shell=True).decode().split()
        for ip in ip_list:
            if "." in ip:
                return ip
        return "N/A"
    except:
        return "N/A"


# Get CPU temperature
def get_temp():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp") as f:
            return float(f.read()) / 1000
    except:
        return 0


# Server-0 uptime
def get_uptime():
    seconds = int(time.time() - psutil.boot_time())

    days = seconds // 86400
    hours = (seconds % 86400) // 3600

    return f"{days}d{hours}h"


# Disk usage
def get_disk():
    d = psutil.disk_usage('/')

    used = d.used // (1024**3)
    total = d.total // (1024**3)

    return f"{used} / {total}G"


# Ping server
def ping(ip):
    try:
        result = subprocess.check_output(
            ["ping", "-c", "1", "-W", "1", ip],
            stderr=subprocess.DEVNULL
        ).decode()

        for line in result.split("\n"):
            if "time=" in line:
                ms = line.split("time=")[1].split()[0]
                return f"{ms}ms"

        return "ON"

    except:
        return "OFF"


# Get server status
def get_servers():
    status = {}

    status["Server-0"] = "Local"

    for name, ip in servers.items():
        status[name] = ping(ip)

    return status


# Convert ps etime format into shorter format for OLED display
def format_etime(etime):
    etime = etime.strip()

    if not etime:
        return "N/A"

    # Examples:
    # 05:12
    # 01:23:45
    # 2-03:14:59
    if "-" in etime:
        day_part, time_part = etime.split("-", 1)
        days = int(day_part)
        h, m, s = map(int, time_part.split(":"))
        return f"{days}d{h}h"

    parts = etime.split(":")

    if len(parts) == 3:
        h, m, s = map(int, parts)
        return f"{h}h{m}m"

    if len(parts) == 2:
        m, s = map(int, parts)
        return f"{m}m{s}s"

    return etime


# Server-1 ASF status + ASF uptime
def get_asf_info():
    try:
        # Check service status
        status_result = subprocess.run(
            SSH_OPTS + ["systemctl", "is-active", "asf"],
            capture_output=True,
            text=True,
            timeout=3
        )

        state = status_result.stdout.strip()

        if state == "active":
            # Get MainPID
            pid_result = subprocess.run(
                SSH_OPTS + ["systemctl", "show", "asf", "--property=MainPID", "--value"],
                capture_output=True,
                text=True,
                timeout=3
            )

            pid = pid_result.stdout.strip()

            if pid and pid != "0":
                # Get ASF process uptime
                etime_result = subprocess.run(
                    SSH_OPTS + ["ps", "-p", pid, "-o", "etime="],
                    capture_output=True,
                    text=True,
                    timeout=3
                )

                asf_uptime = format_etime(etime_result.stdout.strip())
            else:
                asf_uptime = "N/A"

            return "ONLINE", asf_uptime

        elif state in ("inactive", "failed", "activating", "deactivating"):
            return "OFFLINE", ""

        else:
            return "ERROR", ""

    except subprocess.TimeoutExpired:
        return "ERROR", ""

    except:
        return "ERROR", ""


# Check remaining ASF farming games/current game cards
def get_asf_farm_status():
    try:
        result = subprocess.run(
            SSH_OPTS + ["journalctl", "-u", "asf", "-n", "1000", "--no-pager"],
            capture_output=True,
            text=True,
            timeout=4
        )

        log_text = result.stdout

        if not log_text:
            return "N/A", "N/A"

        lines = log_text.strip().splitlines()

##############################
# NOTE:
# The log parsing below is based on Korean ASF logs.
# If your ASF logs use a different language,
# you may need to modify the patterns accordingly.
##############################

        # 1. Determine CURRENT state from the latest state-related logs
        current_state = None
        current_cards = None

        for line in reversed(lines):
            # Farming in progress (highest priority)
            card_match = re.search(r"농사 상태:\s*(\d+)개의 카드 남음", line)
            if card_match:
                current_state = "FARMING"
                current_cards = card_match.group(1)
                break

            if "FarmCards() 아직 농사 중:" in line or "FarmSolo() 현재 농사 중:" in line:
                current_state = "FARMING"
                break

            # Account in use / waiting
            if "계정이 현재 사용 중입니다" in line or "농사가 현재 불가능 합니다" in line:
                current_state = "WAIT"
                break

            # Nothing left to farm
            if "이 계정에는 농사지을 것이 없습니다" in line or "농사 완료!" in line:
                current_state = "DONE"
                break

        if current_state == "WAIT":
            return "WAIT", "WAIT"

        if current_state == "DONE":
            return "0", "0"

        # 2. Find the latest total games line
        total_games = None
        total_index = None

        for i in range(len(lines) - 1, -1, -1):
            line = lines[i]
            match = re.search(r"총\s+(\d+)개의\s+게임\s+\((\d+)개의\s+카드\)\s+남음", line)
            if match:
                total_games = int(match.group(1))
                total_index = i
                break

        if total_games is None or total_index is None:
            if current_state == "FARMING":
                return "N/A", current_cards if current_cards is not None else "N/A"
            return "N/A", "N/A"

        # 3. Count completed games after the latest total games line
        completed_ids = set()

        for line in lines[total_index + 1:]:
            complete_match = re.search(r"FarmSolo\(\)\s+농사 완료:\s+(\d+)", line)
            if complete_match:
                completed_ids.add(complete_match.group(1))

            card_match = re.search(r"농사 상태:\s*(\d+)개의 카드 남음", line)
            if card_match:
                current_cards = card_match.group(1)

        remaining_games = total_games - len(completed_ids)
        if remaining_games < 0:
            remaining_games = 0

        if current_cards is None:
            current_cards = "N/A"

        return str(remaining_games), str(current_cards)

    except subprocess.TimeoutExpired:
        return "N/A", "N/A"

    except:
        return "N/A", "N/A"


while True:

    offset = 1 - offset

    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()

    ip = get_ip()
    temp = get_temp()
    disk = get_disk()
    up = get_uptime()

    mem_used = ram.used // (1024**2)
    mem_total = ram.total // (1024**2)

    # 1. System information screen
    with canvas(device) as draw:
        draw.text((0 + offset, 0), f"CPU:{cpu:.0f}%, TEMP:{temp:.0f}C", font=font, fill="white")
        draw.text((0 + offset, 16), f"MEM:{ram.percent:.0f}% [{mem_used}/{mem_total}]", font=font, fill="white")
        draw.text((0 + offset, 32), f"DSK:{disk}, UPT:{up}", font=font, fill="white")
        draw.text((0 + offset, 48), f"IP:{ip}", font=font, fill="white")

    time.sleep(5)

    # 2. STEAM BOT status screen
    asf_status, asf_uptime = get_asf_info()

    if asf_status == "OFFLINE":
        for blink in range(5):
            with canvas(device) as draw:
                draw.text((0 + offset, 0), "STEAM BOT", font=font, fill="white")
                draw.text((0 + offset, 16), "SERVER: Server-1", font=font, fill="white")

                if blink % 2 == 0:
                    draw.text((0 + offset, 32), "STATE: OFFLINE <<<", font=font, fill="white")
                else:
                    draw.text((0 + offset, 32), "STATE: OFFLINE", font=font, fill="white")

                draw.text((0 + offset, 48), "ACTION REQUIRED", font=font, fill="white")

            time.sleep(1)

    else:
        with canvas(device) as draw:
            draw.text((0 + offset, 0), "STEAM BOT", font=font, fill="white")
            draw.text((0 + offset, 16), "SERVER: Server-1", font=font, fill="white")
            draw.text((0 + offset, 32), f"STATE: {asf_status}", font=font, fill="white")

            if asf_status == "ONLINE":
                draw.text((0 + offset, 48), f"UPT: {asf_uptime}", font=font, fill="white")
            else:
                draw.text((0 + offset, 48), "SSH/CHK ERR", font=font, fill="white")

        time.sleep(5)

    # 3. GAMES / CARD screen
    asf_status, _ = get_asf_info()

    with canvas(device) as draw:
        draw.text((0 + offset, 0), "STEAM BOT", font=font, fill="white")
        draw.text((0 + offset, 16), "SERVER: Server-1", font=font, fill="white")

        if asf_status == "ONLINE":
            games_left, current_cards = get_asf_farm_status()

            if games_left == "WAIT":
                draw.text((0 + offset, 32), "IN USE / WAIT", font=font, fill="white")
            else:
                draw.text((0 + offset, 32), f"GAMES: {games_left}", font=font, fill="white")
                draw.text((0 + offset, 48), f"CARD: {current_cards}", font=font, fill="white")

        elif asf_status == "OFFLINE":
            draw.text((0 + offset, 32), "BOT OFFLINE", font=font, fill="white")

        else:
            draw.text((0 + offset, 32), "SSH/CHK ERR", font=font, fill="white")

    time.sleep(5)

    # 4. Server status screen
    servers_status = get_servers()

    for blink in range(5):
        with canvas(device) as draw:
            y = 0

            for name in sorted(servers_status):
                s = servers_status[name]

                if s == "OFF" and blink % 2 == 0:
                    text = f"{name}: OFF <<<"
                else:
                    text = f"{name}: {s}"

                draw.text((0 + offset, y), text, font=font, fill="white")
                y += 16

        time.sleep(1)