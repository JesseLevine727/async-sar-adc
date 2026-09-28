`timescale 1ps/1ps

module tb_async_sar;
    localparam int N_BITS = 5;
    localparam int N_SAMPLES = 1024;
    localparam int SAMPLE_PERIOD_PS = 2000;
    localparam int START_WIDTH_PS = 20;
    localparam real VFS = 0.45;
    localparam real VCM = 0.7;
    localparam real INPUT_PEAK_FRAC = 0.95;
    localparam real PI = 3.14159265358979323846;
    localparam int INPUT_BIN = 37;
    localparam real LSB = VFS / (1 << N_BITS);

    logic start;
    logic comp_valid;
    logic comp;
    logic [4:0] trial_code;
    logic [4:0] final_code;
    logic active;
    logic done;

    integer sample_idx;
    integer code_fd;
    integer vcd_sample_limit;
    integer decision_count;
    logic [31:0] comp_delay_ps;

    real vin_sample;
    real vdac_trial;

    sar_logic_async dut (
        .start(start),
        .comp_valid(comp_valid),
        .comp(comp),
        .trial_code(trial_code),
        .final_code(final_code),
        .active(active),
        .done(done)
    );

    strongarm_comp_model #(
        .N_BITS(N_BITS),
        .VFS(VFS),
        .VCM(VCM),
        .T_CMP_NOM_PS(124.0),
        .T_CMP_MIN_PS(60.0),
        .T_CMP_MAX_PS(250.0)
    ) strongarm_cmp (
        .start(start),
        .trial_code(trial_code),
        .vin_sample(vin_sample),
        .comp(comp),
        .comp_valid(comp_valid),
        .delay_ps(comp_delay_ps)
    );

    initial begin
        start = 1'b0;
        sample_idx = 0;
        decision_count = 0;
        vin_sample = VCM;
        vdac_trial = VCM - 0.5 * VFS;
        vcd_sample_limit = 12;

        code_fd = $fopen("codes.csv", "w");
        if (code_fd == 0) begin
            $display("ERROR: could not open codes.csv");
            $finish;
        end
        $fwrite(code_fd, "sample_index,code,vin,conversion_time_ps\n");

        $dumpfile("async_sar.vcd");
        $dumpvars(0, tb_async_sar);

        repeat (N_SAMPLES) begin
            start_conversion(sample_idx);
            @(posedge done);
            $fwrite(code_fd, "%0d,%0d,%.12f,%0d\n",
                    sample_idx, final_code, vin_sample, decision_count);
            #(SAMPLE_PERIOD_PS - decision_count - START_WIDTH_PS);
            sample_idx = sample_idx + 1;
        end

        $fclose(code_fd);
        $display("Completed %0d conversions", N_SAMPLES);
        $finish;
    end

    task start_conversion(input integer idx);
        real sample_phase;
        begin
            sample_phase = 2.0 * PI * INPUT_BIN * idx / N_SAMPLES;
            vin_sample = VCM + INPUT_PEAK_FRAC * 0.5 * VFS * $sin(sample_phase);
            decision_count = 0;
            start = 1'b1;
            #START_WIDTH_PS;
            start = 1'b0;
        end
    endtask

    always @(*) begin
        vdac_trial = VCM - 0.5 * VFS + VFS * trial_code / (1 << N_BITS);
    end

    always @(posedge comp_valid) begin
        decision_count = decision_count + comp_delay_ps;
    end

    always @(posedge done) begin
        if (sample_idx < vcd_sample_limit) begin
            $display("sample=%0d vin=%.6f code=%0d conv_time_ps=%0d",
                     sample_idx, vin_sample, final_code, decision_count);
        end
    end
endmodule
