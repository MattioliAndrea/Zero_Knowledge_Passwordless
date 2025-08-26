import sys
import os
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from libs.crypto_utils import CryptoUtils
from actors.victorCore import VictorCore
from libs.zkp_core import ZKPCore

def test_victor_accepts_multiple_key_lengths():
    victor = VictorCore()


    users = [
        {"user_id": "minnie", "password": "topolino", "bit_length": 8},
        {"user_id": "minnie", "password": "topolino", "bit_length": 16},
        {"user_id": "minnie", "password": "topolino", "bit_length": 32},
        {"user_id": "pippo", "password": "plutone", "bit_length": 64},
        {"user_id": "pippo", "password": "plutone", "bit_length": 128},
        {"user_id": "paperone", "password": "dollar", "bit_length": 256},
        {"user_id": "paperone", "password": "dollar", "bit_length": 512},
        {"user_id": "paperone", "password": "dollar", "bit_length": 1024},
        {"user_id": "paperone", "password": "dollar", "bit_length": 2048}
    ]
    
    for user in users:
        print(f"\n🔍 Testing user '{user['user_id']}' con chiave {user['bit_length']} bit")
        system_params = victor.utils.generate_system_parameters(user["bit_length"])
        # 1. Genera parametri ZKP

        print(f"sys_par: {system_params}")
        password_hash = victor.utils.hash_password(user["password"], user["user_id"])
        print(f"pass_hash: {password_hash}")
        public_key = victor.zkp.generate_public_key(user['password'], user['user_id'], system_params)
        print(f"pub_key: {public_key}")

        # 2. Simula registrazione a Victor
        registration_msg = {
            "type": "registration_request",
            "user_id": user["user_id"],
            "public_key": public_key,
            "system_params": system_params
        }
        assert victor.register_user(registration_msg["user_id"],registration_msg["public_key"],registration_msg["system_params"])["success"],f"Registrazione fallita per {user['user_id']}" 
        

        # 3. Flusso ZKP: Peggy → Victor
        commitment, nonce = victor.zkp.create_commitment(user["password"], user["user_id"], system_params)
        print(f"commitment: {commitment}")
        print(f"nounce: {nonce}")
        q = system_params["q"]
        challenge = victor.generate_challenge(q)
        print(f"challenge: {challenge}")
        response = victor.zkp.create_response(nonce, challenge, user["password"], user["user_id"], system_params)
        print(f"response: {response}")

        # 4. Verifica
        result = victor.verify_proof(user["user_id"],registration_msg["public_key"], commitment, challenge, response)
        print(f"result: {result}")
        assert result["success"], f"❌ Verifica fallita per {user['user_id']}"
        print(f"✅ Verifica ZKP riuscita per {user['user_id']}")

if __name__ == "__main__":
    test_victor_accepts_multiple_key_lengths()
