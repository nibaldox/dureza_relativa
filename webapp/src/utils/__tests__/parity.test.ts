import { describe, expect, it } from 'vitest';

import { classifyDuration, hardnessIndex } from '../dataProcessor';
import cases from './fixtures/classification_cases.json';

type ParityCase = {
  input: number;
  expected_dureza: string;
  expected_indice_dureza: number;
  comment?: string;
};

describe('classification_cases.json parity', () => {
  it('loads a non-empty fixture (symlink alive)', () => {
    expect(Array.isArray(cases.cases)).toBe(true);
    expect(cases.cases.length).toBeGreaterThan(0);
  });

  it('contains a sentinel-marked case (proves JSON, not hardcoded)', () => {
    const hasSentinel = (cases.cases as ParityCase[]).some((c) =>
      (c.comment ?? '').toLowerCase().includes('sentinel'),
    );
    expect(hasSentinel).toBe(true);
  });

  it('matches the known 0.0 -> roca suave / 0.0 sentinel', () => {
    const zero = (cases.cases as ParityCase[]).find((c) => c.input === 0.0);
    expect(zero).toBeDefined();
    expect(zero!.expected_dureza).toBe('roca suave');
    expect(zero!.expected_indice_dureza).toBe(0.0);
  });
});

describe('classifyDuration parity', () => {
  it.each(cases.cases as ParityCase[])('case[$comment] input=$input', (c) => {
    const actual = classifyDuration(c.input);
    expect(actual).toBe(c.expected_dureza);
  });
});

describe('hardnessIndex parity', () => {
  // Float tolerance: 1e-9 mirrors Python pytest.approx(abs=1e-9) in test_parity.py.
  it.each(cases.cases as ParityCase[])(
    'case[$comment] input=$input expected=$expected_indice_dureza',
    (c) => {
      const actual = hardnessIndex(c.input);
      expect(
        Math.abs(actual - c.expected_indice_dureza),
        `case[${c.comment}] input=${c.input} expected=${c.expected_indice_dureza} actual=${actual}`,
      ).toBeLessThan(1e-9);
    },
  );
});