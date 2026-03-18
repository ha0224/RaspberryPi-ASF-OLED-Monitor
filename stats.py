#!/usr/bin/env python3

from luma.core.interface.serial import i2c
from luma.oled.device import sh1106
from luma.core.render import canvas
from PIL import ImageFont

import psutil
import time
import subprocess
import re
import requests  # Required for IPC API communication


# OLED setup
serial = i2c(port=1, address=0x3C)
device = sh1106(serial)

# Brightness (to protect OLED lifespan)
device.contrast(120)

font = ImageFont.load_default()

# Server List
servers = {
    "Server-1": "YOUR SERVER IP_1",
    "Server-2": "YOUR SERVER IP_2",
    "Server-3": "YOUR SERVER IP_3"
}

offset = 0


# SSH Settings (Used for service status checks)
SSH_TARGET = "YOUR PI NAME@YOUR PI IP"
SSH_PORT = "YOUR PORT NUMBER"
SSH_OPTS = [
    "ssh",
    "-p", SSH_PORT,
    "-o", "BatchMode=yes",
    "-o", "ConnectTimeout=2",
    SSH_TARGET
]

# ASF IPC Settings
# Default port is 1242. You can change it in IPC.config if needed.
ASF_IPC_URL = "http://YOUR_SERVER_IP:PORT/Api/Bot/ASF"
ASF_IPC_PASSWORD = "YOUR_IPC_PASSWORD"

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


# Server-1 ASF status + ASF uptime via SSH
def get_asf_info():
    try:
        status_result = subprocess.run(
            SSH_OPTS + ["systemctl", "is-active", "asf"],
            capture_output=True,
            text=True,
            timeout=3
        )

        state = status_result.stdout.strip()

        if state == "active":
            pid_result = subprocess.run(
                SSH_OPTS + ["systemctl", "show", "asf", "--property=MainPID", "--value"],
                capture_output=True,
                text=True,
                timeout=3
            )

            pid = pid_result.stdout.strip()

            if pid and pid != "0":
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


# Check remaining ASF farming status via IPC API
def get_asf_farm_status():
    headers = {"Authentication": ASF_IPC_PASSWORD} if ASF_IPC_PASSWORD else {}

    try:
        response = requests.get(ASF_IPC_URL, headers=headers, timeout=3)
        if response.status_code != 200:
            return "N/A", "N/A", "N/A", "API ERR"
        
        data = response.json()
        bots = data.get("Result", {})

        if not bots:
            return "0", "0", "0h", "NO BOT"

        bot_name = list(bots.keys())[0]
        bot_data = bots[bot_name]
        
        cards_farmer = bot_data.get("CardsFarmer", {})
        farming_list = cards_farmer.get("GamesToFarm", [])
        
        if not farming_list:
            return "0", "0", "0h", "DONE"

        games_left = len(farming_list)
        cards_left = sum(game.get("CardsRemaining", 0) for game in farming_list)
        
        # --- Parse TimeRemaining (Handles d.hh:mm:ss.mmmm) ---
        time_str = cards_farmer.get("TimeRemaining", "00:00:00")
        time_left = "N/A"
        
        if time_str:
            # Split by '.' to handle both day-separators and milliseconds
            main_parts = time_str.split('.')
            
            # Case: Multiple dots (e.g., "1.07:44:44.9513" -> 1 day, 7 hours)
            if len(main_parts) == 3:
                days = main_parts[0]
                hms = main_parts[1].split(':')
                time_left = f"{days}d {hms[0]}h"
            
            # Case: Single dot (e.g., "1.07:44:44" or "07:44:44.9513")
            elif len(main_parts) == 2:
                # If ':' is in the first part, it's "hh:mm:ss.mmmm"
                if ":" in main_parts[0]: 
                    hms = main_parts[0].split(':')
                    time_left = f"{hms[0]}h {hms[1]}m"
                # Otherwise, it's "d.hh:mm:ss"
                else: 
                    days = main_parts[0]
                    hms = main_parts[1].split(':')
                    time_left = f"{days}d {hms[0]}h"
            
            # Case: No dots (e.g., "07:44:44")
            else:
                hms = main_parts[0].split(':')
                time_left = f"{hms[0]}h {hms[1]}m"

        return str(games_left), str(cards_left), time_left, "ONLINE"

    except:
        return "N/A", "N/A", "N/A", "CONN ERR"

while True:

    # Screen shift for OLED protection
    offset = 1 - offset

    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()

    ip = get_ip()
    temp = get_temp()
    disk = get_disk()
    up = get_uptime()

    mem_used = ram.used // (1024**2)
    mem_total = ram.total // (1024**2)

    # Screen 1: System Information
    with canvas(device) as draw:
        draw.text((0 + offset, 0), f"CPU:{cpu:.0f}%, TEMP:{temp:.0f}C", font=font, fill="white")
        draw.text((0 + offset, 16), f"MEM:{ram.percent:.0f}% [{mem_used}/{mem_total}]", font=font, fill="white")
        draw.text((0 + offset, 32), f"DSK:{disk}, UPT:{up}", font=font, fill="white")
        draw.text((0 + offset, 48), f"IP:{ip}", font=font, fill="white")
    time.sleep(5)

    # Screen 2: STEAM BOT Service Status
    asf_status, asf_uptime = get_asf_info()

    if asf_status == "OFFLINE":
        # Blink effect for offline status
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

    # Screen 3: Farming Progress (IPC Based)
    asf_status, _ = get_asf_info()

    with canvas(device) as draw:
        draw.text((0 + offset, 0), "STEAM BOT", font=font, fill="white")

        if asf_status == "ONLINE":
            games_left, total_cards, time_left, bot_state = get_asf_farm_status()

            if bot_state == "ONLINE":
                draw.text((0 + offset, 16), f"TIME LEFT: {time_left}", font=font, fill="white")
                draw.text((0 + offset, 32), f"GAMES: {games_left}", font=font, fill="white")
                draw.text((0 + offset, 48), f"CARDS: {total_cards}", font=font, fill="white")
            elif bot_state == "DONE":
                draw.text((0 + offset, 16), "TIME LEFT: 0h", font=font, fill="white")
                draw.text((0 + offset, 32), "ALL DONE!", font=font, fill="white")
            else:
                draw.text((0 + offset, 16), f"IPC: {bot_state}", font=font, fill="white")

        elif asf_status == "OFFLINE":
            draw.text((0 + offset, 32), "BOT OFFLINE", font=font, fill="white")

        else:
            draw.text((0 + offset, 32), "SSH/CHK ERR", font=font, fill="white")

    time.sleep(5)

    # Screen 4: Multi-Server Ping Status
    servers_status = get_servers()

    for blink in range(5):
        with canvas(device) as draw:
            y = 0

            # Sort and display each server's ping or status
            for name in sorted(servers_status):
                s = servers_status[name]

                if s == "OFF" and blink % 2 == 0:
                    text = f"{name}: OFF <<<"
                else:
                    text = f"{name}: {s}"

                draw.text((0 + offset, y), text, font=font, fill="white")
                y += 16

        time.sleep(1)