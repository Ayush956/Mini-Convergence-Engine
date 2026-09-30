import { useEffect, useRef } from 'react';

/** Matches --duration-slow in styles.scss. */
const DURATION_MS = 420;

/** N = 5 gives 96.875 per cent, which is three decimals and no more. */
const MAX_DECIMALS = 3;

const prefersReducedMotion = () =>
  typeof matchMedia === 'function' && matchMedia('(prefers-reduced-motion: reduce)').matches;

interface Props {
  value: number;
  /** Precision held during the count, where a steady digit count reads best. */
  decimals?: number;
  suffix?: string;
  delayMs?: number;
}

/**
 * Counts from zero up to `value`.
 *
 * The number is written straight to the DOM from a rAF loop rather than held
 * in state. Six of these in a list would otherwise re-render the tree sixty
 * times a second for the sake of a digit ticking over.
 */
export function CountUp({ value, decimals = 0, suffix = '', delayMs = 0 }: Props) {
  const host = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    const node = host.current;
    if (!node) {
      return;
    }

    // The resting value is written exactly, with trailing zeros trimmed, so
    // the confidence ladder reads 50%, 87.5%, 96.875% rather than being padded
    // out to a uniform precision none of those numbers actually has.
    const settle = () => {
      node.textContent = String(Number(value.toFixed(MAX_DECIMALS))) + suffix;
    };

    if (prefersReducedMotion()) {
      settle();
      return;
    }

    node.textContent = (0).toFixed(decimals) + suffix;

    let frame = 0;
    const start = () => {
      const began = performance.now();

      const step = (now: number) => {
        const progress = Math.min((now - began) / DURATION_MS, 1);

        if (progress < 1) {
          // Matches --ease-out closely enough at this size, and needs no solver.
          const eased = 1 - Math.pow(1 - progress, 3);
          node.textContent = (value * eased).toFixed(decimals) + suffix;
          frame = requestAnimationFrame(step);
        } else {
          settle();
        }
      };

      frame = requestAnimationFrame(step);
    };

    const timer = setTimeout(start, delayMs);

    return () => {
      clearTimeout(timer);
      cancelAnimationFrame(frame);
    };
  }, [value, decimals, suffix, delayMs]);

  return <span ref={host} />;
}
