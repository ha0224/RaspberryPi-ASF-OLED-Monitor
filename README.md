![GitHub release](https://img.shields.io/github/v/release/ha0224/Raspberry-Pi-ASF-OLED-Monitor)

![Raspberry Pi ASF Rack](rack.jpg)

Example Raspberry Pi rack setup with an SH1106 OLED display monitoring ArchiSteamFarm servers.

## Demo (v1.0)

![OLED Demo](demo.gif)

*(The video above is sped up for demonstration purposes.)*

Note:  
In **v1.0**, the **CARD** value represented the **total remaining cards across all games**.  
Starting from **v1.1**, **CARD** shows the **remaining cards for the currently farming game**.

---

# Raspberry Pi OLED Monitor for ArchiSteamFarm

A **Raspberry Pi OLED monitor** for displaying **ArchiSteamFarm (ASF)** server status and system information.

This project uses a **128x64 SH1106 OLED display** connected to a Raspberry Pi to show real-time system statistics and ASF farming status from another Raspberry Pi over SSH.

It allows you to monitor your ASF servers without opening SSH or a web dashboard.

---

# Features

## System Monitoring

Displays Raspberry Pi system information:

- CPU usage
- RAM usage
- Disk usage
- CPU temperature
- System uptime
- Local IP address

---

## ArchiSteamFarm Monitoring

Displays ASF status from another Raspberry Pi via SSH:

- ASF service status (ONLINE / OFFLINE)
- ASF process uptime
- Remaining farming games
- Remaining cards for the currently farming game
- Detects when the Steam account is currently in use

---

## Multi-Server Monitoring

Displays network status for multiple Raspberry Pi servers.

Example output:

```
Server-0: Local
Server-1: 1.2ms
Server-2: 0.8ms
Server-3: OFF
```

---

# Example Setup

Typical setup used for this project:

```
Server-0 : Raspberry Pi with OLED display (monitor node)
Server-1 : Raspberry Pi running ArchiSteamFarm
Server-2 : Optional Raspberry Pi node
Server-3 : Optional Raspberry Pi node
```

Server-0 connects to Server-1 via **SSH** to monitor the ASF service status and farming progress.

---

# Network Architecture

```
┌───────────────┐
│   Server-0    │
│ Raspberry Pi  │
│ OLED Monitor  │
└───────┬───────┘
        │ SSH
        ▼
┌───────────────┐
│   Server-1    │
│ ASF Server    │
└───────────────┘
```

The OLED monitor runs on **Server-0** and retrieves ASF status from **Server-1** using SSH commands.

---

# Hardware

Tested with the following hardware:

- Raspberry Pi 4B
- Raspberry Pi 3
- SH1106 OLED display (128x64 I2C)

Example server layout:

```
Server-0 : Raspberry Pi with OLED display (monitor node)
Server-1 : Raspberry Pi running ArchiSteamFarm
Server-2 : Optional node
Server-3 : Optional node
```

---

## OLED Display

This project was tested with the following OLED module:

**1.3" SH1106 OLED Display (128x64 I2C)**

Purchase link:
https://aliexpress.com/item/4001145494936.html

(Option used: 4pinIIC-White)

---

# Installation

Install required Python libraries:

```bash
pip3 install luma.oled psutil Pillow
```

Run the monitor:

```bash
python3 stats.py
```

---

# Configuration

Edit the following values inside **stats.py**.

Server list:

```
servers = {
    "Server-1": "YOUR SERVER IP_1",
    "Server-2": "YOUR SERVER IP_2",
    "Server-3": "YOUR SERVER IP_3"
}
```

SSH connection settings:

```
SSH_TARGET = "YOUR PI NAME@YOUR PI IP"
SSH_PORT = "YOUR PORT NUMBER"
```

Passwordless SSH login (SSH keys) is recommended.

---

# ASF Log Language

The log parsing logic in this script is based on **Korean ASF logs**.

If your ASF logs are in another language, you may need to modify the parsing logic inside:

```
get_asf_farm_status()
```

---

# Rack Case

The Raspberry Pi rack mount case used in this setup was designed by another creator.

You can find the 3D model here:

https://www.printables.com/model/211251-19-raspberry-pi-34-rackmount-with-13-oled-screen-p  
https://www.printables.com/model/352578-triple-raspberrypi-rack-mount

---

# License

MIT License
