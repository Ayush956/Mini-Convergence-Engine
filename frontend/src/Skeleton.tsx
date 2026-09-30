import styles from './Skeleton.module.scss';
import { METHOD_COUNT } from './reading.models';

const CARDS = Array.from({ length: METHOD_COUNT }, (_, i) => i);
const ROWS = Array.from({ length: 6 }, (_, i) => i);

/** `slow` is set once the wait has run long enough to need explaining. */
export function Skeleton({ slow }: { slow: boolean }) {
  return (
    <div className={styles.skeleton} aria-busy="true" aria-live="polite">
      <p className={styles.status}>
        {slow
          ? 'Still working. The backend sleeps when idle on the free tier, and waking it can take up to a minute. Nothing has gone wrong.'
          : 'Calculating five systems and scoring six traits\u2026'}
      </p>

      <div className={styles.cards}>
        {CARDS.map((card) => (
          <div
            className={styles.card}
            key={card}
            style={{ '--delay': `${card * 90}ms` } as React.CSSProperties}
          >
            <span className={`${styles.line} ${styles.short}`} />
            <span className={`${styles.line} ${styles.tall}`} />
            <span className={styles.line} />
          </div>
        ))}
      </div>

      <div className={styles.grid}>
        {ROWS.map((row) => (
          <div
            className={styles.gridRow}
            key={row}
            style={{ '--delay': `${row * 70}ms` } as React.CSSProperties}
          >
            <span className={`${styles.line} ${styles.label}`} />
            {CARDS.map((cell) => (
              <span className={`${styles.line} ${styles.cell}`} key={cell} />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
