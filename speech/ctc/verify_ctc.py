"""
CTC Forward Algorithm - Verification Script
Outputs exact values for the markdown tables
"""

import numpy as np

np.random.seed(42)

# ===== PARAMETERS =====
target_Y = list("na group")
vocab = ["n", "a", " ", "g", "r", "o", "u", "p", "blank"]
vocab_to_idx = {c: i for i, c in enumerate(vocab)}
T = 12

# Extended sequence Z
Z = []
for char in target_Y:
    Z.append("blank")
    Z.append(char)
Z.append("blank")
S = len(Z)

print("Target Y: na group")
print("Extended Z:", Z)
print("S = {} states, T = {} timesteps".format(S, T))
print()


# ===== GENERATE PROBABILITY MATRIX =====
def generate_probs():
    probs = np.zeros((len(vocab), T))
    char_schedule = [
        (0, "n", 0.7),
        (1, "n", 0.5),
        (2, "a", 0.6),
        (3, "blank", 0.5),
        (4, " ", 0.65),
        (5, "g", 0.7),
        (6, "r", 0.6),
        (7, "o", 0.55),
        (8, "blank", 0.45),
        (9, "u", 0.6),
        (10, "p", 0.7),
        (11, "blank", 0.5),
    ]

    for t, char, main_prob in char_schedule:
        char_idx = vocab_to_idx[char]
        probs[char_idx, t] = main_prob
        remaining = 1.0 - main_prob
        noise = np.random.dirichlet(np.ones(len(vocab) - 1)) * remaining
        noise_idx = 0
        for i in range(len(vocab)):
            if i != char_idx:
                probs[i, t] = noise[noise_idx]
                noise_idx += 1

    probs = probs / probs.sum(axis=0, keepdims=True)
    return probs


probs = generate_probs()

# Print probability matrix as LaTeX
print("=" * 80)
print("PROBABILITY MATRIX (for LaTeX)")
print("=" * 80)
vocab_display = ["n", "a", "space", "g", "r", "o", "u", "p", "eps"]
for i, char in enumerate(vocab_display):
    vals = " & ".join(["{:.3f}".format(probs[i, t]) for t in range(T)])
    print("{} & {} \\\\".format(char, vals))
print()


# ===== FORWARD ALGORITHM =====
def forward_algorithm(probs, Z, vocab_to_idx):
    S = len(Z)
    T = probs.shape[1]
    alpha = np.zeros((S, T))

    alpha[0, 0] = probs[vocab_to_idx[Z[0]], 0]
    alpha[1, 0] = probs[vocab_to_idx[Z[1]], 0]

    for t in range(1, T):
        for s in range(S):
            z_s = Z[s]
            z_s_idx = vocab_to_idx[z_s]

            if s == 0:
                alpha[s, t] = alpha[s, t - 1] * probs[z_s_idx, t]
            elif s == 1:
                alpha[s, t] = (alpha[s - 1, t - 1] + alpha[s, t - 1]) * probs[
                    z_s_idx, t
                ]
            else:
                if z_s == "blank" or (s >= 2 and Z[s] == Z[s - 2]):
                    alpha[s, t] = (alpha[s - 1, t - 1] + alpha[s, t - 1]) * probs[
                        z_s_idx, t
                    ]
                else:
                    alpha[s, t] = (
                        alpha[s - 2, t - 1] + alpha[s - 1, t - 1] + alpha[s, t - 1]
                    ) * probs[z_s_idx, t]

    return alpha


alpha = forward_algorithm(probs, Z, vocab_to_idx)

# Print full alpha table for LaTeX
print("=" * 80)
print("FULL ALPHA TABLE (for LaTeX)")
print("=" * 80)
print()

Z_display = []
for z in Z:
    if z == "blank":
        Z_display.append("eps")
    elif z == " ":
        Z_display.append("sp")
    else:
        Z_display.append(z)

for s in range(S):
    vals = " & ".join(
        ["{:.4f}".format(alpha[s, t]) if alpha[s, t] > 1e-10 else "0" for t in range(T)]
    )
    print("{} & {} & {} \\\\".format(s + 1, Z_display[s], vals))

# Final result
P_Y_given_X = alpha[S - 2, T - 1] + alpha[S - 1, T - 1]
print()
print("=" * 80)
print("FINAL RESULT")
print("=" * 80)
print("alpha(16, 12) = {:.10f}".format(alpha[S - 2, T - 1]))
print("alpha(17, 12) = {:.10f}".format(alpha[S - 1, T - 1]))
print("P(Y|X) = {:.10f}".format(P_Y_given_X))
print("CTC Loss = {:.6f}".format(-np.log(P_Y_given_X)))

# Check greedy
print()
print("=" * 80)
print("GREEDY DECODING")
print("=" * 80)
greedy_path = np.argmax(probs, axis=0)
greedy_chars = [vocab[i] for i in greedy_path]
print("Argmax indices:", list(greedy_path))
print("Argmax chars:", greedy_chars)
collapsed = []
prev = None
for c in greedy_chars:
    if c != "blank" and c != prev:
        collapsed.append(c)
    prev = c
print("Collapsed: {}".format("".join(collapsed)))
