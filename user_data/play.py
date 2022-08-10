import concurrent.futures
import random
import time


def delayed_print(text="Dor is the king",time_delay=None):
    if time_delay is None:
        time_delay = random.randint(2,10)

    time.sleep(time_delay)
    print(f'{text} after {time_delay}')


analyze_user_threads_pool = concurrent.futures.ThreadPoolExecutor(max_workers=10)



for _ in range(10):
    analyze_user_threads_pool.submit(delayed_print,"Only dor")

time.sleep(30)

