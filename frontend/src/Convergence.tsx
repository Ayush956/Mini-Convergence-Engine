import { useMemo } from 'react';

import styles from './Convergence.module.scss';
import { CountUp } from './CountUp';
import {
  AGREEMENT_THRESHOLD,
  METHOD_COUNT,
  type MethodResult,
  type TraitRow,
} from './reading.models';

interface Props {
  methods: MethodResult[];
  traits: TraitRow[];
}

export function Convergence({ methods, traits }: Props) {
  const rows = useMemo(() => {
    const order = methods.map((method) => method.id);
    const labels = new Map(methods.map((method) => [method.id, method.label]));

    return traits.map((trait) => ({
      trait: trait.trait,
      n: trait.n,
      percent: trait.confidence * 100,
      // Listed in the matrix's column order, so a reader can verify a figure
      // by scanning left to right instead of hunting for each name.
      agreeing: [...trait.agreeing]
        .sort((a, b) => order.indexOf(a) - order.indexOf(b))
        .map((id) => labels.get(id) ?? id),
      pips: Array.from({ length: METHOD_COUNT }, (_, i) => i < trait.n),
    }));
  }, [methods, traits]);

  /**
   * The headline. Six traits over five methods makes ties the normal case, so
   * this names every trait holding the top N rather than picking one.
   */
  const strongest = useMemo(() => {
    if (rows.length === 0) {
      return null;
    }

    const best = Math.max(...rows.map((row) => row.n));
    const tied = rows.filter((row) => row.n === best);

    return { n: best, percent: tied[0]!.percent, traits: tied.map((row) => row.trait) };
  }, [rows]);

  return (
    <>
      {strongest && (
        <p className={styles.headline}>
          {strongest.n === 0 ? (
            'No trait reached the agreement threshold on any method.'
          ) : (
            <>
              Strongest agreement on <strong>{strongest.traits.join(', ')}</strong> &mdash;{' '}
              {strongest.n} of {METHOD_COUNT} methods, giving{' '}
              <strong>
                <CountUp value={strongest.percent} decimals={1} suffix="%" />
              </strong>{' '}
              confidence.
            </>
          )}
        </p>
      )}

      <ul className={styles.rows}>
        {rows.map((row, i) => (
          <li
            className={styles.row}
            key={row.trait}
            style={{ '--delay': `${i * 70}ms` } as React.CSSProperties}
          >
            <div className={styles.label}>
              <span className={styles.trait}>{row.trait}</span>
              <span
                className={styles.pips}
                aria-label={`${row.n} of ${METHOD_COUNT} methods agree`}
              >
                {row.pips.map((filled, pip) => (
                  <span
                    key={pip}
                    className={`${styles.pip} ${filled ? styles.on : ''}`}
                  />
                ))}
              </span>
            </div>

            <div className={styles.meter}>
              <span
                className={`${styles.meterFill} ${row.n === 0 ? styles.none : ''}`}
                style={
                  {
                    '--fill': `${row.percent}%`,
                    '--delay': `${i * 70 + 120}ms`,
                  } as React.CSSProperties
                }
              />
            </div>

            <p className={styles.figure}>
              <span className={styles.percent}>
                <CountUp value={row.percent} decimals={1} suffix="%" delayMs={i * 70 + 120} />
              </span>
              <span className={styles.n}>N = {row.n}</span>
            </p>

            <p className={styles.who}>
              {row.agreeing.length > 0
                ? `Agreeing: ${row.agreeing.join(', ')}`
                : `Nothing scored this ${AGREEMENT_THRESHOLD} or above`}
            </p>
          </li>
        ))}
      </ul>

      <p className={styles.formula}>
        Confidence is the brief&rsquo;s formula, 1 &minus; 1/2<sup>N</sup>, where N counts the
        methods scoring that trait {AGREEMENT_THRESHOLD} or above. It rises 0, 50, 75, 87.5, 93.75,
        96.875 per cent as N goes 0 to 5.
      </p>
    </>
  );
}
