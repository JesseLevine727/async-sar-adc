# Synthesis Experiment

This directory contains a gate-level synthesis cross-check for the Assignment 3
SAR controller.

Scope:
- digital SAR controller only
- synthesized with Yosys
- not transistor-level
- not a full ADC implementation

Files:
- `sar_logic_synth.sv`: synthesis-oriented SAR controller RTL
- `synth.ys`: Yosys synthesis script
- `run_local_flow.sh`: runs local Yosys and writes the outputs
- `sar_logic_synth_netlist.v`: generated gate-level Verilog netlist
- `sar_logic_synth.dot`: generated graphviz netlist view

Usage:
```bash
cd /home/elfo/Documents/ELEC5705/A3/synthesis_experiment
bash run_local_flow.sh
```

Outputs:
- `sar_logic_synth_netlist.v`
- `sar_logic_synth.json`
- `sar_logic_synth.dot`
- `synthesis.log`

Current synthesis result:
- 79 total cells
- 18 `$_DFFE_PN0P_` cells
- 1 `$_DFFE_PN1P_` cell
- 1 `$_DFF_PN0_` cell
- 35 `$_AND_` cells
- 11 `$_OR_` cells
- 7 `$_NOT_` cells
- 5 `$_MUX_` cells
- 1 `$_XOR_` cell

Interpretation:
- this is a gate-level digital realization of the SAR controller only
- it is not a transistor-level ADC implementation
- the dot file is a structural graph of the synthesized controller
