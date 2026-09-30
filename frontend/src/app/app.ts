import {
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  OnDestroy,
  inject,
  signal,
  viewChild,
} from '@angular/core';

import { BirthForm } from './birth-form/birth-form';
import { Convergence } from './convergence/convergence';
import { MethodCards } from './method-cards/method-cards';
import { Reading, ReadingRequest } from './reading.models';
import { ReadingService } from './reading.service';
import { ScoreMatrix } from './score-matrix/score-matrix';
import { Skeleton } from './skeleton/skeleton';

/**
 * How long a wait may run before we explain it. A warm backend answers in
 * well under a second; anything past this is an instance waking from idle,
 * and silence there reads as a hang.
 */
const SLOW_AFTER_MS = 6000;

@Component({
  selector: 'app-root',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [BirthForm, Convergence, MethodCards, ScoreMatrix, Skeleton],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App implements OnDestroy {
  private readonly service = inject(ReadingService);
  private readonly resultPanel =
    viewChild<ElementRef<HTMLElement>>('resultPanel');

  readonly reading = signal<Reading | null>(null);
  readonly busy = signal(false);
  readonly slow = signal(false);
  readonly error = signal<string | null>(null);

  private slowTimer?: ReturnType<typeof setTimeout>;

  run(request: ReadingRequest): void {
    this.busy.set(true);
    this.error.set(null);
    // Cleared so the skeleton replaces the old reading rather than sitting
    // underneath it, which would leave two answers on screen at once.
    this.reading.set(null);
    this.startSlowTimer();

    this.service.getReading(request).subscribe({
      next: (reading) => {
        this.settle();
        this.reading.set(reading);
        this.revealResult();
      },
      error: (failure: { message: string }) => {
        this.settle();
        this.error.set(failure.message);
      },
    });
  }

  reset(): void {
    this.settle();
    this.reading.set(null);
    this.error.set(null);
  }

  ngOnDestroy(): void {
    clearTimeout(this.slowTimer);
  }

  private startSlowTimer(): void {
    clearTimeout(this.slowTimer);
    this.slow.set(false);
    this.slowTimer = setTimeout(() => this.slow.set(true), SLOW_AFTER_MS);
  }

  private settle(): void {
    clearTimeout(this.slowTimer);
    this.busy.set(false);
    this.slow.set(false);
  }

  /**
   * The result lands below the fold on a laptop, so bring it into view. Done
   * on a macrotask because the panel does not exist until this render has
   * flushed.
   */
  private revealResult(): void {
    setTimeout(() => {
      this.resultPanel()?.nativeElement.scrollIntoView({
        behavior: 'smooth',
        block: 'start',
      });
    });
  }
}
