"""
CTC Forward Algorithm - Complete Numerical Example
Target: "na group"
This script computes all alpha values and generates LaTeX tables and visualizations.
"""

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Set random seed for reproducibility
np.random.seed(42)

# ===== PARAMETERS =====
target_Y = list("na group")  # ['n', 'a', ' ', 'g', 'r', 'o', 'u', 'p']
vocab = ["n", "a", " ", "g", "r", "o", "u", "p", "ε"]  # 9 classes (8 chars + blank)
vocab_to_idx = {c: i for i, c in enumerate(vocab)}
T = 12  # Number of timesteps

# Extended sequence Z: insert ε between each character and at boundaries
# Y = [n, a, ␣, g, r, o, u, p]
# Z = [ε, n, ε, a, ε, ␣, ε, g, ε, r, ε, o, ε, u, ε, p, ε]
Z = []
for char in target_Y:
    Z.append("ε")
    Z.append(char)
Z.append("ε")
S = len(Z)  # 17 states

print(f"Target Y: {''.join(target_Y)}")
print(f"Extended Z ({S} states): {Z}")
print(f"Timesteps T: {T}")
print(f"Vocabulary: {vocab}")
print()

# ===== GENERATE PROBABILITY MATRIX =====
# Create a realistic probability matrix where the correct sequence has higher probability
# Matrix shape: (vocab_size, T) = (9, 12)


def generate_probs():
    """Generate a realistic probability matrix for 'na group' recognition."""
    probs = np.zeros((len(vocab), T))

    # Define which character should be most probable at each timestep
    # Mapping timesteps to expected characters with some blank in between
    char_schedule = [
        (0, "n", 0.7),  # t=1: 'n'
        (1, "n", 0.5),  # t=2: still 'n' or blank
        (2, "a", 0.6),  # t=3: 'a'
        (3, "ε", 0.5),  # t=4: blank (transition)
        (4, " ", 0.65),  # t=5: space
        (5, "g", 0.7),  # t=6: 'g'
        (6, "r", 0.6),  # t=7: 'r'
        (7, "o", 0.55),  # t=8: 'o'
        (8, "ε", 0.45),  # t=9: blank
        (9, "u", 0.6),  # t=10: 'u'
        (10, "p", 0.7),  # t=11: 'p'
        (11, "ε", 0.5),  # t=12: blank (end)
    ]

    for t, char, main_prob in char_schedule:
        # Set main character probability
        char_idx = vocab_to_idx[char]
        probs[char_idx, t] = main_prob

        # Distribute remaining probability
        remaining = 1.0 - main_prob
        noise = np.random.dirichlet(np.ones(len(vocab) - 1)) * remaining
        noise_idx = 0
        for i in range(len(vocab)):
            if i != char_idx:
                probs[i, t] = noise[noise_idx]
                noise_idx += 1

    # Normalize columns to sum to 1
    probs = probs / probs.sum(axis=0, keepdims=True)
    return probs


probs = generate_probs()

print("=" * 60)
print("RNN OUTPUT PROBABILITY MATRIX P(class | timestep)")
print("=" * 60)
print(f"Shape: {probs.shape} (9 classes x 12 timesteps)")
print()

# Print probability matrix
header = "Char   | " + " | ".join([f"t={t + 1:2d}" for t in range(T)])
print(header)
print("-" * len(header))
for i, char in enumerate(vocab):
    char_display = "␣" if char == " " else char
    row = f"  {char_display}    | " + " | ".join(
        [f"{probs[i, t]:.3f}" for t in range(T)]
    )
    print(row)
print()


