import { useCallback, useEffect, useRef, useState } from 'react';

import './App.scss';
import { BirthForm } from './BirthForm';
import { MethodCards } from './MethodCards';
import { getReading } from './reading.api';
import type { ApiError, Reading, ReadingRequest } from './reading.models';

export function App() {
  const [reading, setReading] = useState<Reading | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const resultPanel = useRef<HTMLElement | null>(null);

  const run = useCallback(async (request: ReadingRequest) => {
    setBusy(true);
    setError(null);
    // Cleared so the new request replaces the old reading rather than sitting
    // underneath it, which would leave two answers on screen at once.
    setReading(null);

    try {
      setReading(await getReading(request));
    } catch (failure) {
      setError((failure as ApiError).message);
    } finally {
      setBusy(false);
    }
  }, []);

  // The result lands below the fold on a laptop, so bring it into view once
  // the panel actually exists.
  useEffect(() => {
    if (reading) {
      resultPanel.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, [reading]);

  return (
    <main className="shell">
      <header className="masthead">
        <p className="eyebrow">Mini Convergence Engine</p>
        <h1>Five systems, one birth record.</h1>
        <p className="tagline">
          A sun sign, a Chinese animal, two numerology numbers and a Vedic weekday are calculated
          independently, scored against six traits, and measured for where they agree.
        </p>
      </header>

      <section className="panel">
        <BirthForm busy={busy} serverError={error} onSubmit={run} />
      </section>

      {reading && (
        <section className="panel result" ref={resultPanel}>
          <header className="result-head">
            <div>
              <h2>{reading.full_name}</h2>
              <p className="subject">
                Born {reading.date_of_birth} at {reading.time_of_birth}
              </p>
            </div>
            <button type="button" className="link" onClick={() => setReading(null)}>
              Start over
            </button>
          </header>

          <MethodCards methods={reading.methods} />
        </section>
      )}
    </main>
  );
}
