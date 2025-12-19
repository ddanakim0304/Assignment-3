import os
# Suppress TensorFlow logs
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import cv2
import numpy as np
import mss
import tensorflow as tf
import time
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
# Use the exact same capture region as your working script
MONITOR = {'top': 299, 'left': 1, 'width': 719, 'height': 399}

# Image Processing Config (Must match training!)
IMG_WIDTH = 128
IMG_HEIGHT = 72
SEQUENCE_LENGTH = 10 # T=10 frames context

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENCODER_PATH = os.path.join(BASE_DIR, "models", "potato_encoder.keras")
GRU_PATH = os.path.join(BASE_DIR, "models", "potato_gru.keras")

# Thresholds
# Pipeline B (GRU) usually requires a lower threshold than MLP
DECISION_THRESH = 0.36 

# --- LOAD MODELS ---
print("Loading Models... Please wait.")

# Load Encoder
# We use compile=False because we only need inference, not training/loss calculation
encoder_model = tf.keras.models.load_model(ENCODER_PATH, compile=False)

# Load GRU
# If you used custom Focal Loss, compile=False prevents loading errors
gru_model = tf.keras.models.load_model(GRU_PATH, compile=False)

print("\n" + "="*40)
print(" CUPHEAD AUTOPILOT READY (PIPELINE B: AE+GRU)")
print("="*40)
print(" controls:")
print("  [P] -> PAUSE / RESUME (Toggle)")
print("  [Q] -> QUIT Bot")
print("  [1] -> Log LOST & Pause")
print("  [2] -> Log WON & Pause")
print("="*40)

def preprocess_frame(sct_img):
    """
    Converts screen capture to the format expected by the Autoencoder.
    1. Drop Alpha (BGRA -> BGR)
    2. Resize to 128x72
    3. Grayscale
    4. Normalize (0.0 to 1.0)
    5. Expand dims for batch
    """
    frame = np.array(sct_img)
    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
    frame = cv2.resize(frame, (IMG_WIDTH, IMG_HEIGHT))
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    frame = frame.astype('float32') / 255.0
    # Shape becomes (1, 72, 128, 1)
    frame = np.expand_dims(frame, axis=-1)
    frame = np.expand_dims(frame, axis=0)
    return frame

def main():
    # Sequence Buffer (Holds the last 10 latent vectors)
    sequence_buffer = []
    
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
                    with open("gru_segments.txt", "a") as f:
                        f.write(f"{duration:.2f},LOST\n")
                    current_run_start_time = None

                with open("game_log.txt", "a") as f:
                    f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - LOST (GRU) - Survived: {duration:.2f}s\n")
                print(f"Survived: {duration:.2f}s")
                paused = True
                time.sleep(0.3)

            if key_monitor.is_pressed('2'):
                print("\n[RESULT] Logged: WON. Pausing bot...")
                duration = 0
                if current_run_start_time is not None:
                    duration = time.time() - current_run_start_time
                    with open("gru_segments.txt", "a") as f:
                        f.write(f"{current_run_start_time},{time.time()},WON\n")
                    current_run_start_time = None

                with open("game_log.txt", "a") as f:
                    f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - WON (GRU) - Survived: {duration:.2f}s\n")
                print(f"Survived: {duration:.2f}s")
                paused = True
                time.sleep(0.3)

            if key_monitor.is_pressed('p'):
                paused = not paused
                if paused:
                    print("\n[PAUSED] Bot sleeping...")
                else:
                    print("\n[RESUMED] Bot active! Filling sequence buffer...")
                    # RESET LOGIC: Clear buffer so we don't mix old game state with new
                    sequence_buffer = [] 
                    current_run_start_time = time.time()
                
                time.sleep(0.1)

            # --- PAUSE LOGIC ---
            if paused:
                time.sleep(0.1) 
                continue

            # --- MAIN LOOP ---
            
            # 1. CAPTURE SCREEN
            try:
                screenshot = sct.grab(MONITOR)
            except Exception as e:
                print(f"\n[ERROR] Screen capture failed: {e}")
                break

            # 2. PREPROCESS & ENCODE (Vision)
            # Process raw pixels
            input_frame = preprocess_frame(screenshot)
            
            # Get Latent Vector (z) -> Shape (1, 512)
            # Use functional call for speed instead of .predict()
            latent_vector = encoder_model(input_frame, training=False)
            
            # 3. SEQUENCE MANAGEMENT (Memory)
            # Add to buffer
            sequence_buffer.append(latent_vector)
            
            # Keep only the last 10 frames
            if len(sequence_buffer) > SEQUENCE_LENGTH:
                sequence_buffer.pop(0)

            # 4. DECISION (GRU)
            # We can only predict if we have enough history (10 frames)
            if len(sequence_buffer) == SEQUENCE_LENGTH:
                # Stack to create shape (1, 10, 512)
                # Note: latent_vector is (1, 512), so we stack on axis 1
                seq_input = tf.concat([tf.expand_dims(z, axis=1) for z in sequence_buffer], axis=1)
                
                # Predict
                jump_prob = gru_model(seq_input, training=False)[0][0]

                # 5. ACT
                if jump_prob > DECISION_THRESH:
                    print(f"ACTION: JUMP (Prob: {float(jump_prob):.2f})")
                    keyboard_controller.press(Key.space)
                    time.sleep(0.04)
                    keyboard_controller.release(Key.space)

        except KeyboardInterrupt:
            print("\nProgram interrupted.")
            break

if __name__ == "__main__":
    main()