import {
  Directive,
  ElementRef,
  NgZone,
  OnDestroy,
  effect,
  inject,
  input,
} from '@angular/core';

/** Matches --duration-slow in styles.scss. */
const DURATION_MS = 420;

/** N = 5 gives 96.875 per cent, which is three decimals and no more. */
const MAX_DECIMALS = 3;

const prefersReducedMotion = () =>
  typeof matchMedia === 'function' &&
  matchMedia('(prefers-reduced-motion: reduce)').matches;

/**
 * Counts the host element's text from zero up to `appCountUp`.
 *
 * Writing textContent straight from a rAF loop keeps change detection out of
 * the animation entirely - otherwise a six-row list would run the whole tree
 * sixty times a second for the sake of a number ticking.
 */
@Directive({ selector: '[appCountUp]' })
export class CountUp implements OnDestroy {
  readonly value = input.required<number>({ alias: 'appCountUp' });
  /** Precision held during the count, where a steady digit count reads best. */
  readonly decimals = input(0);
  readonly suffix = input('');
  readonly delay = input(0);

  private readonly host = inject<ElementRef<HTMLElement>>(ElementRef);
  private readonly zone = inject(NgZone);
  private frame = 0;
  private timer?: ReturnType<typeof setTimeout>;

  constructor() {
    effect(() => {
      const target = this.value();
      this.stop();

      if (prefersReducedMotion()) {
        this.settle(target);
        return;
      }

      this.render(0);
      this.zone.runOutsideAngular(() => {
        this.timer = setTimeout(() => this.animate(target), this.delay());
      });
    });
  }

  ngOnDestroy(): void {
    this.stop();
  }

  private animate(target: number): void {
    const start = performance.now();

    const step = (now: number) => {
      const progress = Math.min((now - start) / DURATION_MS, 1);
      // Matches --ease-out closely enough at this size, and needs no solver.
      const eased = 1 - Math.pow(1 - progress, 3);

      if (progress < 1) {
        this.render(target * eased);
        this.frame = requestAnimationFrame(step);
      } else {
        this.settle(target);
      }
    };

    this.frame = requestAnimationFrame(step);
  }

  private render(value: number): void {
    this.write(value.toFixed(this.decimals()));
  }

  /**
   * The resting value is written exactly, with trailing zeros trimmed, so the
   * confidence ladder reads 50%, 87.5%, 96.875% rather than being padded out
   * to a uniform precision none of those numbers actually has.
   */
  private settle(value: number): void {
    this.write(String(Number(value.toFixed(MAX_DECIMALS))));
  }

  private write(text: string): void {
    this.host.nativeElement.textContent = text + this.suffix();
  }

  private stop(): void {
    cancelAnimationFrame(this.frame);
    clearTimeout(this.timer);
  }
}
