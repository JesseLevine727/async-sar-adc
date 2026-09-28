clear;
close all;
clc;

% 5-bit asynchronous SAR ADC behavioral model.
% The comparator and CDAC are idealized so the focus stays on SAR logic
% timing, conversion sequencing, and ENOB estimation.

%% ADC and stimulus settings
cfg.nBits = 5;
cfg.vfs = 0.45;                  % Full-scale dynamic range [V]
cfg.vcm = 0.7;                   % Common-mode / center voltage [V]
cfg.fs = 500e6;                  % Sample rate [Hz]
cfg.nSamples = 1024;             % FFT-friendly record length
cfg.inputBin = 37;               % Coherent input bin
cfg.inputAmplitude = 0.95;       % Fraction of full-scale peak
cfg.outputDir = 'figures_matlab';

%% Asynchronous comparator timing model
cfg.tCmpNom = 124e-12;           % Nominal delay near 0.5 LSB [s]
cfg.tCmpMin = 60e-12;            % Minimum allowed decision time [s]
cfg.tCmpMax = 250e-12;           % Maximum allowed decision time [s]
cfg.dvRef = 0.5 * lsb_voltage(cfg.vfs, cfg.nBits);
cfg.dvFloor = 1e-3;              % Avoid singularity for tiny overdrive [V]

%% Generate coherent differential input around Vcm
n = 0:cfg.nSamples-1;
vin = cfg.vcm + cfg.inputAmplitude * (cfg.vfs / 2) * ...
    sin(2 * pi * cfg.inputBin * n / cfg.nSamples);

%% Preallocate outputs
codes = zeros(1, cfg.nSamples);
vout = zeros(1, cfg.nSamples);
convTime = zeros(1, cfg.nSamples);
bitHistory = zeros(cfg.nSamples, cfg.nBits);
bitEventTime = zeros(cfg.nSamples, cfg.nBits);

%% SAR conversion loop
for sampleIdx = 1:cfg.nSamples
    code = 0;
    tAccum = 0;

    for bitPos = cfg.nBits-1:-1:0
        trialCode = bitor(code, bitshift(1, bitPos));
        vdac = dac_voltage(trialCode, cfg.nBits, cfg.vfs, cfg.vcm);

        comparatorHigh = vin(sampleIdx) >= vdac;
        overdrive = abs(vin(sampleIdx) - vdac);
        tCmp = comparator_delay(overdrive, cfg);
        tAccum = tAccum + tCmp;

        if comparatorHigh
            code = trialCode;
        end

        histCol = cfg.nBits - bitPos;
        bitHistory(sampleIdx, histCol) = bitget(code, bitPos + 1);
        bitEventTime(sampleIdx, histCol) = tAccum;
    end

    codes(sampleIdx) = code;
    vout(sampleIdx) = dac_voltage(code, cfg.nBits, cfg.vfs, cfg.vcm);
    convTime(sampleIdx) = tAccum;
end

%% Dynamic performance metrics
[sndrDb, enob, fftDb, freqAxis] = calc_sndr_enob(codes, cfg.nBits, cfg.fs);

%% Console summary
fprintf('5-bit async SAR ADC MATLAB behavioral model\n');
fprintf('LSB                 : %.3f mV\n', 1e3 * lsb_voltage(cfg.vfs, cfg.nBits));
fprintf('Average conv. time  : %.1f ps\n', 1e12 * mean(convTime));
fprintf('Worst-case conv. time: %.1f ps\n', 1e12 * max(convTime));
fprintf('SNDR                : %.2f dB\n', sndrDb);
fprintf('ENOB                : %.2f bits\n', enob);

if ~exist(cfg.outputDir, 'dir')
    mkdir(cfg.outputDir);
end

%% Plots
sampleWindow = 16;
timeNs = (0:sampleWindow-1) / cfg.fs * 1e9;

fig1 = figure('Name', 'ADC Input and Output');
plot(timeNs, vin(1:sampleWindow), 'LineWidth', 1.5);
hold on;
stairs(timeNs, vout(1:sampleWindow), 'LineWidth', 1.2);
grid on;
xlabel('Time [ns]');
ylabel('Voltage [V]');
legend('Input', 'Quantized output', 'Location', 'best');
title('Input Signal and Quantized Output');
save_figure(fig1, cfg.outputDir, 'input_output');

