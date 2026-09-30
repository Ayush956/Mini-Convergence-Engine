import CheckIcon from '@mui/icons-material/Check';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import CircularProgress from '@mui/material/CircularProgress';
import { useState } from 'react';

import styles from './Assistant.module.scss';

export type ThinkingPhase = 'idle' | 'reading_context' | 'calling_model' | 'generating';

const STEPS: { id: ThinkingPhase; label: string; detail: string }[] = [
  {
    id: 'reading_context',
    label: 'Reading your results…',
    detail: 'Loading the five method outputs, the score matrix, and convergence figures.',
  },
  {
    id: 'calling_model',
    label: 'Sending to the model…',
    detail: 'Your question goes out with the full reading so nothing is invented.',
  },
  {
    id: 'generating',
    label: 'Composing an answer…',
    detail: 'Writing a plain-language reply grounded in the numbers on screen.',
  },
];

const ORDER: ThinkingPhase[] = ['reading_context', 'calling_model', 'generating'];

function phaseIndex(phase: ThinkingPhase): number {
  return ORDER.indexOf(phase);
}

interface Props {
  elapsedSeconds: number;
  phase?: ThinkingPhase;
  completed?: boolean;
  defaultExpanded?: boolean;
}

export function AssistantThinkingPanel({
  elapsedSeconds,
  phase = 'generating',
  completed = false,
  defaultExpanded,
}: Props) {
  const [expanded, setExpanded] = useState(defaultExpanded ?? !completed);

  if (!completed && phase === 'idle') {
    return null;
  }

  const currentIndex = completed ? ORDER.length : phaseIndex(phase);

  return (
    <div className={styles.thinking}>
      <button
        type="button"
        className={styles.thinkingHead}
        onClick={() => setExpanded((open) => !open)}
      >
        <AutoAwesomeIcon fontSize="small" />
        <span className={styles.thinkingTitle}>
          {completed || phase === 'generating'
            ? `Thought for ${elapsedSeconds}s`
            : `Thinking… ${elapsedSeconds}s`}
        </span>
        <span className={styles.thinkingBadge}>Convergence AI</span>
        <span className={styles.thinkingSteps}>3 steps</span>
        {expanded ? <ExpandLessIcon fontSize="small" /> : <ExpandMoreIcon fontSize="small" />}
      </button>

      {expanded && (
        <div className={styles.thinkingBody}>
          {STEPS.map((step) => {
            const stepIndex = phaseIndex(step.id);
            const isComplete = completed || currentIndex > stepIndex;
            const isActive = !completed && currentIndex === stepIndex;
            const isPending = !completed && currentIndex < stepIndex;

            return (
              <div className={styles.thinkingRow} key={step.id}>
                <div className={styles.thinkingIcon}>
                  {isComplete ? (
                    <span className={styles.thinkingDone}>
                      <CheckIcon sx={{ fontSize: 14 }} />
                    </span>
                  ) : isActive ? (
                    <CircularProgress size={16} color="inherit" />
                  ) : (
                    <span className={styles.thinkingPending} />
                  )}
                </div>
                <div>
                  <p
                    className={`${styles.thinkingLabel} ${
                      isPending ? styles.muted : ''
                    } ${isActive ? styles.active : ''}`}
                  >
                    {step.label}
                  </p>
                  {(isActive || isComplete) && (
                    <p className={styles.thinkingDetail}>{step.detail}</p>
                  )}
                </div>
              </div>
            );
          })}

          <div className={styles.thinkingFooter}>
            <span className={styles.thinkingDone}>
              <CheckIcon sx={{ fontSize: 14 }} />
            </span>
            <span>{completed ? 'Ready' : 'Working…'}</span>
            <span className={styles.thinkingPill}>
              {completed ? 'Answer generated' : STEPS[Math.min(currentIndex, 2)]!.label.replace('…', '')}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
