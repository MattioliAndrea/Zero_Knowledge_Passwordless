import math
from Crypto.Util.number import inverse
from multiprocessing import Pool, cpu_count

class BruteForceWorker:
        
    def giant_worker(args):
        start_i, chunk_size, factor, g, y, p, baby_table, m = args
        for i in range(start_i, min(start_i + chunk_size, m)):
            gamma = (y * pow(factor, i, p)) % p
            if gamma in baby_table:
                return i * m + baby_table[gamma]
        return None

    def _baby_step_giant_step( g, y, p, q):
        m = int(math.isqrt(q)) + 1
        table = {pow(g, j, p): j for j in range(m)}
        #factor = pow(g, -m, p)
        factor=inverse(pow(g, m, p), p)
        gamma = y
        for i in range(m):
            if gamma in table:
                return i * m + table[gamma]
            gamma = (gamma * factor) % p
        return None

    def _baby_step_giant_step_parallel( g, y, p, q):
        m = int(math.isqrt(q)) + 1
        baby_table = {pow(g, j, p): j for j in range(m)}  # Baby-step table (shared)

        factor = inverse(pow(g, m, p), p)
        num_workers = cpu_count()
                
        # Suddividi il lavoro in blocchi per ciascun processo
        chunk_size = m // num_workers + 1

        # Crea indici di partenza per ciascun worker
        start_indices = list(range(0, m, chunk_size))
                
        # Impacchetta gli argomenti per ogni worker
        args_list = [(start_i, chunk_size, factor, g, y, p, baby_table, m) for start_i in start_indices]
        
        
        with Pool(processes=num_workers) as pool:
            results = pool.map(BruteForceWorker.giant_worker, args_list)

        # Restituisci il primo risultato valido trovato
        for result in results:
            if result is not None:
                return result
        return None