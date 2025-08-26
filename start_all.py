import argparse
import subprocess
import time
import webbrowser
import os

BASE_DIR = os.chdir(os.path.dirname(os.path.abspath(__file__)))

mail: subprocess.Popen[bytes]
malia: subprocess.Popen[bytes]
victor: subprocess.Popen[bytes]
anthony: subprocess.Popen[bytes]
peggy: subprocess.Popen[bytes]

def run_process(cmd, cwd=None):
    return subprocess.Popen(cmd, cwd=cwd or BASE_DIR)

def run_separate_process(cmd, cwd=None,title=""):
    joined_cmd = " ".join(cmd)
    terminal_cmd = ["cmd", "/c", "start","cmd", "/k",f"title {title} && {joined_cmd} "]
    return subprocess.Popen(terminal_cmd, cwd=cwd or BASE_DIR)

def start_gui():
    print("📬 Avvio Mailbox GUI...")
    global mail
    mail=run_process(["cmd", "/c", "start", "firefox ","http://localhost:8025/"])
    
    print("📱💻🖥️ Avvio Malia GUI...")
    global malia
    mail=run_process(["streamlit", "run", "actors/malia_VictorPatner.py","--server.port","8503"])
    
    print("🧑‍⚖️ Avvio Victor GUI...")
    global victor
    victor=run_process(["streamlit", "run", "actors/GUI/victorGUI.py"])
    
    time.sleep(1)
    
    print("🕵️ Avvio Anthony GUI...")
    global anthony
    anthony=run_process(["streamlit", "run", "actors/GUI/anthonyGUI.py"])
    
    time.sleep(1)
    
    print("👩‍💻 Avvio Peggy GUI...")
    global peggy
    peggy=run_process(["streamlit", "run", "actors/GUI/peggyGUI.py"])


def start_cli():
    print("🧑‍⚖️ Avvio Victor CLI...")
    global victor
    victor=run_separate_process(["python", "actors/CLI/victorCLI.py", "--listen"],title="Victor")

    print("🕵️ Avvio Anthony CLI...")
    global anthony
    anthony=run_separate_process(["python", "actors/CLI/anthonyCLI.py", "--mode", "active", "--listen-port", "8081", "--forward-port", "8080"],title="Anthony")

    print("👩‍💻 Avvio Peggy CLI...")
    global peggy
    peggy=run_separate_process(["python", "actors/CLI/peggyCLI.py","--host", "localhost", "--port", "8081"],title="Peggy")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Avvio coordinato di tutti i componenti")
    parser.add_argument("--mode", choices=["gui", "cli"], default="gui", help="Modalità da avviare")
    args = parser.parse_args()
    try:
        if args.mode == "gui":
            start_gui()
        else:
            start_cli()
    except KeyboardInterrupt:
        print("🛑 Arresto manuale in corso...")
        victor.terminate()
        anthony.terminate()
        peggy.terminate()