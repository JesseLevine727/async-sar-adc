`timescale 1ps/1ps

module sar_logic_async (
    input  logic       start,
    input  logic       comp_valid,
    input  logic       comp,
    output logic [4:0] trial_code,
    output logic [4:0] final_code,
    output logic       active,
    output logic       done
);
    integer bit_idx;
    reg [4:0] committed_code;
    reg [4:0] next_code;

    initial begin
        active = 1'b0;
        done = 1'b0;
        bit_idx = 4;
        committed_code = 5'd0;
        trial_code = 5'd0;
        final_code = 5'd0;
    end

    always @(posedge start) begin
        active = 1'b1;
        done = 1'b0;
        bit_idx = 4;
        committed_code = 5'd0;
        trial_code = 5'b10000;
        final_code = 5'd0;
    end

    always @(posedge comp_valid) begin
        if (active) begin
            next_code = committed_code;
            if (comp)
                next_code = trial_code;

            committed_code = next_code;

            if (bit_idx > 0) begin
                bit_idx = bit_idx - 1;
                trial_code = next_code | (5'b00001 << bit_idx);
            end else begin
                final_code = next_code;
                trial_code = next_code;
                active = 1'b0;
                done = 1'b1;
            end
        end
    end

    always @(negedge start) begin
        if (!active)
            done = 1'b0;
    end
endmodule
