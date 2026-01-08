"""
CTC Forward Algorithm - Save results to file
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

# Save to file
with open("ctc_results.txt", "w") as f:
    f.write("CTC FORWARD ALGORITHM RESULTS\n")
    f.write("=" * 60 + "\n\n")

    f.write("PROBABILITY MATRIX (LaTeX format):\n")
    vocab_display = ["n", "a", "space", "g", "r", "o", "u", "p", "eps"]
    for i, char in enumerate(vocab_display):
        vals = " & ".join(["{:.3f}".format(probs[i, t]) for t in range(T)])
        f.write("{} & {} \\\\\n".format(char, vals))
    f.write("\n")

    f.write("ALPHA TABLE (LaTeX format):\n")
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
            [
                "{:.4f}".format(alpha[s, t]) if alpha[s, t] > 1e-10 else "0"
                for t in range(T)
            ]
        )
        f.write("{} & {} & {} \\\\\n".format(s + 1, Z_display[s], vals))
    f.write("\n")

    P_Y_given_X = alpha[S - 2, T - 1] + alpha[S - 1, T - 1]
    f.write("FINAL RESULT:\n")
    f.write("alpha(16, 12) = {:.10f}\n".format(alpha[S - 2, T - 1]))
    f.write("alpha(17, 12) = {:.10f}\n".format(alpha[S - 1, T - 1]))
    f.write("P(Y|X) = {:.10f}\n".format(P_Y_given_X))
    f.write("CTC Loss = {:.6f}\n".format(-np.log(P_Y_given_X)))

print("Results saved to ctc_results.txt")
