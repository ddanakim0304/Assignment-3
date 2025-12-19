import cv2
import json
import os
import random

ASSIGNMENT_2_DIR = os.path.join("..", "Assignment 2", "data", "sessions")
VIDEO_PATH = os.path.join(ASSIGNMENT_2_DIR, "Train.mp4")
SEGMENTS_FILE = "potato_phase_segments.json"
OUTPUT_DIR = "datasets/raw_images"

NUM_FRAMES_TO_EXTRACT = 60  # Extract 60 frames total for labeling

def main():
    if not os.path.exists(SEGMENTS_FILE):
        print("Error: potato_phase_segments.json not found!")
        return

    # 1. Load Segments
    with open(SEGMENTS_FILE, 'r') as f:
        data = json.load(f)
        segments = data['segments']

    # 2. Collect all valid frame indices
    valid_indices = []
    for seg in segments:
        # Add frames from start to end of each segment
        valid_indices.extend(range(seg['start_frame'], seg['end_frame']))
    
    print(f"Found {len(valid_indices)} frames belonging to Potato Phase.")

    # 3. Randomly sample frames
    selected_indices = sorted(random.sample(valid_indices, min(len(valid_indices), NUM_FRAMES_TO_EXTRACT)))
    print(f"Selected {len(selected_indices)} frames to extract.")

    # 4. Extract Images
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    cap = cv2.VideoCapture(VIDEO_PATH)
    
    saved_count = 0
    for idx in selected_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if ret:
            # Save as jpg
            filename = os.path.join(OUTPUT_DIR, f"frame_{idx}.jpg")
            cv2.imwrite(filename, frame)
            saved_count += 1
            print(f"Saved {filename}", end='\r')
    
    cap.release()
    print(f"\n\nDone! Saved {saved_count} images to '{OUTPUT_DIR}'")
    print("NEXT STEP: Upload these images to Roboflow or CVAT for labeling.")

if __name__ == "__main__":
    main()