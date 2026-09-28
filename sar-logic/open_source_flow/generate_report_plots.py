#!/usr/bin/env python3
from pathlib import Path
import csv
import math

import matplotlib.pyplot as plt
import numpy as np
from vcdvcd import VCDVCD


ROOT = Path(__file__).resolve().parent
CSV_PATH = ROOT / "codes.csv"
VCD_PATH = ROOT / "async_sar.vcd"
FIG_DIR = ROOT / "figures_report"

N_BITS = 5
VFS = 0.45
VCM = 0.7
FS = 500e6


def read_codes():
    sample_idx = []
    codes = []
    vin = []
    conv_ps = []
    with CSV_PATH.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            sample_idx.append(int(row["sample_index"]))
            codes.append(int(row["code"]))
            vin.append(float(row["vin"]))
            conv_ps.append(float(row["conversion_time_ps"]))
    return np.array(sample_idx), np.array(codes), np.array(vin), np.array(conv_ps)


def code_to_vdac(code):
    return VCM - 0.5 * VFS + VFS * code / (2 ** N_BITS)


def calc_sndr_enob(codes):
    x = codes.astype(float)
    x = x - np.mean(x)
    x = x / (2 ** (N_BITS - 1))

    n = len(x)
    win = np.hanning(n)
    coherent_gain = np.sum(win) / n
    xw = x * win

    spectrum = np.fft.rfft(xw)
    mag = np.abs(spectrum) / (n * coherent_gain)
    power = mag ** 2
    if len(power) > 2:
        power[1:-1] *= 2.0

    signal_bin = np.argmax(power[1:]) + 1
    lo = max(signal_bin - 1, 1)
    hi = min(signal_bin + 1, len(power) - 1)
    signal_power = np.sum(power[lo:hi + 1])
    noise_dist_power = np.sum(power[1:]) - signal_power

    sndr_db = 10.0 * np.log10(signal_power / noise_dist_power)
    enob = (sndr_db - 1.76) / 6.02
    freq = np.fft.rfftfreq(n, d=1.0 / FS)
    spectrum_db = 10.0 * np.log10(np.maximum(power, 1e-20))
    return sndr_db, enob, freq, spectrum_db


def step_from_tv(tv, t_stop_ps):
    times = [t for t, _ in tv]
    vals = [v for _, v in tv]
    if not times:
        return np.array([0.0, t_stop_ps]), np.array([0, 0])

    x = [times[0]]
    y = [int(vals[0], 2) if isinstance(vals[0], str) else int(vals[0])]
    prev_t = times[0]
    prev_v = y[0]
    for t, v in tv[1:]:
        v_int = int(v, 2) if isinstance(v, str) else int(v)
        x.extend([t, t])
        y.extend([prev_v, v_int])
        prev_t = t
        prev_v = v_int
    x.append(t_stop_ps)
    y.append(prev_v)
    return np.array(x), np.array(y)


def plot_waveforms():
    vcd = VCDVCD(str(VCD_PATH), store_tvs=True)
    sig = {
        "start": vcd["tb_async_sar.start"].tv,
        "comp": vcd["tb_async_sar.comp"].tv,
        "comp_valid": vcd["tb_async_sar.comp_valid"].tv,
        "done": vcd["tb_async_sar.done"].tv,
        "trial_code": vcd["tb_async_sar.trial_code[4:0]"].tv,
        "final_code": vcd["tb_async_sar.final_code[4:0]"].tv,
    }

    t_stop_ps = 6000
    names = ["start", "comp_valid", "comp", "done", "trial_code", "final_code"]
    fig, axes = plt.subplots(len(names), 1, figsize=(10, 8), sharex=True)

    for ax, name in zip(axes, names):
        x, y = step_from_tv(sig[name], t_stop_ps)
        mask = x <= t_stop_ps
        x_ns = x[mask] / 1000.0
        y_plot = y[mask]
        ax.step(x_ns, y_plot, where="post", linewidth=1.5)
        ax.set_ylabel(name)
        ax.grid(True, alpha=0.3)

    axes[-1].set_xlabel("Time [ns]")
    fig.suptitle("Asynchronous SAR Logic Timing with StrongARM-Based Comparator Model")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "waveform_timing.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def plot_input_output(sample_idx, codes, vin):
    window = 64
    t_ns = sample_idx[:window] / FS * 1e9
    vdac = code_to_vdac(codes[:window])

    fig, ax1 = plt.subplots(figsize=(10, 4.8))
    ax1.plot(t_ns, vin[:window], label="Vin", linewidth=1.8)
    ax1.step(t_ns, vdac, where="mid", label="Vout (DAC-equivalent)", linewidth=1.3)
    ax1.set_xlabel("Time [ns]")
    ax1.set_ylabel("Voltage [V]")
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc="upper left")

    ax2 = ax1.twinx()
    ax2.step(t_ns, codes[:window], where="mid", color="tab:red", alpha=0.35, linewidth=1.2)
    ax2.set_ylabel("Output Code")

    fig.suptitle("Input Signal and Quantized SAR Output")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "input_output_codes.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def plot_conv_hist(conv_ps):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.hist(conv_ps, bins=20, edgecolor="black")
    ax.set_xlabel("Total Conversion Time [ps]")
    ax.set_ylabel("Count")
    ax.set_title("Asynchronous Conversion Time Distribution")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "conversion_time_histogram.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def plot_spectrum(codes):
    sndr_db, enob, freq, spectrum_db = calc_sndr_enob(codes)
    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.plot(freq / 1e6, spectrum_db, linewidth=1.2)
    ax.set_xlabel("Frequency [MHz]")
    ax.set_ylabel("Magnitude [dBFS]")
    ax.set_title(f"Output Spectrum: SNDR = {sndr_db:.2f} dB, ENOB = {enob:.2f} bits")
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, FS / 2 / 1e6)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "output_spectrum.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def main():
    FIG_DIR.mkdir(exist_ok=True)

    sample_idx, codes, vin, conv_ps = read_codes()
    plot_waveforms()
    plot_input_output(sample_idx, codes, vin)
    plot_conv_hist(conv_ps)
    plot_spectrum(codes)

    lsb_mv = 1e3 * VFS / (2 ** N_BITS)
    sndr_db, enob, _, _ = calc_sndr_enob(codes)
    summary = [
        f"LSB: {lsb_mv:.3f} mV",
        f"Average conversion time: {np.mean(conv_ps):.1f} ps",
        f"Worst conversion time: {np.max(conv_ps):.1f} ps",
        f"SNDR: {sndr_db:.2f} dB",
        f"ENOB: {enob:.2f} bits",
    ]
    (FIG_DIR / "summary.txt").write_text("\n".join(summary) + "\n")
    print(f"Saved report figures to {FIG_DIR}")


if __name__ == "__main__":
    main()
