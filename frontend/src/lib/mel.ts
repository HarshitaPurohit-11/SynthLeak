import { FILTER_HIGH_CUT_HZ, FILTER_LOW_CUT_HZ, N_MELS } from "../types/contract";

export function hzToMel(hz: number): number {
  return 2595 * Math.log10(1 + Math.max(0, hz) / 700);
}

export function melToHz(mel: number): number {
  return 700 * (Math.pow(10, mel / 2595) - 1);
}

const MEL_MIN = hzToMel(FILTER_LOW_CUT_HZ);
const MEL_MAX = hzToMel(FILTER_HIGH_CUT_HZ);

export function hzToMelBin(hz: number): number {
  const m = hzToMel(hz);
  const frac = (m - MEL_MIN) / (MEL_MAX - MEL_MIN);
  const bin = Math.round(frac * (N_MELS - 1));
  return Math.max(0, Math.min(N_MELS - 1, bin));
}

export function melBinCenterHz(bin: number): number {
  const frac = Math.max(0, Math.min(N_MELS - 1, bin)) / (N_MELS - 1);
  const m = MEL_MIN + frac * (MEL_MAX - MEL_MIN);
  return melToHz(m);
}

