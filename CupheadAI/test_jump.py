# test_jump.py
import time
from pynput.keyboard import Controller, Key

kb = Controller()

print("Switch to Cuphead window in 3 seconds...")
time.sleep(3)

for i in range(5):
    print("JUMP")
    kb.press(Key.space)
    time.sleep(0.05)
    kb.release(Key.space)
    time.sleep(1)
