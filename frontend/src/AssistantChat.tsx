import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import BarChartIcon from '@mui/icons-material/BarChart';
import HelpOutlineIcon from '@mui/icons-material/HelpOutlineOutlined';
import PsychologyIcon from '@mui/icons-material/Psychology';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import IconButton from '@mui/material/IconButton';
import TextField from '@mui/material/TextField';
import { type FormEvent, useCallback, useEffect, useRef, useState } from 'react';

import styles from './Assistant.module.scss';
import { AssistantThinkingPanel, type ThinkingPhase } from './AssistantThinkingPanel';
import { sendChatMessage, type ChatTurn } from './chat.api';
import type { ApiError, Reading } from './reading.models';

const SUGGESTION_ICONS = [TrendingUpIcon, HelpOutlineIcon, PsychologyIcon, BarChartIcon];

const PHASE_ORDER: ThinkingPhase[] = ['reading_context', 'calling_model', 'generating'];

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  thinkingSeconds?: number;
}

interface Props {
  reading: Reading | null;
}

function suggestionsFor(reading: Reading | null): string[] {
  if (!reading) {
    return [
      'What does N mean in the convergence section?',
      'How are trait scores decided?',
      'What are the five systems this app runs?',
      'What will I see after I click Run the five systems?',
    ];
  }

  const top = [...reading.traits].sort((a, b) => b.n - a.n)[0];
  const weak = [...reading.traits].sort((a, b) => a.n - b.n)[0];

  return [
    `Why is ${top?.trait ?? 'this trait'} the strongest convergence on this reading?`,
    `Explain the ${weak?.trait ?? 'weakest'} trait — why do the systems disagree?`,
    'Walk me through one method’s scores in plain language.',
    'Is this reading saying anything about my personality?',
  ];
}

