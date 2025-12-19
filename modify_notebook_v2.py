
import json
import re

nb_path = '/System/Volumes/Data/Users/yeinkim/Desktop/CS156/Assignments/Assignment 3/Assignment_3.ipynb'
with open(nb_path, 'r') as f:
    nb = json.load(f)

# --- Fix Cell 1: Pipeline Definitions ---
c1 = "".join(nb['cells'][1]['source'])

# Define patterns for the blocks
# We are looking for "#### **Pipeline A:..."  up to "#### **Pipeline B:..."
# and then "#### **Pipeline B:..." to the end or next header.
# Since it's Markdown, splitting by header is easiest.

# Let's try to split by the specific headers.
parts = re.split(r'(#### \*\*Pipeline [AB]:.*)', c1)
# parts[0] = Intro text
# parts[1] = Header A (or B)
# parts[2] = Content A
# parts[3] = Header B (or A)
# parts[4] = Content B

if len(parts) >= 5:
    # Identify which is which
    # We want Explicit (YOLO) to be A, Implicit (AE) to be B.
    # Currently: A = Implicit, B = Explicit.
    
    # Let's reconstruct.
    # find implicit block and explicit block
    implicit_header = ""
    implicit_content = ""
    explicit_header = ""
    explicit_content = ""
    
    intro = parts[0]
    
    # Check parts 1 and 3
    if "Implicit" in parts[1]:
        implicit_header = parts[1]
        implicit_content = parts[2]
    elif "Explicit" in parts[1]:
        explicit_header = parts[1]
        explicit_content = parts[2]
        
    if "Implicit" in parts[3]:
        implicit_header = parts[3]
        implicit_content = parts[4]
    elif "Explicit" in parts[3]:
        explicit_header = parts[3]
        explicit_content = parts[4]
        
    # Now reconstruct with A=Explicit first, then B=Implicit
    # Rename headers
    new_explicit_header = explicit_header.replace("Pipeline B", "Pipeline A").replace("Pipeline A", "Pipeline A") # Ensure it says A
    if "Pipeline A" not in new_explicit_header: new_explicit_header = new_explicit_header.replace("Pipeline", "Pipeline A") # Fallback
    
    new_implicit_header = implicit_header.replace("Pipeline A", "Pipeline B").replace("Pipeline B", "Pipeline B") # Ensure it says B
    
    # Construct new source
    new_c1 = intro + new_explicit_header + explicit_content + new_implicit_header + implicit_content
    nb['cells'][1]['source'] = [new_c1]
    print("Swapped Pipeline definitions in Cell 1.")
else:
    print("Could not parse Cell 1 for swapping.")

# --- Verify/Fix other cells ---
# Cell 10 (Mlp Results)
c10 = r"""#### **3.4.2 MLP (Decision Model)**
The MLP decision model, trained on the state vector $S_t = [\Delta x, \Delta y, v_x]$, successfully learned a non-linear decision boundary for the "Jump" action.

![MLP Decision Boundary Heatmap](images/MLP%20Decision%20Boundary%20Heatmap.png)

*Figure 5: MLP Decision Boundary Heatmap*

Figure 5 visualizes the model's learned logic. The red region (High Jump Probability) corresponds to states where the projectile is both **close** (Distance < 200px) and **approaching fast** (high velocity has higher jump probability). The gradient transition from green (Idle) to red (Jump) demonstrates that the model is not acting randomly, but has approximated the underlying physics of a collision.

#### **Threshold Tuning (F-Beta Optimization)**
A standard classification threshold of $0.5$ proved suboptimal for real-time gameplay. While it captured most necessary jumps, it suffered from "panic jumping"—triggering actions when the projectile was safe, which destabilizes the agent. To refine this behavior, I implemented a dynamic threshold tuning algorithm based on the **F-Beta Score**.

**Rationale for F0.8:**
I specifically optimized for the **F0.8-score** (where $\beta=0.8$).
*   **The Problem:** An F1 score treats False Positives (jumping when unnecessary) and False Negatives (failing to jump) equally.
*   **The Solution:** By setting $\beta < 1$, the metric assigns more weight to **Precision**. This enforces a preference for high confidence to ensure stability, preventing the agent from spamming inputs, while maintaining enough sensitivity to react to fast-moving projectiles.

The optimization process yielded a significantly higher decision threshold of **0.784**.

#### **Analysis of Optimization Curve**
Figure 6 illustrates the relationship between the decision threshold and the F0.8 score.

![MLP Optimization Curve](images/MLP%20optimization%20curve.png)

*Figure 6: F0.8 Score Optimization Curve. The red dashed line indicates the optimal threshold.*

As the threshold increases, the model becomes more conservative. Usefully, the curve shows a distinct peak around 0.78.
*   **Low Threshold (< 0.5):** The model jumps too often (High Recall, Low Precision), leading to a lower F0.8 score.
*   **Optimal Threshold (0.784):** This sweet spot maximizes the F0.8 metric, balancing the need to jump for survival with the need to stay grounded for stability.
*   **High Threshold (> 0.85):** The model misses too many generic jumps, causing the score to drop rapidly.

#### **Performance Impact**
As shown in **Figure 7**, shifting the decision threshold from the standard 0.50 to **0.784** resulted in a stricter, more precise agent.

![MLP Confusion Matrix](images/MLP%20confusion%20matrix.png)

*Figure 7: Confusion Matrix comparison. Left: Default Threshold (0.5). Right: Optimized Threshold (0.784).*

The confusion matrices in Figure 7 confirm the improvement:
*   **False Positives (Purple box):** Reduced significantly. The agent stops jumping at "ghost" threats.
*   **False Negatives (Green box):** Remained stable. The agent did not lose the ability to dodge real threats.

This shift creates a "calm expert" behavior compared to the "anxious novice" behavior of the default threshold."""
nb['cells'][10]['source'] = [c10]

# Cell 14
c14 = "".join(nb['cells'][14]['source'])
if "Figure 5" in c14: 
    print("Fixing Cell 14 Figure 5 -> Figure 10")
    c14 = c14.replace("Figure 5", "Figure 10")
nb['cells'][14]['source'] = [c14]


with open(nb_path, 'w') as f:
    json.dump(nb, f, indent=1)
print("Saved notebook.")
