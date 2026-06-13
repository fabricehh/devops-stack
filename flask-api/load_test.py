import requests
import threading

URL = "https://flask-api.devitlab.ddns.net"
TOTAL = 10_000
THREADS = 20


def worker(n):
    for _ in range(n):
        try:
            requests.get(URL, timeout=5)
        except Exception:
            pass


per_thread = TOTAL // THREADS
threads = [threading.Thread(target=worker, args=(per_thread,)) for _ in range(THREADS)]

print(f"Envoi de {TOTAL} requêtes sur {URL} ({THREADS} threads)...")
for t in threads:
    t.start()
for i, t in enumerate(threads, 1):
    t.join()
    print(f"{i * per_thread} / {TOTAL}")

print("Done.")
