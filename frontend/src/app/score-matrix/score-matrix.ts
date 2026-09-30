import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';

import {
  AGREEMENT_THRESHOLD,
  MAX_SCORE,
  MethodResult,
  TraitRow,
} from '../reading.models';

/** One cell of the matrix, pre-resolved so the template stays declarative. */
interface Cell {
  method: string;
  score: number;
  agrees: boolean;
  /** Bar width as a percentage of the 0-10 range. */
  fill: number;
}

interface Row {
  trait: string;
  cells: Cell[];
}

@Component({
  selector: 'app-score-matrix',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './score-matrix.html',
  styleUrl: './score-matrix.scss',
})
export class ScoreMatrix {
  readonly methods = input.required<MethodResult[]>();
  readonly traits = input.required<TraitRow[]>();

  readonly threshold = AGREEMENT_THRESHOLD;
  /** Where to draw the threshold marker inside each bar. */
  readonly thresholdPercent = (AGREEMENT_THRESHOLD / MAX_SCORE) * 100;

  readonly rows = computed<Row[]>(() =>
    this.traits().map((trait) => ({
      trait: trait.trait,
      cells: this.methods().map((method) => {
        const score = trait.scores[method.id] ?? 0;
        return {
          method: method.id,
          score,
          agrees: score >= AGREEMENT_THRESHOLD,
          fill: (score / MAX_SCORE) * 100,
        };
      }),
    })),
  );
}
