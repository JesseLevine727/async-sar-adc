**Files**

- `sar_logic.va`: 5-bit asynchronous SAR controller
- `ideal_dac.va`: ideal 5-bit DAC driven by the SAR bits
- `ideal_comp.va`: ideal comparator with a fixed delay
- `async_sar_tb.va`: self-contained behavioral top-level testbench

**How To Use In Cadence**

1. Create a new library for the assignment.
2. For each `.va` file, create a new cell and add the file as a `veriloga` view.
3. Either:
   - use `async_sar_tb.va` as the top-level for simulation, or
   - create a schematic testbench and instantiate `sar_logic`, `ideal_dac`, and `ideal_comp`.
4. Run a transient simulation for at least `2 us` so you capture many output codes.
5. Plot:
   - `vin`
   - `vdac`
   - `comp`
   - `b4`, `b3`, `b2`, `b1`, `b0`
   - `done`

**What The Logic Does**

- A rising edge on `start` begins a new conversion.
- The controller first tries the MSB.
- Each transition on `comp` is treated as the async decision event for the current bit.
- If `comp = 1`, the current trial bit is kept.
- If `comp = 0`, the current trial bit is cleared.
- The next lower bit is then tried immediately.
- After the LSB decision, `done` goes high.

**Important Modeling Note**

This is a behavioral async SAR loop. It is intended for Assignment 3 style logic verification, not for final transistor-level tapeout-quality timing validation.

**Pure External-File Spectre Flow**

If you want to avoid Cadence's text editor entirely, use [run_async_sar.scs](/home/elfo/Documents/ELEC5705/A3/cadence_behavioral/run_async_sar.scs).

From a terminal:

```bash
cd /home/elfo/Documents/ELEC5705/A3/cadence_behavioral
spectre run_async_sar.scs
```

This includes the three Verilog-A files directly from disk and runs a transient simulation without requiring a Cadence schematic or Verilog-A cellview.
