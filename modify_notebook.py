
import json
import re

nb_path = '/System/Volumes/Data/Users/yeinkim/Desktop/CS156/Assignments/Assignment 3/Assignment_3.ipynb'
with open(nb_path, 'r') as f:
    nb = json.load(f)

# --- Modification 1: Align Pipeline Definitions in Section 3.2 (Cell 1) ---
# Previous: A=Implicit, B=Explicit. New: A=Explicit(YOLO), B=Implicit(AE)
cell1_source = "".join(nb['cells'][1]['source'])
cell1_source = cell1_source.replace("#### **Pipeline A: The Baseline (Implicit Perception)**", "#### **Pipeline B: The Baseline (Implicit Perception)**")
cell1_source = cell1_source.replace("#### **Pipeline B: The Novel Approach (Explicit Perception via YOLO)**", "#### **Pipeline A: The Novel Approach (Explicit Perception via YOLO)**")
# Note: The descriptions below the headers are already correct for the *new* headers (the text describes the method), 
# but we need to check if the specific bullet points or text bind them to A or B incorrectly.
# The original text:
# Pipeline A... Vision: Autoencoder... Rationale: "End-to-End"...
# Pipeline B... Vision: YOLO... Rationale: "Novel"...
#
# If I just swap the headers, the content follows:
# New "Pipeline B": Vision: Autoencoder... (Correct, B is AE in Section 5)
# New "Pipeline A": Vision: YOLO... (Correct, A is YOLO in Section 4)
# So simple header swap is sufficient if the order in text doesn't matter. 
# Better to physically swap the blocks so A comes before B in the text too?
# The list is order dependent? "two distinct pipelines to compete against each other:"
# It usually makes sense to list A then B.
# Let's rebuild the string to actuall swap the blocks.

# Locate the blocks
block_a_start = cell1_source.find("#### **Pipeline A: The Baseline")
block_b_start = cell1_source.find("#### **Pipeline B: The Novel Approach")
# Assuming B follows A
if block_a_start != -1 and block_b_start != -1:
    opening = cell1_source[:block_a_start]
    block_a = cell1_source[block_a_start:block_b_start]
    block_b = cell1_source[block_b_start:]
    
    # Modify headers within blocks
    new_block_a = block_b.replace("Pipeline B", "Pipeline A")
    new_block_b = block_a.replace("Pipeline A", "Pipeline B")
    
    nb['cells'][1]['source'] = [opening + new_block_a + "\n\n" + new_block_b]
else:
    print("Warning: Could not find Pipeline definitions in Cell 1 to swap.")

# --- Modification 2: Explicit Figure Labels (Cell 5) ---
# Annotations -> Figure 1, EDA -> Figure 2
cell5_source = "".join(nb['cells'][5]['source'])
cell5_source = cell5_source.replace("*Figure 1: Roboflow annotation*", "*Figure 1: Roboflow annotation*") # Already has Fig 1
# Check EDA image caption/ref
if "EDA_jump.png" in cell5_source and "Figure 2" not in cell5_source:
   # It seems EDA_jump.png is in Cell 5... wait, looking at my grep, Cell 5 has "Figure 1". 
   # Cell 8 (in my previous grep it wsa Cell 8? No, grep said Cell 5 has EDA_jump.png). 
   # Actually wait, `run_command` output for Cell 5 showed `EDA_jump.png` in attachments but check source text.
   # Ah, let's look at the actual source from the earlier tool output.
   # ... `![EDA_jump.png](attachment:EDA_jump.png)` ... `Class Weighting` ...
   # It effectively doesn't have a caption. Let's add one.
   cell5_source = cell5_source.replace("![EDA_jump.png](attachment:EDA_jump.png)", "![EDA_jump.png](attachment:EDA_jump.png)\n\n*Figure 2: Jump Class Imbalance Distribution.*")
    
nb['cells'][5]['source'] = [cell5_source]


