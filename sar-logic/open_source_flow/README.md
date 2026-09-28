**Open-Source A3 Flow**

This directory avoids Cadence entirely.

It uses:
- `iverilog` for simulation
- `gtkwave` for waveform viewing
- `python3` for ENOB calculation

**Files**

- `sar_logic_async.sv`: 5-bit asynchronous SAR controller
- `strongarm_comp_model.sv`: behavioral StrongARM latch model derived from A2 timing
- `tb_async_sar.sv`: idealized ADC testbench with DAC/comparator timing model
- `analyze_enob.py`: reads `codes.csv` and computes SNDR/ENOB

**Recommended Install**

On Ubuntu:

```bash
sudo apt update
sudo apt install -y iverilog gtkwave
```

**Run**

```bash
iverilog -g2012 -o async_sar_tb tb_async_sar.sv sar_logic_async.sv strongarm_comp_model.sv
vvp async_sar_tb
python3 analyze_enob.py
```

If you want to use the locally extracted `iverilog` tool without installing anything system-wide:

```bash
cd /home/elfo/Documents/ELEC5705/A3/open_source_flow
bash run_local_flow.sh
```

This produces:
- `async_sar.vcd` for waveform viewing in GTKWave
- `codes.csv` with one conversion result per sample

To inspect waveforms:

```bash
gtkwave async_sar.vcd
```

To generate report-ready PNG plots:

```bash
./.venv/bin/python generate_report_plots.py
```

This writes figures into `figures_report/`.

**What The Testbench Models**

- `start` pulse every `2 ns`, matching `500 MS/s`
- sampled input held constant during conversion
- ideal 5-bit DAC
- StrongARM-inspired comparator model derived from A2
- comparator delay that depends on input overdrive
- SAR logic that advances on each `comp_valid` event

**What To Plot For The Report**

- `start`
- `trial_code[4:0]`
- `final_code[4:0]`
- `comp`
- `comp_valid`

Use the console output and `codes.csv` for average conversion time and ENOB.
