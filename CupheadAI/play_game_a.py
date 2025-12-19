import os
# Suppress TensorFlow logs
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import cv2
import numpy as np
import mss
import tensorflow as tf
from ultralytics import YOLO
import time
import math
from pynput import keyboard as pynput_keyboard
from pynput.keyboard import Controller, Key

keyboard_controller = Controller()

# --- KEYBOARD LISTENER ---
class KeyMonitor:
    def __init__(self):
        self.pressed_keys = set()
        self.listener = pynput_keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        self.listener.start()

    def on_press(self, key):
        try:
            if hasattr(key, 'char') and key.char:
                self.pressed_keys.add(key.char)
            else:
                self.pressed_keys.add(key)
        except Exception:
            pass

    def on_release(self, key):
        try:
            if hasattr(key, 'char') and key.char:
                self.pressed_keys.discard(key.char)
            else:
                self.pressed_keys.discard(key)
        except Exception:
            pass

    def is_pressed(self, key_char):
        return key_char in self.pressed_keys

key_monitor = KeyMonitor()

# --- CONFIGURATION ---
MONITOR = {'top': 299, 'left': 1, 'width': 719, 'height': 399}

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
YOLO_PATH = os.path.join(BASE_DIR, "models", "best.pt")
MLP_PATH = os.path.join(BASE_DIR, "models", "potato_mlp_decision.keras")

# Thresholds
YOLO_CONF = 0.13       # Low threshold to catch fast objects
DECISION_THRESH = 0.78 # High threshold to prevent panic jumps

# --- LOAD MODELS ---
print("Loading Models... Please wait.")
yolo_model = YOLO(YOLO_PATH)
mlp_model = tf.keras.models.load_model(MLP_PATH)

print("\n" + "="*40)
print(" CUPHEAD AUTOPILOT READY (MAC OS)")
print("="*40)
print(" controls:")
print("  [P] -> PAUSE / RESUME (Toggle)")
print("  [Q] -> QUIT Bot")
print("  [1] -> Log LOST & Pause")
print("  [2] -> Log WON & Pause")
print("="*40)

def get_box_center(box):
    """Helper to get center from YOLO box"""
    x1, y1, x2, y2 = box.xyxy[0]
    return float((x1 + x2) / 2), float((y1 + y2) / 2)

def main():
    # Physics State
    prev_dist_x = 1280.0
    
    # Bot State
    paused = True 
    print("Status: PAUSED (Press 'p' to start)")

    current_run_start_time = None


    # Initialize Screen Capture
    sct = mss.mss()

    while True:
        try:
            # --- INPUT HANDLING ---
            if key_monitor.is_pressed('q'):
                print("\nBot Stopped by user.")
                break

            if key_monitor.is_pressed('1'):
                print("\n[RESULT] Logged: LOST. Pausing bot...")
                
                duration = 0
                if current_run_start_time is not None:
                    duration = time.time() - current_run_start_time
                    with open("yolo_segments.txt", "a") as f:
                        f.write(f"{duration:.2f},LOST\n")
                    current_run_start_time = None

                with open("game_log.txt", "a") as f:
                    f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - LOST - Survived: {duration:.2f}s\n")
                print(f"Survived: {duration:.2f}s")

                paused = True
                time.sleep(0.3)

            if key_monitor.is_pressed('2'):
                print("\n[RESULT] Logged: WON. Pausing bot...")

                duration = 0
                if current_run_start_time is not None:
                    duration = time.time() - current_run_start_time
                    with open("yolo_segments.txt", "a") as f:
                        f.write(f"{current_run_start_time},{time.time()},WON\n")
                    current_run_start_time = None

                with open("game_log.txt", "a") as f:
                    f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - WON - Survived: {duration:.2f}s\n")
                print(f"Survived: {duration:.2f}s")

                paused = True
                time.sleep(0.3)

            if key_monitor.is_pressed('p'):
                paused = not paused
                if paused:
                    print("\n[PAUSED] Bot sleeping... (You can retry the level now)")
                else:
                    print("\n[RESUMED] Bot active! resetting physics...")
                    # IMPORTANT: Reset physics so bot doesn't think projectile teleported
                    prev_dist_x = 1280.0 
                    current_run_start_time = time.time()
                
                # Small sleep to prevent double-toggling from one keypress
                time.sleep(0.1)

            # --- PAUSE LOGIC ---
            if paused:
                # Sleep briefly to save CPU while waiting for user
                time.sleep(0.1) 
                continue

            # --- MAIN LOOP (Only runs when not paused) ---
            
            # 1. CAPTURE SCREEN
            try:
                screenshot = np.array(sct.grab(MONITOR))
            except Exception as e:
                print(f"\n[ERROR] Screen capture failed: {e}")
                print("Please check macOS Screen Recording permissions for Visual Studio Code.")
                print("System Settings > Privacy & Security > Screen & System Audio Recording")
                break

            # Drop Alpha channel (BGRA -> BGR)
            frame = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)

            # 2. VISION (YOLO)
            results = yolo_model.predict(frame, conf=YOLO_CONF, verbose=False)

            cuphead_pos = None
            projectiles = []

            for box in results[0].boxes:
                cls_id = int(box.cls[0])
                cls_name = yolo_model.names[cls_id]
                
                if cls_name == 'cuphead':
                    cuphead_pos = get_box_center(box)
                elif cls_name == 'projectile':
                    projectiles.append(get_box_center(box))

            # 3. PHYSICS EXTRACTION
            dist_x = 1280.0
            dist_y = 0.0
            
            if cuphead_pos and projectiles:
                # Find nearest projectile
                nearest = min(projectiles, key=lambda p: math.dist(p, cuphead_pos))
                dist_x = nearest[0] - cuphead_pos[0]
                dist_y = nearest[1] - cuphead_pos[1]

            # 4. VELOCITY CALCULATION
            # Safety: If we lost tracking (dist_x reset to 1280), assume 0 velocity 
            # to prevent a massive jump calculation.
            if dist_x == 1280.0 or prev_dist_x == 1280.0:
                velocity = 0.0
            else:
                velocity = dist_x - prev_dist_x
            
            prev_dist_x = dist_x

            # 5. NORMALIZE (Must match training data exactly)
            state_vector = np.array([[
                dist_x / 1280.0,
                dist_y / 720.0,
                velocity / 50.0
            ]])

            # 6. DECISION (MLP)
            jump_prob = mlp_model.predict(state_vector, verbose=0)[0][0]

            # 7. ACT
            if jump_prob > DECISION_THRESH:
                # Only print if we actually jump, to reduce console spam
                print(f"ACTION: JUMP (Prob: {jump_prob:.2f})")
                keyboard_controller.press(Key.space)
                time.sleep(0.04)
                keyboard_controller.release(Key.space)

            
            # (Optional) Uncomment to see what the bot sees. 
            # WARNING: This slows down the loop significantly.
            # cv2.imshow("Bot Vision", frame)
            # if cv2.waitKey(1) & 0xFF == ord('q'): break

        except KeyboardInterrupt:
            print("\nProgram interrupted.")
            break

if __name__ == "__main__":
    main()