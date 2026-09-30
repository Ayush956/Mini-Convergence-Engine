import { useCallback, useEffect, useRef, useState } from 'react';

import styles from './App.module.scss';
import { BirthForm } from './BirthForm';
import { Convergence } from './Convergence';
import { MethodCards } from './MethodCards';
import { ScoreMatrix } from './ScoreMatrix';
import { ReadingAssistant } from './ReadingAssistant';
import { Skeleton } from './Skeleton';
import { ThemeToggle } from './ThemeToggle';
import { getReading } from './reading.api';
import type { ApiError, Reading, ReadingRequest } from './reading.models';

/**
 * How long a wait may run before we explain it. A warm backend answers in
 * well under a second; anything past this is an instance waking from idle,
 * and silence there reads as a hang.
 */
const SLOW_AFTER_MS = 6000;
const MOBILE_QUERY = '(max-width: 40rem)';

function isMobileScreen(): boolean {
  return typeof window !== 'undefined' && window.matchMedia(MOBILE_QUERY).matches;
}

export function App() {
  const [reading, setReading] = useState<Reading | null>(null);
  const [busy, setBusy] = useState(false);
  const [slow, setSlow] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isMobile, setIsMobile] = useState(isMobileScreen);
  // Closed until the user opens Ask with AI — desktop and phone alike.
  const [assistantOpen, setAssistantOpen] = useState(false);
  const resultPanel = useRef<HTMLElement | null>(null);
  const slowTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  const settle = () => {
    clearTimeout(slowTimer.current);
    setBusy(false);
    setSlow(false);
  };

  const run = useCallback(async (request: ReadingRequest) => {
    setBusy(true);
    setError(null);
    // Cleared so the new request replaces the old reading rather than sitting
    // underneath it, which would leave two answers on screen at once.
    setReading(null);
    setSlow(false);
    clearTimeout(slowTimer.current);
    slowTimer.current = setTimeout(() => setSlow(true), SLOW_AFTER_MS);

    try {
      setReading(await getReading(request));
    } catch (failure) {
      setError((failure as ApiError).message);
    } finally {
      settle();
    }
  }, []);

  // The result lands below the fold on a laptop, so bring it into view once
  // the panel actually exists.
  useEffect(() => {
    if (reading) {
      resultPanel.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, [reading]);

  useEffect(() => () => clearTimeout(slowTimer.current), []);

  useEffect(() => {
    const media = window.matchMedia(MOBILE_QUERY);
    const sync = () => setIsMobile(media.matches);
    sync();
    media.addEventListener('change', sync);
    return () => media.removeEventListener('change', sync);
  }, []);

  useEffect(() => {
    if (!(isMobile && assistantOpen)) {
      return;
    }
    const previous = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = previous;
    };
  }, [isMobile, assistantOpen]);

  const pageClass = assistantOpen
    ? isMobile
      ? styles.pageMobileChat
      : styles.pageSplit
    : styles.pageCentered;
  const intakeFocus = assistantOpen && !isMobile && !reading && !busy;

  return (
    <div className={`${styles.page} ${pageClass}`}>
      <div className={styles.chakra} aria-hidden />
      <main className={`${styles.main} ${intakeFocus ? styles.mainIntake : ''}`}>
        <div className={intakeFocus ? styles.intakeWrap : undefined}>
          <header className={`${styles.masthead} ${intakeFocus ? styles.mastheadIntake : ''}`}>
            <p className={styles.eyebrow}>Mini Convergence Engine</p>
            <h1>Five systems, one birth record.</h1>
            <p className={styles.tagline}>
              A sun sign, a Chinese animal, two numerology numbers and a Vedic weekday are
              calculated independently, scored against six traits, and measured for where they
              agree.
            </p>
          </header>

          <section
            className={`${styles.panel} ${intakeFocus ? `${styles.intakePanel} ${styles.panelGlow}` : ''}`}
          >
            <BirthForm busy={busy} serverError={error} onSubmit={run} expanded={intakeFocus} />
          </section>
        </div>

        {busy && (
          <section className={styles.panel}>
            <Skeleton slow={slow} />
          </section>
        )}

        {reading && (
          <section className={`${styles.panel} ${styles.result}`} ref={resultPanel}>
            <header className={styles.resultHead}>
              <div>
                <h2>{reading.full_name}</h2>
                <p className={styles.subject}>
                  Born {reading.date_of_birth} at {reading.time_of_birth}
                </p>
              </div>
              <button
                type="button"
                className={styles.link}
                onClick={() => {
                  setReading(null);
                  setError(null);
                }}
              >
                Start over
              </button>
            </header>

            <MethodCards methods={reading.methods} />

            <section className={styles.block}>
              <h3 className={styles.blockTitle}>The score matrix</h3>
              <ScoreMatrix methods={reading.methods} traits={reading.traits} />
            </section>

            <section className={styles.block}>
              <h3 className={styles.blockTitle}>Where the systems converge</h3>
              <Convergence methods={reading.methods} traits={reading.traits} />
            </section>

            <section className={styles.block}>
              <h3 className={styles.blockTitle}>
                In plain language
                <span
                  className={`${styles.source} ${
                    reading.summary_source === 'template' ? styles.fromTemplate : ''
                  }`}
                >
                  {reading.summary_source === 'model'
                    ? 'written by the model'
                    : 'model unavailable, written from the template'}
                </span>
              </h3>
              <p className={styles.summary}>{reading.summary}</p>
            </section>

            {reading.assumptions.length > 0 && (
              <aside className={styles.assumptions}>
                <h3>Assumptions applied to this reading</h3>
                <ul>
                  {reading.assumptions.map((assumption) => (
                    <li key={assumption}>{assumption}</li>
                  ))}
                </ul>
              </aside>
            )}
          </section>
        )}

        <footer className={styles.siteFooter}>
          <p className={styles.footerEyebrow}>The five systems</p>
          <p className={styles.footerLead}>
            Each tradition is calculated on its own from the same birth record, then scored on
            the same six traits so we can see where they happen to agree.
          </p>
          <ul className={styles.footerSystems}>
            <li>
              <span className={styles.footerIndex} aria-hidden>
                01
              </span>
              <strong>Western sun sign</strong>
              <span>Tropical ecliptic longitude — where the Sun stood at that moment.</span>
            </li>
            <li>
              <span className={styles.footerIndex} aria-hidden>
                02
              </span>
              <strong>Chinese zodiac</strong>
              <span>Animal of the lunar year, using published New Year dates, not 1 January.</span>
            </li>
            <li>
              <span className={styles.footerIndex} aria-hidden>
                03
              </span>
              <strong>Life path</strong>
              <span>Pythagorean reduction of the date, keeping master numbers 11, 22 and 33.</span>
            </li>
            <li>
              <span className={styles.footerIndex} aria-hidden>
                04
              </span>
              <strong>Chaldean name number</strong>
              <span>Cheiro’s letter table on the name as entered, reduced to one digit.</span>
            </li>
            <li>
              <span className={styles.footerIndex} aria-hidden>
                05
              </span>
              <strong>Vedic vara</strong>
              <span>Weekday lord from sunrise to sunrise; 06:00 IST stands in for true dawn.</span>
            </li>
          </ul>
          <p className={styles.footerEyebrow}>The six traits</p>
          <p className={styles.footerLead}>
            Every method is scored 0–10 on the same six dimensions. A score of 7 or above
            counts as agreement when we measure convergence.
          </p>
          <ul className={styles.footerTraits}>
            <li>
              <strong>Leadership</strong>
              <span>Initiative, authority, and the will to take the first step.</span>
            </li>
            <li>
              <strong>Creativity</strong>
              <span>Invention, display, and how freely a result wants to make something new.</span>
            </li>
            <li>
              <strong>Emotional depth</strong>
              <span>Feeling, intuition, and how much inner weather the tradition assigns.</span>
            </li>
            <li>
              <strong>Communication</strong>
              <span>Speech, sociability, and the Mercury-like gift of putting things into words.</span>
            </li>
            <li>
              <strong>Discipline</strong>
              <span>Structure, persistence, and the earthy habit of finishing what was started.</span>
            </li>
            <li>
              <strong>Risk appetite</strong>
              <span>How far a result will go — impulse, extremes, or a careful refusal.</span>
            </li>
          </ul>
          <p className={styles.footerNote}>
            This is a comparison of five mappings, not a prediction. Time is treated as IST
            because the brief never asks for a birthplace.
          </p>
        </footer>
      </main>

      {assistantOpen ? (
        <>
          {!isMobile && (
            <div className={styles.themeOnSplit}>
              <ThemeToggle />
            </div>
          )}
          <div
            className={`${styles.rightColumn} ${isMobile ? styles.rightColumnFullscreen : ''}`}
          >
            <ReadingAssistant reading={reading} open onOpenChange={setAssistantOpen} />
          </div>
        </>
      ) : (
        <>
          <div className={styles.themeBarFixed}>
            <ThemeToggle />
          </div>
          <ReadingAssistant reading={reading} open={false} onOpenChange={setAssistantOpen} />
        </>
      )}
    </div>
  );
}
