from multiprocessing import cpu_count
import os
import json
import time
import random
from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED
from Crypto.Util import number
from typing import Dict, List

CACHE_FOLDER = "cache"
os.makedirs(CACHE_FOLDER, exist_ok=True)


def find_generators(p: int, q: int, count: int = 5, deadline: float | None = None) -> list[str] | None:
    found = set()
    max_tries = 10000  # evita loop infiniti
    tries = 0

    while len(found) < count and tries < max_tries:
        if deadline and time.time() > deadline:
            break
        h = random.randrange(2, p - 1)
        g = pow(h, (p - 1) // q, p)
        if g != 1 and pow(g, q, p) == 1:
            found.add(str(g))
        tries += 1

    return list(found) if found else None


def generate_safe_prime(bit_length: int, deadline: float | None = None, g_count: int = 5) -> list[Dict[str, str]] | None:
    try:
        if deadline and time.time() > deadline:
            return None
        q = number.getPrime(bit_length - 1)

        if deadline and time.time() > deadline:
            return None
        p = 2 * q + 1
        
        if not number.isPrime(p):
            return None

        if deadline and time.time() > deadline:
            return None
        g = find_generators(p, q, count=g_count, deadline=deadline)
        print(f"[DEBUG] Found g: {g}")
        if not g:
            return None
        list=[]
        for gen in g: 
            list.append({"p": str(p), "q": str(q),"g":gen})
        
        return list
    except Exception as e:
        print(f"[!] Errore interno: {e}")
        return None


def generate_many_safe_primes(bit_length: int, duration_seconds: int = 10) -> List[Dict[str, str]]:  
    """, max_workers: int = 8"""
    start_time = time.time()
    deadline = start_time + duration_seconds
    results = []
    max_workers=cpu_count()
    with ProcessPoolExecutor(max_workers) as executor:
        futures = {
            executor.submit(generate_safe_prime, bit_length, deadline): None
            for _ in range(max_workers)
        }

        while futures and time.time() < deadline:
            remaining = deadline - time.time()
            if remaining <= 0:
                break
            done, _ = wait(futures, return_when=FIRST_COMPLETED, timeout=remaining)
            for fut in done:
                futures.pop(fut)
                try:
                    res = fut.result()
                    if res:
                        results.extend(res)
                except Exception as e:
                    print(f"[!] Errore nel future: {e}")
                # Submit nuovo task se c'è ancora tempo
                if time.time() < deadline:
                    futures[executor.submit(generate_safe_prime, bit_length, deadline)] = None

    return results

def append_to_cache_file(bit_length: int, new_entries: list):
    cache_file = os.path.join(CACHE_FOLDER, f"{bit_length}.json")

    # Carica contenuto esistente
    if os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            try:
                existing = json.load(f)
                if not isinstance(existing, list):
                    existing = []
            except json.JSONDecodeError:
                existing = []
    else:
        existing = []

    # Aggiungi nuovi
    existing.extend(new_entries)

    with open(cache_file, "w") as f:
        json.dump(existing, f, indent=2)

    print(f"[💾] Totale parametri salvati in {cache_file}: {len(existing)}")


def generate_and_cache(bit_length: int, duration_seconds: int = 10):
    print(f"[⏳] Generazione parametri ZKP per {bit_length} bit per {duration_seconds}s...")
    primes = generate_many_safe_primes(bit_length, duration_seconds)
    if primes:
        append_to_cache_file(bit_length, primes)
    else:
        print(f"[⚠] Nessun parametro generato per {bit_length} bit.")
    return primes


if __name__ == "__main__":
    # Puoi cambiare questi valori a piacimento
    print(cpu_count())
    for bits in [2048]:
        generate_and_cache(bits, duration_seconds=600)
 