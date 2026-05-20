from pathlib import Path
from typing import Tuple, List

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp, chisquare

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RESULTS_DIR = ROOT / "results"


def per_session_conversion(df: pd.DataFrame) -> Tuple[float, np.ndarray]:
    session = df.groupby("session_id")
    converted = session["conversion_flag"].max()
    rate = float((converted > 0).mean())
    return rate, converted.values.astype(int)


def bootstrap_ci(values: np.ndarray, iters: int = 10_000, alpha: float = 0.05) -> Tuple[float, float]:
    rng = np.random.default_rng(42)
    n = len(values)
    stats = []
    for _ in range(iters):
        sample = values[rng.integers(0, n, size=n)]
        stats.append(float((sample > 0).mean()))
    lower = np.percentile(stats, alpha / 2 * 100)
    upper = np.percentile(stats, (1 - alpha / 2) * 100)
    return float(lower), float(upper)


def session_lengths(df: pd.DataFrame) -> np.ndarray:
    return df.groupby("session_id").size().values.astype(int)


def screen_distribution(df: pd.DataFrame) -> Tuple[List[str], np.ndarray]:
    counts = df["screen_name"].value_counts()
    screens = counts.index.tolist()
    values = counts.values.astype(float)
    return screens, values


def top_transitions(df: pd.DataFrame, k: int = 5) -> List[Tuple[str, str]]:
    df_sorted = df.sort_values(["user_id", "session_id", "timestamp"])
    pairs = []
    for _, g in df_sorted.groupby(["user_id", "session_id"]):
        screens = g["screen_name"].astype(str).tolist()
        for i in range(len(screens) - 1):
            pairs.append((screens[i], screens[i + 1]))
    counts = {}
    for a, b in pairs:
        key = (a, b)
        counts[key] = counts.get(key, 0) + 1
    ranked = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    return [p for p, _ in ranked[:k]]


def main() -> None:
    RESULTS_DIR.mkdir(exist_ok=True)

    real = pd.read_csv(DATA_DIR / "cleaned_logs.csv", parse_dates=["timestamp"])
    synth = pd.read_csv(DATA_DIR / "synthetic_logs.csv", parse_dates=["timestamp"])

    real_rate, real_conv_array = per_session_conversion(real)
    synth_rate, synth_conv_array = per_session_conversion(synth)
    real_ci_low, real_ci_high = bootstrap_ci(real_conv_array)
    synth_ci_low, synth_ci_high = bootstrap_ci(synth_conv_array)

    real_lengths = session_lengths(real)
    synth_lengths = session_lengths(synth)
    ks_stat, ks_p = ks_2samp(real_lengths, synth_lengths)

    real_screens, real_counts = screen_distribution(real)
    synth_screens, synth_counts = screen_distribution(synth)
    all_screens = sorted(set(real_screens) | set(synth_screens))
    real_map = dict(zip(real_screens, real_counts))
    synth_map = dict(zip(synth_screens, synth_counts))
    real_vec = np.array([real_map.get(s, 0.0) for s in all_screens])
    synth_vec = np.array([synth_map.get(s, 0.0) for s in all_screens])
    if real_vec.sum() == 0 or synth_vec.sum() == 0:
        chi2_stat, chi2_p = 0.0, 1.0
    else:
        expected = real_vec * (synth_vec.sum() / real_vec.sum())
        chi2_stat, chi2_p = chisquare(f_obs=synth_vec, f_exp=expected)

    real_top = top_transitions(real, k=5)
    synth_top = top_transitions(synth, k=5)
    overlap = len(set(real_top) & set(synth_top))

    diff_rate = abs(real_rate - synth_rate) / max(real_rate, 1e-8)
    if diff_rate <= 0.10 and ks_p > 0.05 and chi2_p > 0.05 and overlap >= 3:
        verdict = "PASS"
    elif diff_rate <= 0.15:
        verdict = "PARTIAL"
    else:
        verdict = "FAIL"

    lines = [
        "Validation report (real vs synthetic sessions)",
        "",
        f"Real per-session conversion rate: {real_rate:.4f} (95% CI [{real_ci_low:.4f}, {real_ci_high:.4f}])",
        f"Synthetic per-session conversion rate: {synth_rate:.4f} (95% CI [{synth_ci_low:.4f}, {synth_ci_high:.4f}])",
        f"Relative difference: {diff_rate:.4f}",
        "",
        f"Session length KS test: statistic={ks_stat:.4f}, p-value={ks_p:.4f}",
        f"Screen distribution chi-square: statistic={chi2_stat:.4f}, p-value={chi2_p:.4f}",
        "",
        f"Top-5 real transitions: {real_top}",
        f"Top-5 synthetic transitions: {synth_top}",
        f"Overlap in top-5 transitions: {overlap}/5",
        "",
        f"Final validation verdict: {verdict}",
    ]

    with open(RESULTS_DIR / "validation_report.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
