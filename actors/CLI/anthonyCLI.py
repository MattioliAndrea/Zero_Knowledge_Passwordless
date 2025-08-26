import argparse
import os
import sys
import time
import threading
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from actors.anthonyCore import AnthonyCore

def print_header(active, listen_port, forward_port):
    print("🕵️ Anthony Proxy CLI")
    print(f"📡 Listening on localhost:{listen_port}")
    print(f"➡️ Forwarding to localhost:{forward_port}")
    print(f"🔁 Mode: {'ACTIVE 🔴' if active else 'PASSIVE 🟢'}")
    print("=" * 50)

def print_logs(log_queue):
    print("\n📜 Messaggi registrati:")
    if not log_queue:
        print("ℹ️  Nessun messaggio ancora registrato.")
        return
    for entry in log_queue[-20:]:
        timestamp = time.strftime('%H:%M:%S', time.localtime(entry.get("timestamp", time.time())))
        direction = entry.get("direction", "UNKNOWN")
        message = entry.get("message", {})
        print(f"\n[{timestamp}] {direction}")
        if isinstance(message, dict):
            print(json.dumps(message, indent=2, ensure_ascii=False))
        else:
            print(str(message))
    print("=" * 50)

def print_brute_targets(targets):
    if targets:
        print("🎯 Brute Force Targets:")
        for user_id, info in targets.items():
            print(f" - {user_id}: {info.get('public_key', 'N/A')}")
        print("=" * 50)

def main():
    parser = argparse.ArgumentParser(description="AnthonyCLI - Proxy Peggy/Victor")
    parser.add_argument("--mode", choices=["active", "passive"], default="passive", help="Modalità operativa")
    parser.add_argument("--listen-port", type=int, default=8081, help="Porta di ascolto")
    parser.add_argument("--forward-port", type=int, default=8080, help="Porta di inoltro")
    parser.add_argument("--refresh-interval", type=float, default=2.0, help="Secondi tra aggiornamenti log")
    args = parser.parse_args()

    active = args.mode == "active"

    # Init AnthonyCore
    anthony = AnthonyCore(
        listen_port=args.listen_port,
        forward_port=args.forward_port,
        active_mode=active
    )

    threading.Thread(target=anthony.start_proxy, daemon=True).start()

    print_header(active, args.listen_port, args.forward_port)

    try:
        while True:
            time.sleep(args.refresh_interval)

            logs = anthony.get_log_queue()
            print_logs(logs)
            print_brute_targets(anthony.brute_force_targets)

            cmd = input("Comando (Enter = refresh, clear = pulisci log, q = esci): ").strip().lower()
            if cmd == "q":
                print("🛑 Uscita da Anthony.")
                break
            elif cmd == "clear":
                anthony.log_queue.clear()
                print("✅ Log puliti.")
            elif cmd != "":
                print(f"⚠️ Comando sconosciuto: '{cmd}'")

    except KeyboardInterrupt:
        print("\n🛑 Interrotto manualmente.")

if __name__ == "__main__":
    main()
