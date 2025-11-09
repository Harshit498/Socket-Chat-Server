#!/usr/bin/env python3
"""
Simple interactive client for the Simple Socket Chat Server.
Usage:
  python client.py --host localhost --port 4000
Type commands directly, e.g.:
  LOGIN Akash
  MSG Hello
  WHO
  DM Bob Hi
  PING
Press Ctrl+C to quit.
"""
import socket
import threading
import argparse
import sys

def recv_loop(sock):
    try:
        while True:
            data = sock.recv(4096)
            if not data:
                print("[*] Server closed connection.")
                return
            # print server lines as-is
            sys.stdout.write(data.decode('utf-8'))
            if not data.decode('utf-8').endswith("\n"):
                sys.stdout.write("\n")
            sys.stdout.flush()
    except Exception:
        print("[*] Disconnected.")
    finally:
        try:
            sock.close()
        except Exception:
            pass

def main(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    print(f"[+] Connected to {host}:{port}")
    t = threading.Thread(target=recv_loop, args=(sock,), daemon=True)
    t.start()

    try:
        while True:
            line = input()
            if not line:
                continue
            if not line.endswith("\n"):
                line = line + "\n"
            sock.sendall(line.encode('utf-8'))
    except (KeyboardInterrupt, EOFError):
        print("\n[*] Quitting.")
    finally:
        try:
            sock.close()
        except Exception:
            pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=4000)
    args = parser.parse_args()
    main(args.host, args.port)
