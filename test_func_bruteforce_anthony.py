from actors.anthonyCore import AnthonyCore

def test_bruteforce():
    # Parametri di esempio (piccoli per test)
    # Privato x = 17
    # g = 2
    # q = 104729  # primo grande
    # p = 2 * q + 1  # p = 209459
    # y = pow(g, 17, p)  # public_key = g^x mod p
    g="4"
    p="4127794247"
    q="2063897123"
    y="3295856956"
    

    # Simula messaggio in arrivo da Peggy
    test_msg = {
        "user_id": "p",
        "device_public_key": {
            "public_key": str(y),
            "system_params": {
                "g": str(g),
                "p": str(p),
                "q": str(q),
                "bit_length": "32"
            }
        },
        "type": "response"
    }

    # Istanza AnthonyCore
    anthony = AnthonyCore(active_mode=True)

    # Esegui brute-force
    anthony._attempt_bruteforce(test_msg)

if __name__ == "__main__":
    test_bruteforce()