# ===== FORWARD ALGORITHM =====
def forward_algorithm(probs, Z, vocab_to_idx):
    """
    Compute the forward (alpha) probabilities for CTC.

    Args:
        probs: (vocab_size, T) probability matrix
        Z: Extended sequence with blanks
        vocab_to_idx: Mapping from character to index

    Returns:
        alpha: (S, T) forward probabilities
    """
    S = len(Z)
    T = probs.shape[1]
    alpha = np.zeros((S, T))

    # Initialization at t=0 (using 0-indexing, so t=0 is first timestep)
    # Only first two states can be initialized
    z0_idx = vocab_to_idx[Z[0]]  # ε
    z1_idx = vocab_to_idx[Z[1]]  # n
    alpha[0, 0] = probs[z0_idx, 0]
    alpha[1, 0] = probs[z1_idx, 0]

    # Recurrence for t = 1 to T-1
    for t in range(1, T):
        for s in range(S):
            z_s = Z[s]
            z_s_idx = vocab_to_idx[z_s]

            # Determine which case applies
            if s == 0:
                # First state: can only come from itself
                alpha[s, t] = alpha[s, t - 1] * probs[z_s_idx, t]
            elif s == 1:
                # Second state: can come from s=0 or s=1
                alpha[s, t] = (alpha[s - 1, t - 1] + alpha[s, t - 1]) * probs[
                    z_s_idx, t
                ]
            else:
                # General case: check if we can skip s-1
                # Case 1: Cannot skip if z_s is blank OR z_s == z_{s-2}
                # Case 2: Can skip if z_{s-1} is blank between unique characters

                if z_s == "ε" or (s >= 2 and Z[s] == Z[s - 2]):
                    # Case 1: Cannot skip z_{s-1}
                    alpha[s, t] = (alpha[s - 1, t - 1] + alpha[s, t - 1]) * probs[
                        z_s_idx, t
                    ]
                else:
                    # Case 2: Can skip z_{s-1} (which is ε between unique chars)
                    alpha[s, t] = (
                        alpha[s - 2, t - 1] + alpha[s - 1, t - 1] + alpha[s, t - 1]
                    ) * probs[z_s_idx, t]

    return alpha


alpha = forward_algorithm(probs, Z, vocab_to_idx)

print("=" * 60)
print("FORWARD ALGORITHM ALPHA VALUES")
print("=" * 60)
print(f"Alpha matrix shape: {alpha.shape} ({S} states x {T} timesteps)")
print()

# Print alpha values for each timestep
for t in range(T):
    print(f"\n--- TIMESTEP t = {t + 1} ---")
    print(f"{'State s':<10} | {'z_s':<5} | {'α(s,t)':<12}")
    print("-" * 35)
    for s in range(S):
        z_display = "␣" if Z[s] == " " else Z[s]
        print(f"    {s + 1:<6} | {z_display:<5} | {alpha[s, t]:.8f}")

# Final probability
P_Y_given_X = alpha[S - 2, T - 1] + alpha[S - 1, T - 1]  # Second-to-last or last state
print("\n" + "=" * 60)
print("FINAL CTC PROBABILITY")
print("=" * 60)
print(f"P(Y|X) = α({S - 1}, {T}) + α({S}, {T})")
print(f"       = α(state 16, t=12) + α(state 17, t=12)")
print(f"       = {alpha[S - 2, T - 1]:.10f} + {alpha[S - 1, T - 1]:.10f}")
print(f"       = {P_Y_given_X:.10f}")
print(f"\nCTC Loss = -log(P(Y|X)) = {-np.log(P_Y_given_X):.6f}")

# ===== GENERATE LATEX TABLES =====
print("\n" + "=" * 60)
print("LATEX ALPHA TABLES")
print("=" * 60)


def generate_latex_table(alpha, Z, t, show_all_t=False):
    """Generate LaTeX code for alpha table at timestep t."""
    S = len(Z)

    if show_all_t:
        # Show cumulative table up to timestep t
        cols = "c|c|" + "c" * (t + 1)
        header = (
            "s & z_s & "
            + " & ".join([f"\\alpha_{{s,{i + 1}}}" for i in range(t + 1)])
            + " \\\\\n"
        )
    else:
        # Show only single timestep
        cols = "c|c|c"
        header = f"s & z_s & \\alpha_{{s,{t + 1}}} \\\\\n"

    latex = f"\\begin{{array}}{{{cols}}}\n"
    latex += "\\hline\n"
    latex += header
    latex += "\\hline\n"

    for s in range(S):
        z_display = (
            "\\text{␣}" if Z[s] == " " else ("\\epsilon" if Z[s] == "ε" else Z[s])
        )

        if show_all_t:
            vals = " & ".join(
                [
                    f"{alpha[s, i]:.4f}" if alpha[s, i] > 1e-10 else "0"
                    for i in range(t + 1)
                ]
            )
            latex += f"{s + 1} & {z_display} & {vals} \\\\\n"
        else:
            val = f"{alpha[s, t]:.6f}" if alpha[s, t] > 1e-10 else "0"
            latex += f"{s + 1} & {z_display} & {val} \\\\\n"

    latex += "\\hline\n"
    latex += "\\end{array}"

    return latex


# Generate table for t=1
print("\nTable at t=1:")
print(generate_latex_table(alpha, Z, 0))

# Generate cumulative table at final timestep
print("\n\nFull cumulative table (all timesteps):")
print(generate_latex_table(alpha, Z, T - 1, show_all_t=True))

# ===== VISUALIZATIONS =====
print("\n" + "=" * 60)
print("GENERATING VISUALIZATIONS...")
print("=" * 60)

