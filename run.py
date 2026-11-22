"""Satu perintah: jalankan server (otomatis) + client.   python run.py"""
import os
import socket
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
HOST, PORT = "127.0.0.1", 5000


def port_open():
    with socket.socket() as s:
        s.settimeout(0.3)
        return s.connect_ex((HOST, PORT)) == 0


def main():
    server = None
    if not port_open():
        server = subprocess.Popen([sys.executable, "app.py"], cwd=os.path.join(ROOT, "server"))
        for _ in range(50):
            if port_open():
                break
            time.sleep(0.1)
    try:
        subprocess.call([sys.executable, "main.py"], cwd=os.path.join(ROOT, "client"))
    finally:
        if server:
            server.terminate()


if __name__ == "__main__":
    main()
