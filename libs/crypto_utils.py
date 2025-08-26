import hashlib
import secrets
from typing import Dict, Any, Tuple
from Crypto.Util import number
from libs.interfaces.icrypto_utils import ICryptoUtils
from multiprocessing import Pool, cpu_count
from Crypto.Util import number

# GLOBAL FIXED PARAMETERS FOR ALL CLIENTS
# These parameters are shared across all users and sessions
# GLOBAL_PARAMETERS = {
#     "p": 2147483647,  # 32-bit prime (2^31 - 1, Mersenne prime)
#     "g": 5,           # Generator
#     "q": 1073741823,  # (p-1)/2 
#     "bit_length": 32
# }



class CryptoUtils(ICryptoUtils):
    
    # @staticmethod
    # def get_global_parameters() -> Dict[str, Any]:
    #     """
    #     Get global system parameters used by all clients
    #     Returns consistent parameters for all users
    #     """
    #     return GLOBAL_PARAMETERS.copy()
    
    #SINGLE THREAD
    @staticmethod
    def generate_safe_prime(bit_length: int) -> Tuple[int, int, int]:
        """
        Genera un safe prime p = 2q + 1 con q primo, e un generatore g.
        Usa la libreria Crypto.Util.number.
        """
        while True:
            q = number.getPrime(bit_length - 1)
            p = 2 * q + 1
            if number.isPrime(p):
                g = CryptoUtils.find_generator(p, q)
                return p, g, q
    
    @staticmethod
    def find_generator(p: int, q: int) -> int:
        """
        Trova un generatore g per il gruppo Z_p* con ordine q.
        """
        for h in range(2, p-1):
            g = pow(h, (p - 1) // q, p)
            if g != 1 and pow(g, q, p) == 1: #and pow(g, 1, p) != 1 g appartiene al sottogruppo di ordine q
                return g
        raise ValueError("Nessun generatore valido trovato.")
    #SINGLE THREAD
    
    #PARALLEL
    def try_generate_safe_prime(bit_length: int):
        """
        Worker process to try generating a safe prime.
        """
        while True:
            q = number.getPrime(bit_length - 1)
            p = 2 * q + 1
            if number.isPrime(p):
                g = CryptoUtils.find_generator(p, q)
                return p, g, q

    @staticmethod
    def generate_safe_prime_parallel(bit_length: int, workers: int = None) -> Tuple[int, int, int]:
        """
        Genera un safe prime p = 2q + 1 con q primo e trova un generatore g, in parallelo.
        """
        workers = workers or cpu_count()

        with Pool(workers) as pool:
            results = [pool.apply_async(CryptoUtils.try_generate_safe_prime, args=(bit_length,)) for _ in range(workers)]

            for r in results:
                try:
                    p, g, q = r.get(timeout=180)  # Timeout per worker
                    pool.terminate()
                    return p, g, q
                except Exception:
                    continue

        raise RuntimeError(f"Safe prime non trovato entro il tempo limite per {bit_length} bit.")
    #PARALLEL
    
    @staticmethod
    def hash_password(password: str, salt: str = "") -> int:
        """
        Hash password with optional salt to create integer secret
        Returns integer in appropriate range for ZKP
        """
        combined = f"{password}{salt}".encode('utf-8')
        digest = hashlib.sha256(combined).digest()
        hash_int = int.from_bytes(digest, 'big')
        return hash_int
    
    @staticmethod
    def generate_nonce(max_value: int) -> int:
        """
        Generate cryptographically secure random integer
        Returns random integer in range [1, max_value-1]
        """
        return secrets.randbelow(max_value - 1) + 1
    
    @staticmethod
    def generate_challenge(max_value: int) -> int:
        return CryptoUtils.generate_nonce(max_value)


    @staticmethod
    def generate_system_parameters(bit_length: int) -> Dict[str, Any]:
        """
        Generate system-wide parameters for ZKP
        Returns global fixed parameters for all users
        """
        if bit_length is not None:
            p, g, q = CryptoUtils.generate_safe_prime_parallel(bit_length)
            return {
                "p": p,
                "g": g,
                "q": q,
                "bit_length": bit_length
            }
        else:
            print("[generate_system_parameters] CHIAMATO CON BIT_LENGHT NULLO")
            exit(1)
            
        print(f"[DEBUG_GEN] bit_length={bit_length}, p={p}, q={q}, g={g}")
        
    
    @staticmethod
    def check_parameter_consistency(stored_params: Dict[str, Any], expected_params: Dict[str, Any]) -> bool:
        """
        Check if stored parameters match expected system parameters.
        Returns True if parameters are consistent, False otherwise
        """
        for key in ['p', 'g', 'q']:
            if key not in stored_params or stored_params[key] != expected_params[key]:
                print(f"[DEBUG] Mismatch in key '{key}': stored={stored_params.get(key)}, expected={expected_params.get(key)}")
                return False
        return True