
import json
import re

nb_path = '/System/Volumes/Data/Users/yeinkim/Desktop/CS156/Assignments/Assignment 3/Assignment_3.ipynb'
try:
    with open(nb_path, 'r') as f:
        nb = json.load(f)
        
    print("Read notebook successfully.")
    
    # Check Cell 1
    c1 = "".join(nb['cells'][1]['source'])
    print(f"Cell 1 length: {len(c1)}")
    if "Pipeline A" in c1:
        print("Cell 1 contains 'Pipeline A'")
        print(c1[c1.find("Pipeline A"):c1.find("Pipeline A")+100])
    
    # Check Cell 5
    c5 = "".join(nb['cells'][5]['source'])
    print(f"Cell 5 content snippet: {c5[:200]}")
    if "Figure" in c5:
        print("Cell 5 has Figure references.")
    else:
        print("Cell 5 looks unmodified regarding Figures.")

    # Check Cell 9
    c9 = "".join(nb['cells'][9]['source'])
    if "Figure 3" in c9:
        print("Cell 9 has Figure 3 (Correct).")
    elif "Figure 1" in c9:
        print("Cell 9 still has Figure 1 (Incorrect).")

except Exception as e:
    print(f"Error reading notebook: {e}")
