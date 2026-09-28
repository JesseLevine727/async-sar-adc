`timescale 1ps/1ps

module strongarm_comp_model #(
    parameter int  N_BITS = 5,
    parameter real VFS = 0.45,
    parameter real VCM = 0.7,
    parameter real INPUT_OFFSET_V = 0.0,
    parameter real T_CMP_NOM_PS = 124.0,
    parameter real T_CMP_MIN_PS = 60.0,
    parameter real T_CMP_MAX_PS = 250.0,
    parameter real DV_FLOOR_V = 1e-3
) (
    input  logic       start,
    input  logic [4:0] trial_code,
    input  real        vin_sample,
    output logic       comp,
    output logic       comp_valid,
    output logic [31:0] delay_ps
);
    real dv_ref_v;

    initial begin
        comp = 1'b0;
        comp_valid = 1'b0;
        delay_ps = 0;
        dv_ref_v = 0.5 * VFS / (1 << N_BITS);
    end

    // StrongARM-inspired behavioral model based on A2:
    // - nominal decision time around 124 ps at ~0.5 LSB overdrive
    // - faster for larger overdrive, bounded below by T_CMP_MIN_PS
    // - slower for smaller overdrive, bounded above by T_CMP_MAX_PS
    always @(posedge start or trial_code) begin
        real vin_eff;
        real vdac_trial;
        real overdrive_v;
        real scaled_delay_ps;
        integer local_delay_ps;
        reg comp_result;

        vin_eff = vin_sample + INPUT_OFFSET_V;
        vdac_trial = VCM - 0.5 * VFS + VFS * trial_code / (1 << N_BITS);
        overdrive_v = (vin_eff >= vdac_trial) ? (vin_eff - vdac_trial) : (vdac_trial - vin_eff);

        if (overdrive_v < DV_FLOOR_V)
            overdrive_v = DV_FLOOR_V;

        scaled_delay_ps = T_CMP_NOM_PS * (dv_ref_v / overdrive_v);
        if (scaled_delay_ps < T_CMP_MIN_PS)
            scaled_delay_ps = T_CMP_MIN_PS;
        if (scaled_delay_ps > T_CMP_MAX_PS)
            scaled_delay_ps = T_CMP_MAX_PS;

        local_delay_ps = $rtoi(scaled_delay_ps);
        comp_result = (vin_eff >= vdac_trial);
        delay_ps = local_delay_ps[31:0];

        fork
            begin
                #local_delay_ps;
                comp = comp_result;
                comp_valid = 1'b1;
                #1;
                comp_valid = 1'b0;
            end
        join_none
    end
endmodule