fig2 = figure('Name', 'SAR Bit Decisions');
imagesc(1:sampleWindow, 1:cfg.nBits, bitHistory(1:sampleWindow, :).');
colormap(flipud(gray));
colorbar('Ticks', [0, 1], 'TickLabels', {'0', '1'});
xlabel('Sample index');
ylabel('Decision number');
yticks(1:cfg.nBits);
yticklabels({'Bit 4', 'Bit 3', 'Bit 2', 'Bit 1', 'Bit 0'});
title('Bit Values After Each Asynchronous Decision');
save_figure(fig2, cfg.outputDir, 'bit_decisions');

fig3 = figure('Name', 'Bit Decision Timing');
plot(1:sampleWindow, 1e12 * bitEventTime(1:sampleWindow, :), 'LineWidth', 1.2);
grid on;
xlabel('Sample index');
ylabel('Decision time [ps]');
legend('Bit 4', 'Bit 3', 'Bit 2', 'Bit 1', 'Bit 0', 'Location', 'northwest');
title('Per-Bit Ready Events');
save_figure(fig3, cfg.outputDir, 'bit_timing');

fig4 = figure('Name', 'Conversion Time Histogram');
histogram(1e12 * convTime, 20);
grid on;
xlabel('Total conversion time [ps]');
ylabel('Count');
title('Asynchronous Conversion Time Distribution');
save_figure(fig4, cfg.outputDir, 'conversion_time_histogram');

fig5 = figure('Name', 'Output Spectrum');
plot(freqAxis / 1e6, fftDb, 'LineWidth', 1.2);
grid on;
xlabel('Frequency [MHz]');
ylabel('Magnitude [dBFS]');
title(sprintf('Output Spectrum, SNDR = %.2f dB, ENOB = %.2f bits', sndrDb, enob));
xlim([0, cfg.fs / 2 / 1e6]);
save_figure(fig5, cfg.outputDir, 'output_spectrum');

%% Local functions
function lsb = lsb_voltage(vfs, nBits)
    lsb = vfs / (2^nBits);
end

function v = dac_voltage(code, nBits, vfs, vcm)
    v = vcm - vfs / 2 + vfs * double(code) / (2^nBits);
end

function tCmp = comparator_delay(overdrive, cfg)
    scaledDelay = cfg.tCmpNom * (cfg.dvRef / max(overdrive, cfg.dvFloor));
    tCmp = min(max(scaledDelay, cfg.tCmpMin), cfg.tCmpMax);
end

function [sndrDb, enob, spectrumDb, freqAxis] = calc_sndr_enob(codes, nBits, fs)
    x = double(codes(:));
    x = x - mean(x);
    x = x / (2^(nBits - 1));

    n = length(x);
    win = 0.5 - 0.5 * cos(2 * pi * (0:n-1)' / (n - 1));
    coherentGain = sum(win) / n;
    xw = x .* win;

    spectrum = fft(xw);
    mag = abs(spectrum(1:n/2+1)) / (n * coherentGain);
    powerBins = mag .^ 2;
    powerBins(2:end-1) = 2 * powerBins(2:end-1);

    signalBin = find_max_bin(powerBins);
    signalBins = max(signalBin - 1, 2):min(signalBin + 1, length(powerBins));

    signalPower = sum(powerBins(signalBins));
    noiseDistPower = sum(powerBins(2:end)) - signalPower;

    sndrDb = 10 * log10(signalPower / noiseDistPower);
    enob = (sndrDb - 1.76) / 6.02;

    spectrumDb = 10 * log10(max(powerBins, 1e-20));
    freqAxis = (0:n/2) * fs / n;
end

function idx = find_max_bin(powerBins)
    [~, idx] = max(powerBins(2:end));
    idx = idx + 1;
end

function save_figure(figHandle, outputDir, baseName)
    pngPath = fullfile(outputDir, [baseName, '.png']);
    figPath = fullfile(outputDir, [baseName, '.fig']);
    saveas(figHandle, pngPath);
    savefig(figHandle, figPath);
end