export function AssistantChat({ reading }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [thinkingPhase, setThinkingPhase] = useState<ThinkingPhase>('idle');
  const [thinkingSeconds, setThinkingSeconds] = useState(0);
  const endRef = useRef<HTMLDivElement>(null);
  const phaseTimer = useRef<ReturnType<typeof setInterval> | undefined>(undefined);
  const elapsedTimer = useRef<ReturnType<typeof setInterval> | undefined>(undefined);
  const elapsedRef = useRef(0);

  const showHero = messages.length === 0 && !busy;

  const clearTimers = () => {
    clearInterval(phaseTimer.current);
    clearInterval(elapsedTimer.current);
  };

  const startThinking = () => {
    setThinkingPhase('reading_context');
    elapsedRef.current = 0;
    setThinkingSeconds(0);
    clearTimers();
    elapsedTimer.current = setInterval(() => {
      elapsedRef.current += 1;
      setThinkingSeconds(elapsedRef.current);
    }, 1000);
    let step = 0;
    phaseTimer.current = setInterval(() => {
      step += 1;
      setThinkingPhase(PHASE_ORDER[Math.min(step, PHASE_ORDER.length - 1)]!);
    }, 1800);
  };

  const stopThinking = () => {
    clearTimers();
    setThinkingPhase('idle');
  };

  const scrollToBottom = useCallback(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, busy, thinkingPhase, scrollToBottom]);

  useEffect(() => () => clearTimers(), []);

  const submit = async (prompt: string) => {
    const trimmed = prompt.trim();
    if (!trimmed || busy) {
      return;
    }

    setError(null);
    setInput('');
    const userMsg: Message = { id: `u-${Date.now()}`, role: 'user', content: trimmed };
    setMessages((prev) => [...prev, userMsg]);
    setBusy(true);
    startThinking();

    const history: ChatTurn[] = messages.map((m) => ({
      role: m.role,
      content: m.content,
    }));

    try {
      const response = await sendChatMessage(trimmed, reading, history);
      const seconds = elapsedRef.current;
      stopThinking();
      setMessages((prev) => [
        ...prev,
        {
          id: `a-${Date.now()}`,
          role: 'assistant',
          content: response.reply,
          thinkingSeconds: seconds,
        },
      ]);
    } catch (failure) {
      stopThinking();
      setError((failure as ApiError).message);
    } finally {
      setBusy(false);
    }
  };

  const onSubmit = (event: FormEvent) => {
    event.preventDefault();
    void submit(input);
  };

  const suggestions = suggestionsFor(reading);

  return (
    <div className={styles.chat}>
      {showHero ? (
        <div className={styles.hero}>
          <div className={styles.heroIcon}>
            <span className={styles.heroGlow} />
            <span className={styles.heroBadge}>
              <PsychologyIcon />
            </span>
          </div>
          <h3>{reading ? 'Ask about this reading' : 'Ask about the engine'}</h3>
          <p>
            {reading
              ? 'Questions stay grounded in the numbers on screen — methods, trait scores, N, and confidence.'
              : 'General questions work now. Anything about your personal results needs a run first — enter birth details on the left and click Run the five systems.'}
          </p>
          <p className={styles.heroHint}>
            {reading
              ? `Context: ${reading.full_name}, born ${reading.date_of_birth}.`
              : 'No reading on screen yet — I will not invent signs or scores.'}
          </p>

          <div className={styles.suggestions}>
            <p className={styles.suggestLabel}>Suggested</p>
            {suggestions.map((text, index) => {
              const Icon = SUGGESTION_ICONS[index % SUGGESTION_ICONS.length]!;
              return (
                <button
                  key={text}
                  type="button"
                  className={styles.suggestBtn}
                  disabled={busy}
                  onClick={() => void submit(text)}
                >
                  <span className={styles.suggestIcon}>
                    <Icon fontSize="small" />
                  </span>
                  <span>{text}</span>
                </button>
              );
            })}
          </div>
        </div>
      ) : (
        <div className={styles.messages}>
          {messages.map((msg) => (
            <div key={msg.id} className={msg.role === 'assistant' ? styles.assistantBlock : undefined}>
              {msg.role === 'assistant' && msg.thinkingSeconds != null && (
                <AssistantThinkingPanel
                  completed
                  elapsedSeconds={msg.thinkingSeconds}
                  defaultExpanded={false}
                />
              )}
              <div className={msg.role === 'user' ? styles.userRow : styles.assistantRow}>
                <div
                  className={msg.role === 'user' ? styles.userBubble : styles.assistantBubble}
                >
                  {msg.content}
                </div>
              </div>
            </div>
          ))}

          {busy && (
            <div className={styles.assistantRow}>
              <div className={styles.assistantBlockWide}>
                <AssistantThinkingPanel
                  phase={thinkingPhase === 'idle' ? 'reading_context' : thinkingPhase}
                  elapsedSeconds={thinkingSeconds}
                  defaultExpanded
                />
              </div>
            </div>
          )}
          <div ref={endRef} />
        </div>
      )}

      {error && (
        <p className={styles.chatError} role="alert">
          {error}
        </p>
      )}

      <form className={styles.composer} onSubmit={onSubmit}>
        <TextField
          placeholder={
            reading
              ? 'Ask about the scores, convergence, or one method…'
              : 'Ask how the app works, or what N means…'
          }
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={busy}
          size="small"
          fullWidth
          slotProps={{ htmlInput: { 'aria-label': 'Message to the assistant' } }}
        />
        <IconButton
          type="submit"
          color="primary"
          disabled={!input.trim() || busy}
          aria-label="Send message"
          className={styles.send}
        >
          <ArrowUpwardIcon fontSize="small" />
        </IconButton>
      </form>
      <p className={styles.disclaimer}>
        {reading
          ? 'Answers use the same model as the summary — check the matrix if something looks off.'
          : 'Without a reading I explain the app only; run the five systems for personal scores.'}
      </p>
    </div>
  );
}
