import { FILTER_HIGH_CUT_HZ, FILTER_LOW_CUT_HZ, N_MELS } from "../types/contract";

const F_SP = 200.0 / 3.0;
const MIN_LOG_HZ = 1000.0;
const MIN_LOG_MEL = MIN_LOG_HZ / F_SP; // 15.0
const LOGSTEP = Math.log(6.4) / 27.0;

/** Slaney mel scale (linear below 1 kHz, logarithmic above) - matching DSP engine. */
export function hzToMel(f: number): number {
  const safeF = Math.max(0, f);
  return safeF >= MIN_LOG_HZ
    ? MIN_LOG_MEL + Math.log(Math.max(safeF, 1e-9) / MIN_LOG_HZ) / LOGSTEP
    : safeF / F_SP;
}

export function melToHz(m: number): number {
  const safeM = Math.max(0, m);
  return safeM >= MIN_LOG_MEL
    ? MIN_LOG_HZ * Math.exp(LOGSTEP * (safeM - MIN_LOG_MEL))
    : F_SP * safeM;
}

const MEL_MIN = hzToMel(FILTER_LOW_CUT_HZ);
const MEL_MAX = hzToMel(FILTER_HIGH_CUT_HZ);

/** Converts frequency (Hz) to Mel bin index [0 .. N_MELS - 1]. */
export function hzToMelBin(hz: number): number {
  const mel = hzToMel(hz);
  const frac = (mel - MEL_MIN) / (MEL_MAX - MEL_MIN);
  return Math.min(N_MELS - 1, Math.max(0, Math.floor(frac * N_MELS)));
}

/** Computes the center frequency in Hz for a given Mel bin index [0 .. N_MELS - 1]. */
export function melBinCenterHz(bin: number): number {
  const mel = MEL_MIN + ((bin + 0.5) / N_MELS) * (MEL_MAX - MEL_MIN);
  return melToHz(mel);
}
