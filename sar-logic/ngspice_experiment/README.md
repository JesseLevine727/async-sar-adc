**ngspice A3 Experiment**

This directory is a separate open-source experiment for Assignment 3 using `ngspice`.

Because `ngspice` is not a natural fit for event-driven SAR logic, this version uses the
`ngspice` control language to implement a behavioral asynchronous SAR loop rather than the
SystemVerilog controller used in `open_source_flow/`.

**Files**

- `ngspice_behavioral_sar.cir`: behavioral SAR experiment implemented in `ngspice`
- `analyze_ngspice.py`: reads the exported `ngspice` data and generates figures
- `run_local_flow.sh`: runs the local `ngspice` binary and analysis script

**Run**

```bash
cd /home/elfo/Documents/ELEC5705/A3/ngspice_experiment
bash run_local_flow.sh
```

If `ngspice` is installed system-wide, `run_local_flow.sh` will use it automatically.
Otherwise you may set:

```bash
export NGSPICE_BIN=/path/to/ngspice
```

**Outputs**

- `ngspice_results.csv`
- `ngspice_waveform.csv`
- `figures_report/waveform_timing.png`
- `figures_report/input_output_codes.png`
- `figures_report/conversion_time_histogram.png`
- `figures_report/output_spectrum.png`
- `figures_report/summary.txt`

**Modeling Note**

This is not a transistor-level SAR implementation in `ngspice`. It is a behavioral experiment
that uses the same A2-derived comparator timing assumptions as the Icarus flow so that the two
open-source methods can be compared directly.
