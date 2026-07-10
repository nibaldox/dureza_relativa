import { describe, expect, it } from 'vitest';

import { classifyDuration, hardnessIndex } from '../dataProcessor';

const classifyBoundaries: Array<[number, 'roca suave' | 'roca media' | 'roca dura' | 'roca muy dura']> = [
  [15.999, 'roca suave'],
  [16.0, 'roca media'],
  [23.999, 'roca media'],
  [24.0, 'roca dura'],
  [39.999, 'roca dura'],
  [40.0, 'roca muy dura'],
  [60.0, 'roca muy dura'],
  [61.0, 'roca muy dura'],
];

describe('classifyDuration', () => {
  it.each(classifyBoundaries)('classifies %s minutes as %s', (minutes, expected) => {
    expect(classifyDuration(minutes)).toBe(expected);
  });
});

const hardnessSegments: Array<[number, number]> = [
  [0.0, 0.0],
  [8.0, 12.5],
  [15.999, 24.9984375],
  [16.0, 25.0],
  [20.0, 37.5],
  [23.999, 49.996875],
  [24.0, 50.0],
  [32.0, 62.5],
  [39.999, 74.9984375],
  [40.0, 75.0],
  [50.0, 87.5],
  [59.999, 99.99875],
  [60.0, 100.0],
  [61.0, 100.0],
];

describe('hardnessIndex', () => {
  // Float tolerance: 1e-9 mirrors the Python pytest.approx(abs=1e-9).
  it.each(hardnessSegments)('maps %s minutes to %s within 1e-9', (minutes, expected) => {
    expect(Math.abs(hardnessIndex(minutes) - expected)).toBeLessThan(1e-9);
  });

  it('clamps negative inputs to zero', () => {
    expect(hardnessIndex(-1.0)).toBe(0);
    expect(hardnessIndex(-999.0)).toBe(0);
  });
});