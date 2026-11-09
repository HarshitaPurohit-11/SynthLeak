"""
SynthLeak Local Process Termination Utility.
Finds and terminates any local processes listening on backend (8000) and frontend (5173) ports.
"""

import os
import subprocess
import sys


def terminate_port(port: int) -> None:
    try:
        # Run netstat to locate listening sockets on Windows
        output = subprocess.check_output("netstat -ano", shell=True, text=True, stderr=subprocess.DEVNULL)
        target = f":{port}"
        pids = set()

        for line in output.splitlines():
            line_clean = line.strip()
            if target in line_clean and "LISTENING" in line_clean.upper():
                parts = line_clean.split()
                if parts:
                    pid_str = parts[-1]
                    if pid_str.isdigit():
                        pid = int(pid_str)
                        if pid > 0 and pid != os.getpid():
                            pids.add(pid)

        for pid in pids:
            try:
                subprocess.call(
                    f"taskkill /F /PID {pid}",
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                print(f"[OK] Terminated process on port {port} (PID {pid})")
            except Exception:
                pass

        if not pids:
            print(f"[INFO] Port {port} is free (no active listener).")

    except Exception as e:
        print(f"[WARN] Unable to inspect port {port}: {e}")


def main():
    print("Stopping active SynthLeak services...")
    terminate_port(8000)
    terminate_port(5173)


if __name__ == "__main__":
    main()