# --- Modification 3: Renumbering Figures 3-4 (Cell 9) ---
# BoxF1 -> Fig 3, Consufion Matrix -> Fig 4
cell9_source = "".join(nb['cells'][9]['source'])
cell9_source = cell9_source.replace("Figure 1", "Figure 3") # The text says "Figure 1... (Left) and (Right)" maybe?
# Check previous content: "Figure 1 displays the Training Loss..." no wait, that was cell 13 in the grep.
# Cell 9 likely refers to F1 curve.
# If there are multiple simple replacements, just do them.
cell9_source = re.sub(r'Figure 1', 'Figure 3', cell9_source)
cell9_source = re.sub(r'Figure 2', 'Figure 4', cell9_source)
nb['cells'][9]['source'] = [cell9_source]


# --- Modification 4: Renumbering Figures 5-7 (Cell 10) ---
# Heatmap -> Fig 5, Conf Mat -> Fig 6, Opt Curve -> Fig 7
cell10_source = "".join(nb['cells'][10]['source'])
# Current refs might be mixed "Figure 3", "Figure 5" etc.
# Need to be map specific context.
# "Figure 3" (Decision Boundary) -> Figure 5
cell10_source = cell10_source.replace("Figure 3", "Figure 5")
# "Figure 4" (Confusion Matrix) -> Figure 6
cell10_source = cell10_source.replace("Figure 4", "Figure 6")
# "Figure 5" (Optimization Curve) -> Figure 7
cell10_source = cell10_source.replace("Figure 5", "Figure 7")

nb['cells'][10]['source'] = [cell10_source]


# --- Modification 5: Renumbering Figures 8-9 (Cell 13) ---
# AE Recon -> Fig 8, Threshold -> Fig 9
cell13_source = "".join(nb['cells'][13]['source'])
# Old: Figure 1 (Recon), Figure 2 (Threshold)
cell13_source = cell13_source.replace("Figure 1", "Figure 8")
cell13_source = cell13_source.replace("Figure 2", "Figure 9")
nb['cells'][13]['source'] = [cell13_source]


# --- Modification 6: Renumbering Figures 10-12 (Cell 14) ---
# MLP Train -> Fig 10, Session 9 -> Fig 11, AE Train -> Fig 12
cell14_source = "".join(nb['cells'][14]['source'])
# Old: Figure 5 (MLP timeline), Figure X (AE timeline?)
# Let's Replace explicit filenames with captions if missing or update refs.
# "Figure 5" (MLP Train Timeline) -> "Figure 10"
cell14_source = cell14_source.replace("Figure 5", "Figure 10")
# "Figure X" (AE Timeline) -> "Figure 12"
cell14_source = cell14_source.replace("Figure X", "Figure 12")

# Add/Fix captions
if "*Figure 10:" not in cell14_source:
    cell14_source = cell14_source.replace("![MLP train timeline.png]", "![MLP train timeline.png]\n*Figure 10: Pipeline A Training Timeline (Session 10).*")
    
if "*Figure 11:" not in cell14_source:
     cell14_source = cell14_source.replace("![session9-timeline-MLP.png](attachment:session9-timeline-MLP.png)", "![session9-timeline-MLP.png](attachment:session9-timeline-MLP.png)\n*Figure 11: Pipeline A Robustness in Session 9.*")

if "*Figure 12:" not in cell14_source:
     cell14_source = cell14_source.replace("![Training Set Timeline.png]", "![Training Set Timeline.png]\n*Figure 12: Pipeline B Training Timeline (Session 10).*")

nb['cells'][14]['source'] = [cell14_source]


# --- Modification 7: Renumbering Figures 13-14 (Cell 15) ---
# MLP Test -> Fig 13, GRU Test -> Fig 14
cell15_source = "".join(nb['cells'][15]['source'])
# Old: Figure 6, Figure 7
cell15_source = cell15_source.replace("Figure 6", "Figure 13")
cell15_source = cell15_source.replace("Figure 7", "Figure 14")
nb['cells'][15]['source'] = [cell15_source]


with open(nb_path, 'w') as f:
    json.dump(nb, f, indent=1)

print("Modification complete.")
