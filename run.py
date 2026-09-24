#!/usr/bin/env python3
"""
PharmaGuard Environment & Service Launcher
==========================================
Launches both the local Ollama inference daemon and the Streamlit clinical
evaluation dashboard in separate, dedicated terminal windows.

Usage:
    python run.py
    python run.py --port 8501
    python run.py --no-ollama

Owner: Krishna Sikheriya (IIT2023139) | Group 07, IIIT Allahabad
"""
from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# Paths
REPO_ROOT = Path(__file__).resolve().parent
DASHBOARD_SCRIPT = REPO_ROOT / "scripts" / "dashboard.py"


def get_venv_python() -> str:
    """Detect and return the virtual environment Python executable if available."""
    if platform.system() == "Windows":
        candidates = [
            REPO_ROOT / ".venv" / "Scripts" / "python.exe",
            REPO_ROOT / "venv" / "Scripts" / "python.exe",
        ]
    else:
        candidates = [
            REPO_ROOT / ".venv" / "bin" / "python",
            REPO_ROOT / "venv" / "bin" / "python",
        ]

    for cand in candidates:
        if cand.is_file():
            return str(cand)
    return sys.executable


def is_ollama_running(url: str = "http://localhost:11434", timeout: float = 1.5) -> bool:
    """Check whether the Ollama local inference daemon is already active."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.status == 200
    except Exception:
        return False


def is_port_in_use(port: int) -> bool:
    """Check whether a local TCP port is already bound."""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def find_free_port(start_port: int, max_attempts: int = 20) -> int:
    """Find the first available TCP port starting from start_port."""
    for p in range(start_port, start_port + max_attempts):
        if not is_port_in_use(p):
            return p
    return start_port


def launch_in_new_terminal(title: str, command: str, cwd: Path) -> None:
    """Launch a command in a new dedicated terminal window based on operating system."""
    system = platform.system()

    if system == "Windows":
        # Check if Windows Terminal (wt) is available for modern tabbed/windowed experience
        powershell_exe = shutil.which("powershell.exe") or "powershell.exe"
        cmd_str = (
            f"Set-Location -LiteralPath '{cwd}'; "
            f"$host.UI.RawUI.WindowTitle = '{title}'; "
            f"{command}"
        )
        # Use cmd /c start to spawn an independent new PowerShell window
        subprocess.Popen(
            ["cmd.exe", "/c", "start", title, powershell_exe, "-NoExit", "-Command", cmd_str],
            cwd=str(cwd),
            shell=False,
        )

    elif system == "Darwin":  # macOS
        apple_script = (
            f'tell application "Terminal"\n'
            f'    do script "cd {cwd} && {command}"\n'
            f'    activate\n'
            f'end tell'
        )
        subprocess.Popen(["osascript", "-e", apple_script])

    else:  # Linux
        # Detect installed terminal emulator
        terminals = [
            ("gnome-terminal", ["gnome-terminal", "--title", title, "--", "bash", "-c", f"cd '{cwd}' && {command}; exec bash"]),
            ("xterm", ["xterm", "-T", title, "-e", f"cd '{cwd}' && {command}; exec bash"]),
            ("konsole", ["konsole", "--title", title, "-e", f"bash -c 'cd \"{cwd}\" && {command}; exec bash'"]),
            ("xfce4-terminal", ["xfce4-terminal", "--title", title, "-e", f"bash -c 'cd \"{cwd}\" && {command}; exec bash'"]),
        ]
        spawned = False
        for term_name, term_cmd in terminals:
            if shutil.which(term_name):
                subprocess.Popen(term_cmd, cwd=str(cwd))
                spawned = True
                break

        if not spawned:
            print(f"⚠️  No desktop terminal emulator found. Starting {title} in background...")
            subprocess.Popen(command, cwd=str(cwd), shell=True)


def print_banner():
    banner = """
========================================================================
  🛡️  PharmaGuard — Autonomous Postmarketing Signal Triage System
  Orchestrating Local Ollama LLM Daemon + Streamlit Evaluation Dashboard
========================================================================
"""
    print(banner)


def main():
    parser = argparse.ArgumentParser(
        description="Launch Ollama daemon and Streamlit evaluation dashboard in separate terminals."
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8501,
        help="Port to run the Streamlit dashboard on (default: 8501)",
    )
    parser.add_argument(
        "--no-ollama",
        action="store_true",
        help="Skip launching Ollama (use if solely using cloud Gemini backend)",
    )
    parser.add_argument(
        "--ollama-model",
        type=str,
        default="qwen2.5:7b",
        help="Target local LLM model for Ollama (default: qwen2.5:7b)",
    )
    args = parser.parse_args()

    print_banner()

    python_bin = get_venv_python()
    print(f"[*] Python Interpreter : {python_bin}")
    print(f"[*] Project Root       : {REPO_ROOT}")
    print(f"[*] Streamlit App      : {DASHBOARD_SCRIPT}")
    print("-" * 72)

    # ── 1. Ollama Daemon Launch ──
    if not args.no_ollama:
        ollama_bin = shutil.which("ollama")
        if not ollama_bin:
            print("[!] WARNING: 'ollama' executable was not found on your system PATH.")
            print("    Please install Ollama from https://ollama.com if you wish to run offline.")
        elif is_ollama_running():
            print("[✓] Ollama Daemon       : Already active and serving on http://localhost:11434")
        else:
            print("[+] Launching Ollama in a separate terminal window...")
            launch_in_new_terminal(
                title="PharmaGuard — Ollama Local Inference (qwen2.5:7b)",
                command="ollama serve",
                cwd=REPO_ROOT,
            )
            print("    Waiting for Ollama service to respond on http://localhost:11434...")
            for _ in range(10):
                time.sleep(1.0)
                if is_ollama_running():
                    print("[✓] Ollama Daemon       : Online and ready on http://localhost:11434")
                    break
            else:
                print("    (Ollama is starting up in its dedicated terminal window)")
    else:
        print("[i] Ollama launch skipped (--no-ollama flag provided).")

    # ── 2. Streamlit Dashboard Launch ──
    target_port = args.port
    if is_port_in_use(target_port):
        free_port = find_free_port(target_port)
        print(f"[!] NOTICE: Port {target_port} is already in use by another process.")
        print(f"[✓] Automatically re-routing Streamlit to free port: {free_port}")
        target_port = free_port

    print(f"[+] Launching Streamlit Dashboard on port {target_port} in a separate terminal window...")
    streamlit_cmd = (
        f"& '{python_bin}' -m streamlit run '{DASHBOARD_SCRIPT}' "
        f"--server.port {target_port} --server.headless false"
        if platform.system() == "Windows"
        else f"'{python_bin}' -m streamlit run '{DASHBOARD_SCRIPT}' --server.port {target_port}"
    )

    launch_in_new_terminal(
        title=f"PharmaGuard — Clinical Evaluation Dashboard (Port {target_port})",
        command=streamlit_cmd,
        cwd=REPO_ROOT,
    )

    print("-" * 72)
    print("🚀 Both services have been launched into dedicated terminal windows!")
    print(f"   • Evaluation Dashboard : http://localhost:{target_port}/")
    if not args.no_ollama:
        print(f"   • Ollama API Endpoint  : http://localhost:11434/")
        print(f"   • Model Requirement    : 'ollama run {args.ollama_model}' (if not pulled yet)")
    print("-" * 72)
    print("You may safely close this launcher script. The terminals will continue running.")


if __name__ == "__main__":
    main()
