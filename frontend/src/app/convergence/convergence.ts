import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';

import { CountUp } from '../count-up';
import { AGREEMENT_THRESHOLD, MethodResult, TraitRow } from '../reading.models';

/** The brief's method count, and the denominator of N. */
const METHOD_COUNT = 5;

interface Row {
  trait: string;
  n: number;
  /** Confidence as a percentage, which is how it is read out. */
  percent: number;
  agreeing: string[];
  /** Filled pips, one per method, so N is countable without reading it. */
  pips: boolean[];
}

@Component({
  selector: 'app-convergence',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CountUp],
  templateUrl: './convergence.html',
  styleUrl: './convergence.scss',
})
export class Convergence {
  readonly methods = input.required<MethodResult[]>();
  readonly traits = input.required<TraitRow[]>();

  readonly methodCount = METHOD_COUNT;
  readonly threshold = AGREEMENT_THRESHOLD;

  readonly rows = computed<Row[]>(() => {
    const order = this.methods().map((method) => method.id);
    const labels = new Map(this.methods().map((m) => [m.id, m.label]));

    return this.traits().map((trait) => ({
      trait: trait.trait,
      n: trait.n,
      percent: trait.confidence * 100,
      // Listed in the matrix's column order, so a reader can check a claim by
      // scanning left to right rather than hunting for each name.
      agreeing: [...trait.agreeing]
        .sort((a, b) => order.indexOf(a) - order.indexOf(b))
        .map((id) => labels.get(id) ?? id),
      pips: Array.from({ length: METHOD_COUNT }, (_, i) => i < trait.n),
    }));
  });

  /**
   * The headline. Ties are common - six traits over five methods leaves
   * plenty of them - so this reports every trait holding the top N rather
   * than picking one arbitrarily.
   */
  readonly strongest = computed(() => {
    const rows = this.rows();
    if (!rows.length) {
      return null;
    }

    const best = Math.max(...rows.map((row) => row.n));
    const tied = rows.filter((row) => row.n === best);

    return {
      n: best,
      percent: tied[0].percent,
      traits: tied.map((row) => row.trait),
    };
  });
}
