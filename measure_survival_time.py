import cv2
import json
import os
import sys

# --- Configuration ---
# Adjust this path if the filename is different
VIDEO_PATH = os.path.join("CupheadAI", "[CS156] Pipeline B final gameplay.mp4")
OUTPUT_FILE = "pipeline_b_survival.json"

def main():
    global VIDEO_PATH
    if not os.path.exists(VIDEO_PATH):
        print(f"Error: Video not found at {VIDEO_PATH}")
        # Fallback check for the other filename seen previously
        alt_path = os.path.join("CupheadAI", "[CS156] Pipeline B final gameplay.mp4")
        if os.path.exists(alt_path):
            print(f"Found video at alternative path: {alt_path}")
            VIDEO_PATH = alt_path
        else:
            sys.exit(1)

    cap = cv2.VideoCapture(VIDEO_PATH)
    base_fps = cap.get(cv2.CAP_PROP_FPS)
    if base_fps <= 0: base_fps = 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # State variables
    frame_idx = 0
    start_point = None # Stores {frame}
    segments = []      # Stores list of completed segments
    
    paused = True
    speed_mult = 1.0
    need_seek = False

    print("\n" + "="*50)
    print(" PIPELINE A SURVIVAL TAGGER")
    print(" 1. Find start of run -> Press [ S ]")
    print(" 2. Find end of run   -> Press [ E ]")
    print("    (This saves the segment and lets you find the next one)")
    print(" 3. Repeat for all sessions.")
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
        
        # Top Info Bar Background
        cv2.rectangle(display, (0, 0), (600, 130), (0, 0, 0), -1)
        
        # Status & Speed
        status_txt = "PAUSED" if paused else f"PLAYING {speed_mult:.1f}x"
        cv2.putText(display, f"Status: {status_txt}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        # Frame Info
        cv2.putText(display, f"Frame:  {frame_idx} / {total_frames}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        # Session Count
        seg_count = len(segments)
        cv2.putText(display, f"Sessions Captured: {seg_count}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # Recording Indicator
        if start_point:
            # Red text and circle for recording
            cv2.putText(display, f"RECORDING: Start {start_point['frame']}", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            cv2.circle(display, (550, 60), 20, (0, 0, 255), -1)
        else:
            cv2.putText(display, "Waiting for Start [S]...", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

        cv2.imshow("Pipeline A Tagger", display)

        # --- Timing & Inputs ---
        if paused:
            delay = 0
        else:
            delay = int(1000 / (base_fps * speed_mult))
            if delay < 1: delay = 1
        
        key = cv2.waitKey(delay) & 0xFF

        # Speed Controls (1-9 for 1x-9x, 0 for 10x)
        if ord('1') <= key <= ord('9'): 
            speed_mult = float(key - ord('0'))
        elif key == ord('0'): 
            speed_mult = 10.0
        
        # Pause
        elif key == ord(' '): 
            paused = not paused

        # Quit
        elif key == ord('q'): 
            break

        # Mark START
        elif key == ord('s'):
            start_point = {'frame': frame_idx}
            print(f"[{seg_count+1}] Start marked at {frame_idx}")
            paused = False # Auto-play to find end

        # Mark END (Commit Segment)
        elif key == ord('e'):
            if start_point:
                if frame_idx > start_point['frame']:
                    duration_sec = (frame_idx - start_point['frame']) / base_fps
                    new_seg = {
                        "id": seg_count + 1,
                        "start_frame": start_point['frame'],
                        "end_frame": frame_idx,
                        "duration_seconds": duration_sec
                    }
                    segments.append(new_seg)
                    print(f"[{seg_count+1}] CAPTURED! ({start_point['frame']} -> {frame_idx}) Duration: {duration_sec:.2f}s")
                    start_point = None # Reset
                    paused = True # Pause to confirm
                else:
                    print("Error: End frame must be after Start frame.")
            else:
                print("Error: Press [S] to mark start first.")

        # Navigation
        elif key == 81 or key == 2 or key == ord('j'): # Left Arrow / J
            frame_idx = max(0, frame_idx - 1); need_seek = True; paused = True
        elif key == 83 or key == 3 or key == ord('l'): # Right Arrow / L
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
            "source_video": VIDEO_PATH,
            "total_sessions": len(segments),
            "sessions": segments
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
