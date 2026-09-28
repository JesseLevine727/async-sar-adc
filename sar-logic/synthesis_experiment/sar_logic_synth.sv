module sar_logic_synth (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       start,
    input  wire       comp_valid,
    input  wire       comp,
    output reg  [4:0] trial_code,
    output reg  [4:0] final_code,
    output reg        active,
    output reg        done
);
    reg [2:0] bit_idx;
    reg [4:0] committed_code;
    reg [4:0] kept_code;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            bit_idx = 3'd4;
            committed_code = 5'd0;
            trial_code = 5'd0;
            final_code = 5'd0;
            active = 1'b0;
            done = 1'b0;
        end else if (start) begin
            bit_idx = 3'd4;
            committed_code = 5'd0;
            trial_code = 5'b10000;
            final_code = 5'd0;
            active = 1'b1;
            done = 1'b0;
        end else if (active && comp_valid) begin
            kept_code = committed_code;
            if (comp)
                kept_code = trial_code;

            committed_code = kept_code;

            if (bit_idx > 0) begin
                bit_idx = bit_idx - 1'b1;
                trial_code = kept_code | (5'b00001 << (bit_idx - 1'b1));
                done = 1'b0;
            end else begin
                final_code = kept_code;
                trial_code = kept_code;
                active = 1'b0;
                done = 1'b1;
            end
        end else begin
            done = 1'b0;
        end
    end
endmodule
