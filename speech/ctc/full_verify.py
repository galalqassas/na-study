"""
CTC Verification - Manual Calculation Check
Validates every calculation in ctc.md
"""

import numpy as np

np.set_printoptions(precision=6, suppress=True)
np.random.seed(42)

# === PROBABILITY MATRIX (from ctc.md and ctc_results.txt) ===
# Row order: n, a, space, g, r, o, u, p, eps
probs = np.array(
    [
        [
            0.700,
            0.500,
            0.037,
            0.059,
            0.002,
            0.007,
            0.022,
            0.011,
            0.020,
            0.000,
            0.091,
            0.127,
        ],  # n
        [
            0.017,
            0.057,
            0.600,
            0.149,
            0.101,
            0.036,
            0.006,
            0.026,
            0.048,
            0.106,
            0.045,
            0.037,
        ],  # a
        [
            0.111,
            0.076,
            0.076,
            0.022,
            0.650,
            0.002,
            0.096,
            0.006,
            0.009,
            0.077,
            0.018,
            0.007,
        ],  # space
        [
            0.049,
            0.001,
            0.058,
            0.070,
            0.115,
            0.700,
            0.041,
            0.047,
            0.099,
            0.082,
            0.003,
            0.073,
        ],  # g
        [
            0.034,
            0.216,
            0.035,
            0.087,
            0.056,
            0.125,
            0.600,
            0.059,
            0.005,
            0.093,
            0.017,
            0.083,
        ],  # r
        [
            0.006,
            0.110,
            0.097,
            0.005,
            0.012,
            0.016,
            0.077,
            0.550,
            0.265,
            0.005,
            0.018,
            0.048,
        ],  # o
        [
            0.006,
            0.015,
            0.015,
            0.091,
            0.004,
            0.057,
            0.062,
            0.038,
            0.090,
            0.600,
            0.060,
            0.086,
        ],  # u
        [
            0.002,
            0.012,
            0.035,
            0.018,
            0.039,
            0.020,
            0.025,
            0.211,
            0.014,
            0.028,
            0.700,
            0.040,
        ],  # p
        [
            0.074,
            0.013,
            0.047,
            0.500,
            0.020,
            0.038,
            0.070,
            0.053,
            0.450,
            0.008,
            0.047,
            0.500,
        ],  # eps
    ]
)

vocab = ["n", "a", " ", "g", "r", "o", "u", "p", "eps"]
vocab_to_idx = {c: i for i, c in enumerate(vocab)}
T = 12

# === VERIFY COLUMN SUMS ===
print("=== COLUMN SUM VERIFICATION ===")
col_sums = probs.sum(axis=0)
print("Column sums:", col_sums)
for t in range(T):
    if abs(col_sums[t] - 1.0) > 0.01:
        print(f"  WARNING: Column {t + 1} sums to {col_sums[t]:.4f}, not 1.0")
print()

# === EXTENDED SEQUENCE Z ===
target_Y = list("na group")
Z = []
for char in target_Y:
    Z.append("eps")
    if char == " ":
        Z.append(" ")
    else:
        Z.append(char)
Z.append("eps")
S = len(Z)

print("=== EXTENDED SEQUENCE Z ===")
print(f"Y = {target_Y} ({len(target_Y)} chars)")
print(f"Z = {Z} ({S} states)")
print()


# === FORWARD ALGORITHM ===
def forward_algorithm(probs, Z, vocab_to_idx):
    S = len(Z)
    T = probs.shape[1]
    alpha = np.zeros((S, T))

    # Initialization at t=0 (corresponds to t=1 in document)
    alpha[0, 0] = probs[vocab_to_idx[Z[0]], 0]  # eps at t=1
    alpha[1, 0] = probs[vocab_to_idx[Z[1]], 0]  # n at t=1

    # Recurrence
    for t in range(1, T):
        for s in range(S):
            z_s = Z[s]
            z_s_idx = vocab_to_idx[z_s]

            if s == 0:
                # Only stay in same state
                alpha[s, t] = alpha[s, t - 1] * probs[z_s_idx, t]
            elif s == 1:
                # Can come from state 0 or stay
                alpha[s, t] = (alpha[s - 1, t - 1] + alpha[s, t - 1]) * probs[
                    z_s_idx, t
                ]
            else:
                if z_s == "eps" or (s >= 2 and Z[s] == Z[s - 2]):
                    # Case 1: Cannot skip (blank or repeated char)
                    alpha[s, t] = (alpha[s - 1, t - 1] + alpha[s, t - 1]) * probs[
                        z_s_idx, t
                    ]
                else:
                    # Case 2: Can skip (unique char, prev is blank)
                    alpha[s, t] = (
                        alpha[s - 2, t - 1] + alpha[s - 1, t - 1] + alpha[s, t - 1]
                    ) * probs[z_s_idx, t]

    return alpha


alpha = forward_algorithm(probs, Z, vocab_to_idx)

