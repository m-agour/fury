import time
import ctypes
import sys
from matplotlib import pyplot as plt

if sys.platform == 'win32' and sys.version_info[1] < 11:
    winmm = ctypes.WinDLL('winmm')
    winmm.timeBeginPeriod(1)

x, y = [], []
t = time.perf_counter()
for i in range(0, 101):
    t = time.perf_counter()
    time.sleep(i/1000)
    x.append(i)
    y.append((time.perf_counter() - t) * 1000)

plt.plot(x, y)
plt.xlabel("Specified offset in ms")
plt.ylabel("Actual offset in ms")
plt.title("Figure 1: The improved time accuracy in windows")
plt.savefig("callback timing.png")
plt.show()
