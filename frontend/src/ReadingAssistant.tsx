import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import CloseIcon from '@mui/icons-material/Close';
import RestartAltIcon from '@mui/icons-material/RestartAlt';
import IconButton from '@mui/material/IconButton';
import { useEffect, useState } from 'react';

import { AssistantChat } from './AssistantChat';
import styles from './Assistant.module.scss';
import type { Reading } from './reading.models';

interface Props {
  reading: Reading | null;
}

/** Floating “Ask with AI” control and slide-over panel. */
export function ReadingAssistant({ reading }: Props) {
  const [open, setOpen] = useState(false);
  const [chatKey, setChatKey] = useState(0);

  useEffect(() => {
    if (!open) {
      return;
    }

    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setOpen(false);
      }
    };

    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open]);

  return (
    <>
      {!open && (
        <button
          type="button"
          className={styles.fab}
          onClick={() => setOpen(true)}
          aria-label="Ask with AI"
        >
          <AutoAwesomeIcon />
          <span>Ask with AI</span>
        </button>
      )}

      {open && (
        <>
          <button
            type="button"
            className={styles.backdrop}
            aria-label="Close assistant"
            onClick={() => setOpen(false)}
          />

          <aside className={styles.panel} role="dialog" aria-label="Reading assistant">
            <header className={styles.panelHead}>
              <div className={styles.panelTitle}>
                <span className={styles.panelIcon}>
                  <AutoAwesomeIcon fontSize="small" />
                </span>
                <div>
                  <h2>Reading assistant</h2>
                  <p>Grounded in your latest calculation</p>
                </div>
              </div>
              <div className={styles.panelActions}>
                <IconButton
                  size="small"
                  aria-label="New conversation"
                  onClick={() => setChatKey((k) => k + 1)}
                >
                  <RestartAltIcon fontSize="small" />
                </IconButton>
                <IconButton size="small" aria-label="Close" onClick={() => setOpen(false)}>
                  <CloseIcon fontSize="small" />
                </IconButton>
              </div>
            </header>

            <div className={styles.panelBody}>
              <AssistantChat
                key={`${chatKey}-${reading?.full_name ?? 'none'}-${reading?.date_of_birth ?? ''}`}
                reading={reading}
              />
            </div>
          </aside>
        </>
      )}
    </>
  );
}
