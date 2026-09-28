#!/usr/bin/env python3
from pathlib import Path
import math
import numpy as np
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parent
RESULTS_CSV = ROOT / "ngspice_results.csv"
WAVEFORM_CSV = ROOT / "ngspice_waveform.csv"
OUT_DIR = ROOT / "figures_report"
IVERILOG_SUMMARY = ROOT.parent / "open_source_flow" / "figures_report" / "summary.txt"

N_BITS = 5
VFS = 0.45
VCM = 0.7
FS = 500e6
TIMING_TSTOP_NS = 6.0


def load_wrdata_table(path: Path):
    data = np.loadtxt(path, skiprows=1)
    return data


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


def parse_iverilog_summary():
    if not IVERILOG_SUMMARY.exists():
        return None
    result = {}
    for line in IVERILOG_SUMMARY.read_text().splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            result[key.strip()] = value.strip()
    return result


def main():
    OUT_DIR.mkdir(exist_ok=True)

    data = load_wrdata_table(RESULTS_CSV)
    sample_index = data[:, 0]
    vin = data[:, 1]
    codes = data[:, 3]
    conv_time_ps = data[:, 5]
    vdac_out = data[:, 7]

    wave = load_wrdata_table(WAVEFORM_CSV)
    time_ns = wave[:, 0] / 1000.0
    wave_start = wave[:, 1]
    wave_comp_valid = wave[:, 3]
    wave_comp = wave[:, 5]
    wave_done = wave[:, 7]
    wave_trial_code = wave[:, 9]
    wave_final_code = wave[:, 11]

    sndr_db, enob, freq, spectrum_db = calc_sndr_enob(codes)
    lsb_mv = 1e3 * VFS / (2 ** N_BITS)
    avg_conv_ps = float(np.mean(conv_time_ps))
    worst_conv_ps = float(np.max(conv_time_ps))

    fig, axes = plt.subplots(6, 1, figsize=(10, 8), sharex=True)
    signals = [
        ("start", wave_start),
        ("comp_valid", wave_comp_valid),
        ("comp", wave_comp),
        ("done", wave_done),
        ("trial_code", wave_trial_code),
        ("final_code", wave_final_code),
    ]
    for ax, (name, values) in zip(axes, signals):
        ax.step(time_ns, values, where="post", linewidth=1.5)
        ax.set_ylabel(name)
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, TIMING_TSTOP_NS)
    axes[-1].set_xlabel("Time [ns]")
    fig.suptitle("ngspice Behavioral SAR Timing Trace")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "waveform_timing.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

    window = 64
    t_ns = sample_index[:window] / FS * 1e9
    fig, ax1 = plt.subplots(figsize=(10, 4.8))
    ax1.plot(t_ns, vin[:window], label="Vin", linewidth=1.8)
    ax1.step(t_ns, vdac_out[:window], where="mid", label="Vout (DAC-equivalent)", linewidth=1.3)
    ax1.set_xlabel("Time [ns]")
    ax1.set_ylabel("Voltage [V]")
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc="upper left")
    ax2 = ax1.twinx()
    ax2.step(t_ns, codes[:window], where="mid", color="tab:red", alpha=0.35, linewidth=1.2)
    ax2.set_ylabel("Output Code")
    fig.suptitle("ngspice Input Signal and Quantized Output")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "input_output_codes.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.hist(conv_time_ps, bins=20, edgecolor="black")
    ax.set_xlabel("Total Conversion Time [ps]")
    ax.set_ylabel("Count")
    ax.set_title("ngspice Conversion Time Distribution")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "conversion_time_histogram.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.plot(freq / 1e6, spectrum_db, linewidth=1.2)
    ax.set_xlabel("Frequency [MHz]")
    ax.set_ylabel("Magnitude [dBFS]")
    ax.set_title(f"ngspice Output Spectrum: SNDR = {sndr_db:.2f} dB, ENOB = {enob:.2f} bits")
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, FS / 2 / 1e6)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "output_spectrum.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

    summary_lines = [
        f"LSB: {lsb_mv:.3f} mV",
        f"Average conversion time: {avg_conv_ps:.1f} ps",
        f"Worst conversion time: {worst_conv_ps:.1f} ps",
        f"SNDR: {sndr_db:.2f} dB",
        f"ENOB: {enob:.2f} bits",
    ]

    iverilog = parse_iverilog_summary()
    if iverilog is not None:
        summary_lines.append("")
        summary_lines.append("Comparison to Icarus flow:")
        for key in ["Average conversion time", "Worst conversion time", "SNDR", "ENOB"]:
            summary_lines.append(f"{key} (Icarus): {iverilog.get(key, 'n/a')}")
        try:
            avg_delta = avg_conv_ps - float(iverilog["Average conversion time"].split()[0])
            worst_delta = worst_conv_ps - float(iverilog["Worst conversion time"].split()[0])
            sndr_delta = sndr_db - float(iverilog["SNDR"].split()[0])
            enob_delta = enob - float(iverilog["ENOB"].split()[0])
            summary_lines.append(f"Average conversion delta: {avg_delta:+.1f} ps")
            summary_lines.append(f"Worst conversion delta: {worst_delta:+.1f} ps")
            summary_lines.append(f"SNDR delta: {sndr_delta:+.2f} dB")
            summary_lines.append(f"ENOB delta: {enob_delta:+.2f} bits")
        except Exception:
            pass

    (OUT_DIR / "summary.txt").write_text("\n".join(summary_lines) + "\n")
    print("\n".join(summary_lines))


if __name__ == "__main__":
    main()