# === VERIFY INITIALIZATION (t=1) ===
print("=== INITIALIZATION VERIFICATION (t=1) ===")
print(f"alpha(1,1) = P(eps|t=1) = {probs[8, 0]:.4f}")
print(f"alpha(2,1) = P(n|t=1) = {probs[0, 0]:.4f}")
print(f"Computed: alpha[0,0] = {alpha[0, 0]:.4f}, alpha[1,0] = {alpha[1, 0]:.4f}")
print()

# === VERIFY t=2 CALCULATIONS ===
print("=== t=2 STEP-BY-STEP VERIFICATION ===")
# State 1 (eps): alpha(1,1) * P(eps|2)
calc_1_2 = alpha[0, 0] * probs[8, 1]
print(f"alpha(1,2) = {alpha[0, 0]:.4f} * {probs[8, 1]:.4f} = {calc_1_2:.6f}")
print(f"  Computed: {alpha[0, 1]:.6f}")

# State 2 (n): [alpha(1,1) + alpha(2,1)] * P(n|2)  -- Case 2 (can skip nothing since s=1)
calc_2_2 = (alpha[0, 0] + alpha[1, 0]) * probs[0, 1]
print(
    f"alpha(2,2) = [{alpha[0, 0]:.4f} + {alpha[1, 0]:.4f}] * {probs[0, 1]:.4f} = {calc_2_2:.6f}"
)
print(f"  Computed: {alpha[1, 1]:.6f}")

# State 3 (eps): [alpha(2,1) + alpha(3,1)] * P(eps|2) -- Case 1 (eps)
calc_3_2 = (alpha[1, 0] + alpha[2, 0]) * probs[8, 1]
print(
    f"alpha(3,2) = [{alpha[1, 0]:.4f} + {alpha[2, 0]:.4f}] * {probs[8, 1]:.4f} = {calc_3_2:.6f}"
)
print(f"  Computed: {alpha[2, 1]:.6f}")

# State 4 (a): [alpha(2,1) + alpha(3,1) + alpha(4,1)] * P(a|2) -- Case 2 (unique char)
calc_4_2 = (alpha[1, 0] + alpha[2, 0] + alpha[3, 0]) * probs[1, 1]
print(
    f"alpha(4,2) = [{alpha[1, 0]:.4f} + {alpha[2, 0]:.4f} + {alpha[3, 0]:.4f}] * {probs[1, 1]:.4f} = {calc_4_2:.6f}"
)
print(f"  Computed: {alpha[3, 1]:.6f}")
print()

# === FINAL RESULT ===
print("=== FINAL RESULT ===")
P_Y_given_X = alpha[S - 2, T - 1] + alpha[S - 1, T - 1]
print(f"alpha(16, 12) = alpha[{S - 2}, {T - 1}] = {alpha[S - 2, T - 1]:.10f}")
print(f"alpha(17, 12) = alpha[{S - 1}, {T - 1}] = {alpha[S - 1, T - 1]:.10f}")
print(f"P(Y|X) = {P_Y_given_X:.10f}")
print(f"CTC Loss = -log(P(Y|X)) = {-np.log(P_Y_given_X):.6f}")
print()

# Compare with ctc_results.txt
print("=== COMPARISON WITH ctc_results.txt ===")
expected_alpha_16_12 = 0.0004581489
expected_alpha_17_12 = 0.0050243620
expected_P = 0.0054825109
expected_loss = 5.206192

print(f"Expected alpha(16,12) = {expected_alpha_16_12:.10f}")
print(f"Computed alpha(16,12) = {alpha[S - 2, T - 1]:.10f}")
print(f"  Match: {abs(alpha[S - 2, T - 1] - expected_alpha_16_12) < 0.0001}")

print(f"Expected alpha(17,12) = {expected_alpha_17_12:.10f}")
print(f"Computed alpha(17,12) = {alpha[S - 1, T - 1]:.10f}")
print(f"  Match: {abs(alpha[S - 1, T - 1] - expected_alpha_17_12) < 0.0001}")

print(f"Expected P(Y|X) = {expected_P:.10f}")
print(f"Computed P(Y|X) = {P_Y_given_X:.10f}")
print(f"  Match: {abs(P_Y_given_X - expected_P) < 0.0001}")
print()

# === GREEDY DECODING VERIFICATION ===
print("=== GREEDY DECODING VERIFICATION ===")
greedy_indices = np.argmax(probs, axis=0)
greedy_chars = [vocab[i] for i in greedy_indices]
print(f"Argmax at each timestep: {list(greedy_indices)}")
print(f"Characters: {greedy_chars}")

# Collapse
collapsed = []
prev = None
for c in greedy_chars:
    if c != "eps" and c != prev:
        collapsed.append(c)
    prev = c
collapsed_str = "".join(collapsed)
print(f"Collapsed output: '{collapsed_str}'")
print(f"Expected: 'na group'")
print(f"Match: {collapsed_str == 'na group'}")
