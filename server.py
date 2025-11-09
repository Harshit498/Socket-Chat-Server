#!/usr/bin/env python3
"""
Simple Socket Chat Server
- Listens on port 4000 by default (configurable).
- Uses only Python standard library.
- Supports LOGIN, MSG, WHO, DM, PING, and idle timeout (60s).
Protocol examples:
  LOGIN Alice
  OK
  MSG Hello everyone
  -> broadcast: MSG Alice Hello everyone
  WHO
  -> USER <username> (per user)
  DM Bob Hey, privately
  -> DM <from> <text> (delivered only to Bob)
  PING
  -> PONG
When a user disconnects:
  INFO <username> disconnected
"""
import socket
import threading
import argparse
import os
import time
import traceback

# Configuration
DEFAULT_PORT = 4000
IDLE_TIMEOUT = 60  # seconds

# Global client structures
clients_lock = threading.Lock()
# username -> {"conn": socket, "addr": (host,port), "last_active": float}
clients = {}
# conn.fileno() -> username (for quick lookup)
conn_to_username = {}

# Helper functions
def now():
    return time.time()

def send_line(conn, line):
    try:
        if not line.endswith("\n"):
            line = line + "\n"
        conn.sendall(line.encode('utf-8'))
    except Exception:
        # ignore errors while sending (client may have disconnected)
        pass

def broadcast_line(line, exclude_username=None):
    """Send line to all connected users except exclude_username (if provided)."""
    with clients_lock:
        for uname, meta in list(clients.items()):
            if uname == exclude_username:
                continue
            send_line(meta["conn"], line)

def handle_login(raw, conn, addr):
    """
    Attempt to parse and perform login.
    Returns (username, error_message) where username or error_message is set.
    """
    raw = raw.strip()
    parts = raw.split()
    if len(parts) >= 2 and parts[0].upper() == "LOGIN":
        username = " ".join(parts[1:]).strip()
        if not username:
            return (None, "ERR invalid-username")
        # ensure username not taken
        with clients_lock:
            if username in clients:
                return (None, "ERR username-taken")
            # reserve socket temporarily by assigning
            clients[username] = {"conn": conn, "addr": addr, "last_active": now()}
            conn_to_username[conn.fileno()] = username
        return (username, None)
    else:
        return (None, "ERR expected-login")

def cleanup_connection(conn):
    """Close socket and remove mappings. Broadcast disconnect if a logged-in user."""
    try:
        fileno = conn.fileno()
    except Exception:
        fileno = None

    username = None
    with clients_lock:
        if fileno in conn_to_username:
            username = conn_to_username.pop(fileno)
        if username and username in clients:
            # remove client
            try:
                clients.pop(username)
            except KeyError:
                pass

    try:
        conn.close()
    except Exception:
        pass

    if username:
        broadcast_line(f"INFO {username} disconnected")

def parse_command(line):
    """Return (cmd, rest) where cmd is uppercased first word, rest is remainder (stripped)."""
    line = line.strip()
    if not line:
        return (None, "")
    parts = line.split(maxsplit=1)
    cmd = parts[0].upper()
    rest = parts[1] if len(parts) > 1 else ""
    return (cmd, rest.strip())

