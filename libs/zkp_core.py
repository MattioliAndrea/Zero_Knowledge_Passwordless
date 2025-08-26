from typing import Tuple
from typing import Dict, Any
from libs.crypto_utils import CryptoUtils
from libs.interfaces.icrypto_utils import ICryptoUtils
from libs.interfaces.izkp_core import IZKPCore

class ZKPCore(IZKPCore):
    """
    Core Zero-Knowledge Proof protocol functions
    Based on Schnorr's identification scheme
    Uses global fixed parameters for all users
    """
    def __init__(self, utils: ICryptoUtils = None):
        self.crypto = utils or CryptoUtils()

    def generate_public_key(self, password: str, user_id: str, system_params: dict) -> int:
        """
        Generate public key using the correct system parameters.
        """
        q = int(system_params["q"])
        g = int(system_params["g"])
        p = int(system_params["p"])
        private_key = (self.crypto.hash_password(password, user_id) % (q - 1)) + 1
        print(f"[DEBUG_public_key] Private key used: {private_key}")
        return pow(g, private_key, p)

    def create_commitment(self, password: str, user_id: str, system_params: dict) -> Tuple[int, int]:
        """
        Create commitment for ZKP with specific system parameters
        """
        q = int(system_params["q"])
        g = int(system_params["g"])
        p = int(system_params["p"])
        nonce = self.crypto.generate_nonce(q)
        return pow(g, nonce, p), nonce

    def create_response(self, nonce: int, challenge: int, password: str, user_id: str, system_params: dict) -> int:
        """
        Create response to challenge using device-specific parameters
        """
        q = int(system_params["q"])
        private_key = (self.crypto.hash_password(password, user_id) % (q - 1)) + 1
        print(f"[DEBUG_response] Private key used: {private_key}")
        return (nonce + challenge * private_key) % q

    def verify_response(self, commitment, challenge, response, public_key, system_params):
        """
        Verify the proof
        Checks if g^response ≡ commitment * public_key^challenge (mod p)
        """
        p = int(system_params["p"])
        g = int(system_params["g"])
        lhs = pow(g, response, p)
        rhs = (commitment * pow(public_key, challenge, p)) % p
        
        if lhs == rhs:
            print("[ZKP] ✅ Prova superata")
        else:
            print("[ZKP] ❌ Prova fallita")
            print(f"    - LHS: {lhs}")
            print(f"    - RHS: {rhs}")
            print(f"    - commitment: {commitment}")
            print(f"    - challenge: {challenge}")
            print(f"    - response: {response}")
            print(f"    - public_key: {public_key}")
            print(f"    - g: {g}")
            print(f"    - p: {p}")
        
        return lhs == rhs
    
    def generate_challenge(self, q: int) -> int:
        """Generate random challenge"""
        return self.crypto.generate_challenge(q)
    
    # WARNING FUNCTIONS
    def get_security_info(self) -> dict:
        """
        Returns dict with security info and educational notes
        """
        return {
            "educational_note": "Educational implementation - not for production use",
            "real_world_note": "Production systems use 2048+ bit primes with additional security measures"
        }