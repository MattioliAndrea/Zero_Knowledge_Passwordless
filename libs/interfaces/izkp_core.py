from abc import ABC, abstractmethod

class IZKPCore(ABC):
    @abstractmethod
    def generate_public_key(self, password: str, user_id: str) -> int:
        pass

    @abstractmethod
    def create_commitment(self, password: str, user_id: str, system_params: dict) -> tuple[int, int]:
        pass

    @abstractmethod
    def create_response(self, nonce: int, challenge: int, password: str, user_id: str, system_params: dict) -> int:
        pass

    @abstractmethod
    def verify_response(self, commitment: int, challenge: int, response: int, public_key: int,system_params: dict) -> bool:
        pass

    @abstractmethod
    def generate_challenge(self,q: int) -> int:
        pass

    @abstractmethod
    def get_security_info(self) -> dict:
        pass