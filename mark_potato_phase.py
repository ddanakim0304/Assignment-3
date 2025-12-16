import cv2
import json
import os
import sys

# --- Configuration ---
ASSIGNMENT_2_DIR = os.path.join("..", "Assignment 2", "data", "sessions")
VIDEO_PATH = os.path.join(ASSIGNMENT_2_DIR, "Train.mp4")
FRAMES_LOG_PATH = os.path.join(ASSIGNMENT_2_DIR, "Train_frames.jsonl")
OUTPUT_FILE = "potato_phase_segments.json"

def load_utc_map(log_path):
    """Loads timestamps."""
    print(f"Loading timestamps from {log_path}...")
    timestamps = []
    if os.path.exists(log_path):
        with open(log_path, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    timestamps.append(data.get('t'))
                except:
                    timestamps.append(None)
    return timestamps

def main():
    if not os.path.exists(VIDEO_PATH):
        print(f"Error: Video not found at {VIDEO_PATH}")
        sys.exit(1)

    utc_map = load_utc_map(FRAMES_LOG_PATH)
    cap = cv2.VideoCapture(VIDEO_PATH)
    base_fps = cap.get(cv2.CAP_PROP_FPS)
    if base_fps <= 0: base_fps = 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # State variables
    frame_idx = 0
    start_point = None # Stores {frame, utc}
    segments = []      # Stores list of completed segments
    
    paused = True
    speed_mult = 1.0
    need_seek = False

    print("\n" + "="*50)
    print(" MULTI-SESSION TAGGER")
    print(" 1. Find start of Potato fight -> Press [ S ]")
    print(" 2. Find end of Potato fight   -> Press [ E ]")
    print("    (This saves the segment and lets you find the next one)")
    print(" 3. Repeat for all 15 sessions.")
    print(" 4. Press [ Q ] to finish and write to file.")
    print("="*50 + "\n")

    while True:
        # --- Video Logic ---
        if need_seek:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            need_seek = False
        
        if not paused:
            ret, frame = cap.read()
            if not ret:
                paused = True
                frame_idx = total_frames - 1
            else:
                frame_idx = int(cap.get(cv2.CAP_PROP_POS_FRAMES)) - 1
        else:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()

        if frame is None: break

        # --- UI Overlay ---
        display = frame.copy()
        curr_utc = utc_map[frame_idx] if frame_idx < len(utc_map) else "N/A"

        # Top Info Bar
        cv2.rectangle(display, (0, 0), (600, 120), (0, 0, 0), -1)
        
        # Status
        status_txt = "PAUSED" if paused else f"PLAYING {int(speed_mult)}x"
        cv2.putText(display, f"Status: {status_txt}", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.putText(display, f"Frame:  {frame_idx} / {total_frames}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        # Segment Info
        seg_count = len(segments)
        cv2.putText(display, f"Segments Captured: {seg_count}", (10, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # Current Marking Status
        if start_point:
            cv2.putText(display, f"IN PROGRESS: Started at {start_point['frame']}", (10, 105), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 100, 255), 2)
            # Visual indicator that we are recording
            cv2.circle(display, (550, 60), 15, (0, 0, 255), -1)
        else:
            cv2.putText(display, "Waiting for Start [S]...", (10, 105), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

        cv2.imshow("Potato Tagger", display)

        # --- Timing & Inputs ---
        if paused:
            delay = 0
        else:
            delay = int(1000 / (base_fps * speed_mult))
            if delay < 1: delay = 1
        
        key = cv2.waitKey(delay) & 0xFF

        # Speed (1-0)
        if ord('1') <= key <= ord('9'): speed_mult = float(key - ord('0'))
        elif key == ord('0'): speed_mult = 10.0
        
        # Pause
        elif key == ord(' '): paused = not paused

        # Quit
        elif key == ord('q'): break

        # Mark START
        elif key == ord('s'):
            start_point = {'frame': frame_idx, 'utc': curr_utc}
            print(f"[{seg_count+1}] Start marked at {frame_idx}")
            paused = False # Optional: Keep playing to find end

        # Mark END (Commit Segment)
        elif key == ord('e'):
            if start_point:
                if frame_idx > start_point['frame']:
                    new_seg = {
                        "id": seg_count + 1,
                        "start_frame": start_point['frame'],
                        "start_utc": start_point['utc'],
                        "end_frame": frame_idx,
                        "end_utc": curr_utc
                    }
                    segments.append(new_seg)
                    print(f"[{seg_count+1}] CAPTURED! ({start_point['frame']} -> {frame_idx})")
                    start_point = None # Reset for next session
                    paused = True # Pause to confirm
                else:
                    print("Error: End frame must be after Start frame.")
            else:
                print("Error: Press [S] to mark start first.")

        # Navigation (Arrows / J / L)
        elif key == 81 or key == 2 or key == ord('j'): # Left
            frame_idx = max(0, frame_idx - 1); need_seek = True; paused = True
        elif key == 83 or key == 3 or key == ord('l'): # Right
            frame_idx = min(total_frames - 1, frame_idx + 1); need_seek = True; paused = True
        elif key == ord('a'): # Fast Rewind
            frame_idx = max(0, frame_idx - 50); need_seek = True
        elif key == ord('d'): # Fast Forward
            frame_idx = min(total_frames - 1, frame_idx + 50); need_seek = True

    cap.release()
    cv2.destroyAllWindows()

    # Save to JSON
    if segments:
        data = {
            "source_video": "Train.mp4",
            "total_segments": len(segments),
            "segments": segments
        }
        with open(OUTPUT_FILE, "w") as f:
            json.dump(data, f, indent=4)
        print("\n" + "="*50)
        print(f"SAVED {len(segments)} SEGMENTS TO {OUTPUT_FILE}")
        print("="*50)
    else:
        print("Exited without saving any segments.")

if __name__ == "__main__":
    main()