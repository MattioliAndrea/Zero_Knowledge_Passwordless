from abc import ABC, abstractmethod
from typing import Any, Dict, Tuple

class ICryptoUtils(ABC):
    @abstractmethod
    def hash_password(password: str, user_id: str) -> str:
        pass

    @abstractmethod
    def check_parameter_consistency(params: dict) -> bool:
        pass
    
    @abstractmethod
    def generate_nonce(max_value: int) -> int:
        pass
    
    @abstractmethod
    def generate_challenge(max_value: int) -> int:
        pass
    
    @abstractmethod
    def generate_safe_prime(bit_length: int) -> Tuple[int, int, int]:
        pass
    
    @abstractmethod
    def generate_system_parameters(bit_length: int) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def check_parameter_consistency(stored_params: Dict[str, Any], expected_params: Dict[str, Any]) -> bool:
        pass