# Set style
plt.style.use("seaborn-v0_8-whitegrid")

# 1. Probability Matrix Heatmap
fig, ax = plt.subplots(figsize=(14, 6))
vocab_display = ["n", "a", "␣", "g", "r", "o", "u", "p", "ε"]
sns.heatmap(
    probs,
    annot=True,
    fmt=".3f",
    cmap="Blues",
    xticklabels=[f"t={i + 1}" for i in range(T)],
    yticklabels=vocab_display,
    ax=ax,
    cbar_kws={"label": "Probability"},
)
ax.set_xlabel("Timestep", fontsize=12)
ax.set_ylabel("Character", fontsize=12)
ax.set_title(
    "RNN Output Probabilities P(character | timestep)", fontsize=14, fontweight="bold"
)
plt.tight_layout()
plt.savefig(
    "ctc_probability_matrix.png", dpi=150, bbox_inches="tight", facecolor="white"
)
print("Saved: ctc_probability_matrix.png")

# 2. Alpha Trellis Heatmap
fig, ax = plt.subplots(figsize=(14, 10))
Z_display = ["ε" if z == "ε" else ("␣" if z == " " else z) for z in Z]
state_labels = [f"s={i + 1}: {Z_display[i]}" for i in range(S)]

# Use log scale for better visualization (add small epsilon to avoid log(0))
alpha_log = np.log10(alpha + 1e-15)
alpha_log[alpha < 1e-15] = np.nan  # Set zeros to NaN for clear display

sns.heatmap(
    alpha,
    annot=True,
    fmt=".4f",
    cmap="Greens",
    xticklabels=[f"t={i + 1}" for i in range(T)],
    yticklabels=state_labels,
    ax=ax,
    cbar_kws={"label": "α value"},
)
ax.set_xlabel("Timestep", fontsize=12)
ax.set_ylabel("State (s: character)", fontsize=12)
ax.set_title("Forward Algorithm α(s,t) Values", fontsize=14, fontweight="bold")
plt.tight_layout()
plt.savefig("ctc_alpha_trellis.png", dpi=150, bbox_inches="tight", facecolor="white")
print("Saved: ctc_alpha_trellis.png")

# 3. Greedy Decoding Path
fig, ax = plt.subplots(figsize=(14, 6))
greedy_path = np.argmax(probs, axis=0)
greedy_chars = [vocab[i] for i in greedy_path]
greedy_display = ["ε" if c == "ε" else ("␣" if c == " " else c) for c in greedy_chars]

ax.bar(range(T), [1] * T, color="lightblue", edgecolor="navy", linewidth=2)
for t in range(T):
    ax.text(
        t,
        0.5,
        greedy_display[t],
        ha="center",
        va="center",
        fontsize=16,
        fontweight="bold",
    )
    ax.text(
        t,
        0.1,
        f"p={probs[greedy_path[t], t]:.3f}",
        ha="center",
        va="center",
        fontsize=10,
    )

ax.set_xlim(-0.5, T - 0.5)
ax.set_ylim(0, 1)
ax.set_xticks(range(T))
ax.set_xticklabels([f"t={i + 1}" for i in range(T)])
ax.set_yticks([])
ax.set_xlabel("Timestep", fontsize=12)
ax.set_title(
    "Greedy Decoding: Most Likely Character at Each Timestep",
    fontsize=14,
    fontweight="bold",
)

# Show collapsed output
collapsed = []
prev = None
for c in greedy_chars:
    if c != "ε" and c != prev:
        collapsed.append(c)
    prev = c
ax.text(
    T / 2,
    -0.15,
    f'Collapsed Output: "{"".join(collapsed)}"',
    ha="center",
    fontsize=14,
    fontweight="bold",
    transform=ax.get_xaxis_transform(),
)

plt.tight_layout()
plt.savefig("ctc_greedy_decoding.png", dpi=150, bbox_inches="tight", facecolor="white")
print("Saved: ctc_greedy_decoding.png")

plt.close("all")
print("\nAll visualizations generated successfully!")

# ===== OUTPUT SUMMARY FOR MARKDOWN =====
print("\n" + "=" * 60)
print("SUMMARY FOR MARKDOWN")
print("=" * 60)
print(f"""
Target: Y = "na group"
Extended: Z = {Z}
Timesteps: T = {T}
States: S = {S}

Final Result:
  P(Y|X) = {P_Y_given_X:.10f}
  CTC Loss = -log(P(Y|X)) = {-np.log(P_Y_given_X):.6f}
""")