def client_thread(conn, addr):
    """
    Handle a single client connection.
    Enforces that first successful command is LOGIN <username>.
    Then accepts MSG, WHO, DM, PING.
    """
    try:
        conn.settimeout(None)
        buffer = ""
        logged_in = False
        username = None
        fileno = conn.fileno()

        # First read must be LOGIN
        # We'll loop receiving until client logs in or disconnects
        while True:
            data = conn.recv(4096)
            if not data:
                # disconnected before login
                cleanup_connection(conn)
                return
            buffer += data.decode('utf-8', errors='ignore')
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if not line:
                    continue
                u, err = handle_login(line, conn, addr)
                if err:
                    send_line(conn, err)
                    # if an ERR username-taken, close connection
                    if err.startswith("ERR username-taken"):
                        cleanup_connection(conn)
                        return
                    # otherwise keep waiting for LOGIN
                else:
                    username = u
                    logged_in = True
                    send_line(conn, "OK")
                    # broadcast nothing for initial login (spec doesn't require INFO)
                    with clients_lock:
                        # update last_active
                        clients[username]["last_active"] = now()
                    break
            if logged_in:
                break

        # After login, enter message loop
        while True:
            data = conn.recv(4096)
            if not data:
                # client disconnected
                cleanup_connection(conn)
                return
            buffer += data.decode('utf-8', errors='ignore')
            # Process all full lines
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if not line:
                    continue
                cmd, rest = parse_command(line)
                # update last active
                with clients_lock:
                    if username in clients:
                        clients[username]["last_active"] = now()

                if cmd == "MSG":
                    # rest is text
                    text = " ".join(rest.split())  # normalize spaces
                    broadcast_line(f"MSG {username} {text}")
                elif cmd == "WHO":
                    # respond with USER <username> per line to the requester only
                    with clients_lock:
                        for uname in clients.keys():
                            send_line(conn, f"USER {uname}")
                elif cmd == "DM":
                    # DM <username> <text>
                    parts = rest.split(maxsplit=1)
                    if len(parts) < 2:
                        send_line(conn, "ERR invalid-dm-format")
                    else:
                        target, text = parts[0], parts[1]
                        with clients_lock:
                            if target in clients:
                                send_line(clients[target]["conn"], f"DM {username} {text}")
                            else:
                                send_line(conn, "ERR user-not-found")
                elif cmd == "PING":
                    send_line(conn, "PONG")
                else:
                    send_line(conn, "ERR unknown-command")
    except ConnectionResetError:
        cleanup_connection(conn)
    except Exception:
        # show traceback on server console, then cleanup
        traceback.print_exc()
        cleanup_connection(conn)

def idle_reaper_thread():
    """Disconnect clients that have been idle for > IDLE_TIMEOUT seconds."""
    while True:
        time.sleep(5)
        nowt = now()
        to_disconnect = []
        with clients_lock:
            for uname, meta in list(clients.items()):
                if nowt - meta["last_active"] > IDLE_TIMEOUT:
                    to_disconnect.append(uname)
        for uname in to_disconnect:
            with clients_lock:
                meta = clients.get(uname)
                if not meta:
                    continue
                conn = meta["conn"]
                # send a message then close
                try:
                    send_line(conn, "INFO disconnected-due-to-inactivity")
                except Exception:
                    pass
                try:
                    fileno = conn.fileno()
                except Exception:
                    fileno = None
                # remove mappings
                if fileno in conn_to_username:
                    conn_to_username.pop(fileno, None)
                clients.pop(uname, None)
                try:
                    conn.close()
                except Exception:
                    pass
            broadcast_line(f"INFO {uname} disconnected")

def start_server(host, port):
    # Start idle reaper thread
    reaper = threading.Thread(target=idle_reaper_thread, daemon=True)
    reaper.start()

    # Create server socket
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((host, port))
    srv.listen(50)
    print(f"[+] Chat server listening on {host}:{port}")
    try:
        while True:
            conn, addr = srv.accept()
            print(f"[+] New connection from {addr}")
            t = threading.Thread(target=client_thread, args=(conn, addr), daemon=True)
            t.start()
    except KeyboardInterrupt:
        print("[*] Shutting down server.")
    finally:
        try:
            srv.close()
        except Exception:
            pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simple Socket Chat Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to (default 0.0.0.0)")
    parser.add_argument("--port", type=int, default=int(os.environ.get("CHAT_PORT", DEFAULT_PORT)),
                        help=f"Port to bind to (default env CHAT_PORT or {DEFAULT_PORT})")
    args = parser.parse_args()
    start_server(args.host, args.port)
