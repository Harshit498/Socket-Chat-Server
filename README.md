# 🗨️ Simple Socket Chat Server

## 📘 Project Overview
This project implements a **real-time multi-user chat system** using **TCP sockets** in Python — **without any external libraries or frameworks**.  
It supports multiple clients connecting to one server, sending and receiving live chat messages, private DMs, and real-time user notifications.
----
LINK - https://www.loom.com/share/daa14ee7b8714766b606542bc50c66d3
----

## ⚙️ Features
✅ Multi-user chat over TCP  
✅ Unique username login system  
✅ Broadcast messages (`MSG`)  
✅ Private messages (`DM`)  
✅ Online users list (`WHO`)  
✅ Heartbeat check (`PING` → `PONG`)  
✅ Automatic disconnection notice  
✅ Idle timeout (60 s inactivity auto-disconnect)

---

socket-chat-server/

├── server.py        # TCP chat server
├── client.py        # interactive client
├── run.sh           # optional helper script
└── README.md        # this documentation

---

## 🧠 How It Works
- The **server** listens on port 4000 (default).  
- Each **client** connects via socket, logs in with a unique username, and exchanges messages.  
- Messages are broadcast to all connected users instantly.  
- Disconnects are handled automatically, notifying everyone.

---

## 🖥️ Requirements
- Python 3.8 or higher  
- Works on **Windows**, **macOS**, or **Linux**  
- No extra installations needed (uses only the Python standard library)

---

## 🚀 Step-by-Step Setup (VS Code)

### **Step 1 — Open the folder**
1. Open **VS Code** → **File → Open Folder …**  
2. Select your project folder:
3. Ensure you see these files in the Explorer:

---

### **Step 2 — Open three terminals**
Open three terminals inside VS Code:

| Terminal | Purpose | Command |
|-----------|----------|----------|
| 1️⃣ | Start the server | `python server.py` |
| 2️⃣ | Client 1 (Harshit) | `python client.py` |
| 3️⃣ | Client 2 (Neha) | `python client.py` |

---

### **Step 3 — Run the server**
In **Terminal 1**:
```bash
python server.py
[+] Chat server listening on 0.0.0.0:4000

**Step 4 — Connect two clients**

**In Terminal 2:
**
python client.py


**Then type:**

LOGIN Harshit
OK
MSG Hello everyone!


**In Terminal 3:**

python client.py


**Then type:**

LOGIN Neha
OK
MSG Hi Harshit!


✅ Client 1 sees:

MSG Neha Hi Harshit!


✅ Client 2 sees:

MSG Akash Hello everyone!

**Step 5 — Test optional features**

Try these commands in any client:

WHO
DM Neha this is private
PING


If a user closes their client window, others see:

INFO <username> disconnected

**Step 6 — Stop the server**

Press Ctrl + C in the server terminal.
