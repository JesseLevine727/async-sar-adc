#!/usr/bin/env python3
import csv
import math
from pathlib import Path


def hann_window(n: int):
    return [0.5 - 0.5 * math.cos(2.0 * math.pi * i / (n - 1)) for i in range(n)]


def dft_real(x):
    n = len(x)
    out = []
    for k in range(n // 2 + 1):
        re = 0.0
        im = 0.0
        for i, xi in enumerate(x):
            angle = -2.0 * math.pi * k * i / n
            re += xi * math.cos(angle)
            im += xi * math.sin(angle)
        out.append((re, im))
    return out


def main():
    csv_path = Path("codes.csv")
    if not csv_path.exists():
        raise SystemExit("codes.csv not found. Run the simulation first.")

    codes = []
    conv_times = []
    with csv_path.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            codes.append(float(row["code"]))
            conv_times.append(float(row["conversion_time_ps"]))

    n = len(codes)
    n_bits = 5
    fs = 500e6
    lsb_mv = 1e3 * 0.45 / (2 ** n_bits)

    mean_code = sum(codes) / n
    x = [(c - mean_code) / (2 ** (n_bits - 1)) for c in codes]
    win = hann_window(n)
    coherent_gain = sum(win) / n
    xw = [a * b for a, b in zip(x, win)]

    spectrum = dft_real(xw)
    mags = [math.hypot(re, im) / (n * coherent_gain) for re, im in spectrum]
    powers = [m * m for m in mags]
    for i in range(1, len(powers) - 1):
        powers[i] *= 2.0

    signal_bin = max(range(1, len(powers)), key=lambda i: powers[i])
    signal_bins = range(max(1, signal_bin - 1), min(len(powers), signal_bin + 2))
    signal_power = sum(powers[i] for i in signal_bins)
    noise_dist_power = sum(powers[1:]) - signal_power

    sndr_db = 10.0 * math.log10(signal_power / noise_dist_power)
    enob = (sndr_db - 1.76) / 6.02

    avg_conv_ps = sum(conv_times) / len(conv_times)
    worst_conv_ps = max(conv_times)

    print(f"Samples               : {n}")
    print(f"LSB                   : {lsb_mv:.3f} mV")
    print(f"Average conversion    : {avg_conv_ps:.1f} ps")
    print(f"Worst conversion      : {worst_conv_ps:.1f} ps")
    print(f"SNDR                  : {sndr_db:.2f} dB")
    print(f"ENOB                  : {enob:.2f} bits")


if __name__ == "__main__":
    main()
