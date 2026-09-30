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
        this.render(target);
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
      this.render(target * eased);

      if (progress < 1) {
        this.frame = requestAnimationFrame(step);
      }
    };

    this.frame = requestAnimationFrame(step);
  }

  private render(value: number): void {
    this.host.nativeElement.textContent =
      value.toFixed(this.decimals()) + this.suffix();
  }

  private stop(): void {
    cancelAnimationFrame(this.frame);
    clearTimeout(this.timer);
  }
}
