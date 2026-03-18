![GitHub release](https://img.shields.io/github/v/release/ha0224/Raspberry-Pi-ASF-OLED-Monitor)
![Python](https://img.shields.io/badge/python-3.x-blue)
![License](https://img.shields.io/github/license/ha0224/Raspberry-Pi-ASF-OLED-Monitor)

![Raspberry Pi ASF Rack](rack.jpg)

Example Raspberry Pi rack setup with an SH1106 OLED display monitoring ArchiSteamFarm servers.

## Demo (v2.0)

![OLED Demo](demo.gif)

*(The video above is sped up for demonstration purposes.)*

---

# Raspberry Pi OLED Monitor for ArchiSteamFarm

Raspberry Pi OLED monitor for ArchiSteamFarm servers using SH1106 displays and the ASF IPC API.

Keywords: Raspberry Pi, SH1106 OLED, ArchiSteamFarm, ASF Monitor, Steam Card Farming, OLED Display Monitor

A **Raspberry Pi OLED monitor** for displaying **ArchiSteamFarm (ASF)** server status and system information.

This project uses a **128x64 SH1106 OLED display** connected to a Raspberry Pi to show real-time system statistics and ASF farming status from another Raspberry Pi.

Starting from **v2.0**, farming data is retrieved through the **ASF IPC API** instead of log parsing, providing more accurate farming statistics.

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

Displays ASF status from another Raspberry Pi:

- ASF service status (ONLINE / OFFLINE)
- ASF process uptime
- Remaining farming games
- Total remaining cards across all farming games
- Estimated farming time left
- ASF IPC-based farming data retrieval

---

## Multi-Server Monitoring

Displays network status for multiple Raspberry Pi servers.

Example output:

```
Server-0: Local
Server-1: 1.2ms
Server-2: 0.8ms
Server-3: OFF
````

---

# Example Setup

Typical setup used for this project:

```
Server-0 : Raspberry Pi with OLED display (monitor node)
Server-1 : Raspberry Pi running ArchiSteamFarm
Server-2 : Optional Raspberry Pi node
Server-3 : Optional Raspberry Pi node
```

* **Server-0** displays system information and ASF farming status on the OLED screen.
* **Server-1** runs **ArchiSteamFarm**.
* Server-0 uses **SSH** to check the ASF service status and **ASF IPC API** to retrieve farming progress.

---

# Network Architecture

```
┌────────┐
│      Server-0      │
│   Raspberry Pi    │
│  OLED Monitor  │
└─┬─────┬┘
       │ SSH / IPC
       ▼
┌────────┐
│       Server-1      │
│     ASF Server    │
└────────┘
```

The OLED monitor runs on **Server-0** and retrieves ASF status from **Server-1** using **SSH** and **ASF IPC API**.

---

# Hardware

Tested with the following hardware:

* Raspberry Pi 4B
* Raspberry Pi 3
* SH1106 OLED display (128x64 I2C)

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
[https://aliexpress.com/item/4001145494936.html](https://aliexpress.com/item/4001145494936.html)

(Option used: 4pinIIC-White)

---

# Installation

Install required Python libraries:

```
pip3 install luma.oled psutil Pillow requests
```

Run the monitor:

```
python3 stats.py
```

---

# Requirements

Before using this project, make sure the following requirements are met.

## Hardware

* Two Raspberry Pi devices
* SH1106 128x64 I2C OLED display connected to **Server-0**

Example setup:

```
Server-0 : Raspberry Pi with OLED display (monitor node)
Server-1 : Raspberry Pi running ArchiSteamFarm
```

Server-0 displays system and ASF status on the OLED screen.
Server-1 runs **ArchiSteamFarm** and provides farming information via SSH and IPC.

---

## Network

* Both Raspberry Pi devices must be on the **same local network**
* Server-0 must be able to reach Server-1 via **SSH**
* Server-0 must be able to access the **ASF IPC API** on Server-1

Example:

```
Server-0 → 192.168.0.10
Server-1 → 192.168.0.11
```

---

## Raspberry Pi Configuration

On **Server-0**, enable I2C for the OLED display:

```
sudo raspi-config
```

Navigate to:

```
Interface Options → I2C → Enable
```

Then reboot the Raspberry Pi.

---

## Python Dependencies

Install the required Python libraries on Server-0:

```
pip3 install luma.oled Pillow psutil requests
```

---

## ArchiSteamFarm

Server-1 must have **ArchiSteamFarm installed and running**.

The script checks the ASF service status using:

```
systemctl is-active asf
```

Make sure ASF is running as a **systemd service named `asf`**.

---

## SSH Access

Server-0 must be able to connect to Server-1 using SSH.

Example:

```
ssh -p PORT USER@SERVER_IP
```

Passwordless SSH login using SSH keys is recommended for reliable monitoring.

---

## ASF IPC

Starting from **v2.0**, this project uses the **ASF IPC API** for accurate farming data.

Make sure IPC is enabled in ASF and that an IPC password is configured.

Example IPC settings:

```
{
  "IPC": true,
  "IPCPassword": "your_password_here"
}
```

The default ASF IPC port is usually:

```
1242
```

You can change it in ASF configuration if needed.

---

# OLED Display Information

Example farming screen:

```
STEAM BOT
TIME LEFT: 7h 44m
GAMES: 8
CARDS: 21
```

Meaning:

* **TIME LEFT** = Estimated farming time remaining
* **GAMES** = Remaining games with card drops
* **CARDS** = Total remaining cards across all farming games

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

ASF IPC settings:

```
ASF_IPC_URL = "http://YOUR_SERVER_IP:PORT/Api/Bot/ASF"
ASF_IPC_PASSWORD = "YOUR_IPC_PASSWORD"
```

Notes:

* The default ASF IPC port is usually **1242**
* Replace `YOUR_IPC_PASSWORD` with your actual ASF IPC password
* Passwordless SSH login (SSH keys) is recommended

---

# Rack Case

The Raspberry Pi rack mount case used in this setup was designed by another creator.

You can find the 3D model here:

https://www.printables.com/model/211251-19-raspberry-pi-34-rackmount-with-13-oled-screen-p

https://www.printables.com/model/352578-triple-raspberrypi-rack-mount

---

# Support

If you find this project useful, consider giving it a ⭐ on GitHub.

It motivates further development and improvements.

Thank you for your support!

# License

MIT License
