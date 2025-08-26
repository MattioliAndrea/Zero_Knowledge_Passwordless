def main():
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
    import streamlit as st
    from streamlit_autorefresh import st_autorefresh
    import json
    import time
    import threading
    from actors.anthonyCore import AnthonyCore

    # Stato condiviso
    if "anthony" not in st.session_state:
        st.session_state.anthony = AnthonyCore(active_mode=False)
        threading.Thread(target=st.session_state.anthony.start_proxy, daemon=True).start()
        
    if "last_log_count" not in st.session_state:
        st.session_state.last_log_count = 0

    if "sidebar_logs" not in st.session_state:
        st.session_state.sidebar_logs = []
    sidebar_logs = st.session_state.anthony.sidebar_logs

    # UI
    st.set_page_config(page_title="Anthony Proxy", layout="wide")

    st.title("🕵️ Anthony - Proxy tra Peggy e Victor")



    mode = st.sidebar.toggle("Modalità attaccante attivo", value=st.session_state.anthony.active_mode)
    st.session_state.anthony.active_mode = mode

    bg_color = "#0e1117" if mode else "#fafafa"
    txt_color = "#fafafa" if mode else "#29b09d"

    st.markdown(f"""
    <style>
    .stApp {{
        background-color: {bg_color};
        color: {txt_color};
    }}
    </style>
    """, unsafe_allow_html=True)

    # Auto-refresh every 2 seconds
    st_autorefresh(interval=2000, key="refresh")


    st.subheader("📜 Log dei messaggi")
        
    # Get current logs from Anthony
    current_logs = st.session_state.anthony.get_log_queue()
    current_count = len(current_logs)
    
    # Show log count and last update time
    st.write(f"**Log entries: {current_count}** | Last update: {time.strftime('%H:%M:%S')}")
        
    if st.button("Pulisci log"):
        st.session_state.anthony.log_queue.clear()
        st.rerun()
        
    # Display logs
    if current_logs:
        log_display = ""
        for i, entry in enumerate(current_logs[-current_count:]):  # Show last 20 entries, newest first
            timestamp = entry.get('timestamp', time.time())
            time_str = time.strftime('%H:%M:%S', time.localtime(timestamp))
            direction = entry['direction']
            message = entry['message']
                
            if isinstance(message, dict):
                message_str = json.dumps(message, indent=2, ensure_ascii=False)
            else:
                message_str = str(message)
            
            log_display += f"**{direction}**\n```json\n{message_str}\n```\n\n"
            
        st.markdown(log_display or "_Nessun messaggio ancora registrato_", unsafe_allow_html=True)
    else:
        st.info("_Nessun messaggio ancora registrato_")
            
    st.sidebar.title("⚙️ Impostazioni") 
    # Show connection status
    st.sidebar.subheader("📊 Status")
    st.sidebar.write(f"**Listening on:** {st.session_state.anthony.listen_host}:{st.session_state.anthony.listen_port}")
    st.sidebar.write(f"**Forwarding to:** {st.session_state.anthony.forward_host}:{st.session_state.anthony.forward_port}")
    st.sidebar.write(f"**Active mode:** {'🔴 ON' if st.session_state.anthony.active_mode else '🟢 OFF'}")
    st.sidebar.subheader("🧠 Brute Force Log")
    if sidebar_logs:
        for entry in sidebar_logs:
            msg = entry["message"]
            st.sidebar.markdown(f"```json{msg}```")
    else:
        st.sidebar.info("Nessun log brute-force recente.")
        
    if st.session_state.anthony.brute_force_targets:
        st.subheader("🎯 Brute Force Targets")
        for user_id, target_info in st.session_state.anthony.brute_force_targets.items():
            st.write(f"**{user_id}:** {target_info.get('public_key', 'N/A')}")
        
if __name__ == "__main__":  # 🔒 necessaria per multiprocessing su Windows
    main()