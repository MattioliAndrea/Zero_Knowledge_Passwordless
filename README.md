# 🔐 Zero Knowledge Passwordless Login System

Un sistema dimostrativo che implementa un protocollo di autenticazione **Zero-Knowledge Proof** (ZKP) con supporto a:

- ✅ Passwordless login
- 📱💻🖥️ **Gestore dei dispositivi** nominato malia(Mail Devices Manager)
- 🧑‍⚖️ **Verifica lato serve**r nominato Victor (Verifier)
- 👩‍💻 **Client prover** nominato Peggy (Provider)
- 🕵️ **Proxy/Attaccante** (Anthony) in modalità passiva o attiva 
- 🥷 **Emulatore** (Anthony_patner) finge di essere un altro utente
- 📊 Interfaccia Web (Streamlit) o da terminale (CLI)
- 🔐 **Chiavi configurabili** (forti o deboli)
- 💾 Salvataggio credenziali e log
- ☁️ Supporto a MongoDB per gestione utenti/dispositivi su Victor
- 📬 Supporto per l'invio di mail con MailHog 🐖 
- 📨 invio **JWT tokens** con timeout per gestire i dispositivi Client 🖥️💻📱

---

## 📦 Requisiti

- 🐍 Python 3.9+
- 🍃 MongoDB (per Victor)
- 👑 Streamlit
- 🐖 MailHog (per Victor)
- Librerie: `pip install -r requirements.txt`

> File `requirements.txt` consigliato:
>```text
>streamlit
>streamlit-autorefresh
>pymongo
>jwt
>smtplib
>```




## 📐 Struttura del progetto

>```text
>├── docs/
>│   ├── start_all.bat
>│   ├── Zero Knowledge Passwordless Login.pptx
>│   └── Zero Knowledge Passwordless Login.pdf
>├── libs/
>│   ├── zkp_core.py
>│   ├── crypto_utils.py
>│   ├── bruteforce_worker.py
>│   ├── socket.py
>│   ├── file_utils.py
>│   └── interfaces/
>│       ├── izkp_core.py
>│       └── icrypto_utils.py
>├── actors/
>│   ├── peggyCore.py
>│   ├── victorCore.py
>│   ├── anthonyCore.py
>│   ├── anthony_partner.py
>│   ├── malia_VictorPartner.py
>│   ├── CLI/
>│   │   ├── peggyCLI.py
>│   │   ├── victorCLI.py
>│   │   ├── CLI-commands.py
>│   │   ├── test_auth_key.py
>│   │   └── anthonyCLI.py
>│   └── GUI/
>│       ├── peggyGUI.py
>│       ├── victorGUI.py
>│       └── anthonyGUI.py
>├── cache/
>│   ├── 512.json
>│   ├── 1024.json
>│   └── 2048.json
>│
>├── docker-compose.yml
>├── start_all.py
>├── mailHog.yml
>│
>├── test_show_PK_& SK_keys.py
>├── test_func_bruteforce_anthony.py
>├── test_gen_long_key_parallel.py
>├── test_gen_long_key_single.py
>└── README.md

# Esecuzione
## 🍃 DOCKER MongoDB

Installare MongoDB con docker per l'usare Victor <br>
`docker-compose -f docker-compose.yml up -d`

## 🐖 DOCKER MailHog

Installare MailHog con docker per l'usare Victor le funzionalità di devices manage mail <br>
`docker-compose -f mailhog.yml up -d`

---

## RUN COMPLESSIVO
### with CLI
`python start_all.py --mode cli` <br>
**cosa parte?** <br>
👩‍💻 peggyCLI, 🧑‍⚖️ VictorCLI e 🕵️ AnthonyCLI
### with GUI 
`python start_all.py --mode gui`
apri il browser dalla pagina [http://localhost:8501](http://localhost:8501) in poi<br>
**cosa parte?** <br>
👩‍💻 peggyGUI, 🧑‍⚖️ VictorGUI, 🕵️ AnthonyGUI, 📱💻🖥️ Malia (http://localhost:8503) e 🐖 mailHog (http://localhost:8025)

---

## RUN SINGOLI FILE
### 👩‍💻 Peggy CLI (Prover)
`python actors/CLI/peggyCLI.py --host localhost --port 8080`<br>
### 👩‍💻 Peggy GUI (Prover)
`streamlit run actors/GUI/peggyGUI.py`

---

### 🧑‍⚖️ Victor CLI (Verifier)
`python actors/CLI/victorCLI.py --listen` <br>
`python actors/CLI/victorCLI.py --list-users` <br>
`python actors/CLI/victorCLI.py --verify $User`
### 🧑‍⚖️ Victor GUI (Verifier)
`streamlit run actors/GUI/victorGUI.py`

---

### 🕵️ Anthony CLI (Attacker) 
#### &emsp; Modalità passiva (default =>logger )
&emsp; `python actors/CLI/anthonyCLI.py --mode passive --listen-port 8081 --forward-port 8080`
#### &emsp; Modalità attiva (attacca chiavi deboli <= 64 bit)
&emsp; `python actors/CLI/anthonyCLI.py --mode active --listen-port 8081 --forward-port 8080`
### 🕵️ Anthony GUI (Attacker) passiva e attiva
`streamlit run actors/GUI/anthonyGUI.py`
### 🥷 Anthony_patner (The false Prover)
`python actors/anthony_patner.py` 

---

### 📱💻🖥️ Malia (fai l'accesso con un token valido)
`streamlit run actors/malia_VictorPatner.py --server.port 8503`