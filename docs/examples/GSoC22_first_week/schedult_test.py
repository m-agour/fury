import schedule
import time

t = time.perf_counter()


def job():
    global t
    print(time.perf_counter() - t)
    t = time.perf_counter()


schedule.every(0.016).seconds.do(job)


while True:
    schedule.run_pending()
    time.sleep(.000001)

