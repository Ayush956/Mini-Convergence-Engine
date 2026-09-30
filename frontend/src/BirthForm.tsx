import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutlined';
import PersonOutlineIcon from '@mui/icons-material/PersonOutlined';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';
import InputAdornment from '@mui/material/InputAdornment';
import TextField from '@mui/material/TextField';
import { MobileDatePicker } from '@mui/x-date-pickers/MobileDatePicker';
import { MobileTimePicker } from '@mui/x-date-pickers/MobileTimePicker';
import type { MobileTimePickerProps } from '@mui/x-date-pickers/MobileTimePicker';
import { renderMultiSectionDigitalClockTimeView } from '@mui/x-date-pickers/timeViewRenderers';
import dayjs, { type Dayjs } from 'dayjs';
import { useMemo, useState } from 'react';

import styles from './BirthForm.module.scss';
import type { ReadingRequest } from './reading.models';

/** Start of the verified Chinese calendar table, mirrored from the API. */
const EARLIEST_YEAR = 1902;

/** Only used to choose which page of years the calendar opens on. */
const TYPICAL_AGE_YEARS = 30;

const MAX_NAME_LENGTH = 120;

type Field = 'fullName' | 'dateOfBirth' | 'timeOfBirth';

/**
 * Digital hour and minute columns for the time dialog, instead of the default
 * clock face. On a 24-hour clock the hours crowd into two rings and the
 * minutes have to be aimed at, and the exact minute matters here: it decides
 * the vara either side of 06:00, and the sign either side of a cusp.
 *
 * The cast is a gap in MUI's own types. The renderer is declared over the view
 * union that includes 'meridiem', which MobileTimePicker's does not, but with
 * ampm off there is no meridiem view to render - so it is a superset being
 * handed to a narrower slot.
 */
const renderDigitalColumns = (
  props: Parameters<typeof renderMultiSectionDigitalClockTimeView>[0],
) =>
  renderMultiSectionDigitalClockTimeView({
    ...props,
    // Every minute, not the default five. Most people round their birth time
    // anyway, but the ones who know it to the minute are exactly the ones
    // sitting near a boundary where it changes the answer.
    timeSteps: { hours: 1, minutes: 1 },
  });

const DIGITAL_COLUMNS = {
  hours: renderDigitalColumns,
  minutes: renderDigitalColumns,
} as unknown as NonNullable<MobileTimePickerProps['viewRenderers']>;

interface Props {
  busy: boolean;
  serverError: string | null;
  onSubmit: (request: ReadingRequest) => void;
}

export function BirthForm({ busy, serverError, onSubmit }: Props) {
  const [fullName, setFullName] = useState('');
  const [dateOfBirth, setDateOfBirth] = useState<Dayjs | null>(null);
  const [timeOfBirth, setTimeOfBirth] = useState<Dayjs | null>(null);
  // The picker dialogs are driven from here rather than left to open
  // themselves, so a click anywhere on the read-only field opens them. Left
  // to MUI, a read-only field only responds to the small toggle button, and a
  // field that ignores a click looks broken.
  const [dateOpen, setDateOpen] = useState(false);
  const [timeOpen, setTimeOpen] = useState(false);
  const [touched, setTouched] = useState<Record<Field, boolean>>({
    fullName: false,
    dateOfBirth: false,
    timeOfBirth: false,
  });

  // Recomputed per render rather than per keystroke; three fields is nothing
  // to validate and keeping it derived means there is no second copy of the
  // form's state that can fall out of step.
  const problems = validate(fullName, dateOfBirth, timeOfBirth);
  const valid = Object.keys(problems).length === 0;

  // Both depend only on today, so they must not be rebuilt every render - a
  // new Dayjs each time would reopen the calendar on a different page.
  const maxDate = useMemo(() => dayjs(), []);
  const minDate = useMemo(() => dayjs(`${EARLIEST_YEAR}-01-01`), []);
  const referenceDate = useMemo(
    () => dayjs().subtract(TYPICAL_AGE_YEARS, 'year').startOf('year'),
    [],
  );

  const errorFor = (field: Field) => (touched[field] ? (problems[field] ?? null) : null);
  const markTouched = (field: Field) => setTouched((was) => ({ ...was, [field]: true }));

  const submit = (event: React.FormEvent) => {
    event.preventDefault();

    if (!valid || busy) {
      // Touch everything so every outstanding problem becomes visible at
      // once, rather than the user discovering them one at a time.
      setTouched({ fullName: true, dateOfBirth: true, timeOfBirth: true });
      return;
    }

    onSubmit({
      full_name: fullName.trim(),
      // Formatted from the local calendar date, never through UTC, which can
      // shift the day and would silently change both the sun sign and the
      // Chinese animal.
      date_of_birth: dateOfBirth!.format('YYYY-MM-DD'),
      time_of_birth: timeOfBirth!.format('HH:mm'),
    });
  };

  return (
    <form className={styles.form} onSubmit={submit} noValidate>
      <TextField
        label="Full name"
        value={fullName}
        placeholder="e.g. Ayush Mishra"
        autoComplete="name"
        required
        error={Boolean(errorFor('fullName'))}
        helperText={errorFor('fullName') ?? 'Used for the Chaldean name number'}
        onChange={(event) => setFullName(event.target.value)}
        onBlur={() => markTouched('fullName')}
        slotProps={{
          input: {
            endAdornment: (
              <InputAdornment position="end">
                <PersonOutlineIcon fontSize="small" />
              </InputAdornment>
            ),
          },
        }}
      />

      <div className={`${styles.row} ${styles.pickers}`}>
        {/*
          Mobile variants on both, on purpose. Their field is not typeable and
          opens a dialog, which is exactly what is wanted for a birth date:
          05/06/2002 means two different dates depending on where the reader is
          from, and for any day of 12 or less the two readings are
          indistinguishable, so a mistyped date would come back as a complete,
          plausible, wrong reading.
        */}
        <MobileDatePicker
          label="Date of birth"
          value={dateOfBirth}
          format="DD/MM/YYYY"
          openTo="year"
          views={['year', 'month', 'day']}
          minDate={minDate}
          maxDate={maxDate}
          referenceDate={referenceDate}
          onChange={setDateOfBirth}
          open={dateOpen}
          onOpen={() => setDateOpen(true)}
          onClose={() => {
            setDateOpen(false);
            markTouched('dateOfBirth');
          }}
          slotProps={{
            // readOnly stops the sectioned field being typed into, leaving the
            // calendar as the only way to set a date.
            field: { readOnly: true },
            textField: {
              required: true,
              onClick: () => setDateOpen(true),
              error: Boolean(errorFor('dateOfBirth')),
              helperText: errorFor('dateOfBirth') ?? 'Pick from the calendar',
            },
          }}
        />

        <MobileTimePicker
          label="Time of birth"
          value={timeOfBirth}
          format="HH:mm"
          ampm={false}
          // Digital columns rather than the default clock face. On a 24-hour
          // clock the hours crowd into two rings and the minutes have to be
          // aimed at, and the exact minute matters here: it decides the vara
          // either side of 06:00, and the sign either side of a cusp.
          viewRenderers={DIGITAL_COLUMNS}
          onChange={setTimeOfBirth}
          open={timeOpen}
          onOpen={() => setTimeOpen(true)}
          onClose={() => {
            setTimeOpen(false);
            markTouched('timeOfBirth');
          }}
          slotProps={{
            field: { readOnly: true },
            textField: {
              required: true,
              onClick: () => setTimeOpen(true),
              error: Boolean(errorFor('timeOfBirth')),
              helperText: errorFor('timeOfBirth') ?? 'Assumed to be IST',
            },
            // Styles hang off the paper, because the dialog renders in a portal
            // outside the form. The sx on layout wins over MUI's default grid,
            // which reserves a shortcut column this picker never uses.
            layout: {
              sx: {
                width: '100%',
                gridTemplateColumns: '1fr',
                '& .MuiPickersLayout-toolbar': { gridColumn: '1', width: '100%' },
                '& .MuiPickersLayout-contentWrapper': {
                  gridColumn: '1',
                  width: '100%',
                  alignItems: 'stretch',
                },
                '& .MuiPickersLayout-actionBar': { gridColumn: '1', width: '100%' },
                '& .MuiMultiSectionDigitalClock-root': {
                  width: '100%',
                  justifyContent: 'stretch',
                  borderBottom: 0,
                },
                '& .MuiMultiSectionDigitalClockSection-root': {
                  flex: '1 1 50%',
                  width: 'auto',
                  maxWidth: 'none',
                },
              },
            },
            mobilePaper: { className: styles.timeDialogPaper },
          }}
        />
      </div>

      {serverError && (
        <p className={styles.serverError} role="alert">
          <ErrorOutlineIcon fontSize="small" />
          <span>{serverError}</span>
        </p>
      )}

      <div className={styles.actions}>
        <Button
          type="submit"
          variant="contained"
          className={styles.submit}
          disabled={busy}
          startIcon={
            busy ? <CircularProgress size={16} color="inherit" /> : <AutoAwesomeIcon />
          }
        >
          {busy ? 'Calculating' : 'Run the five systems'}
        </Button>

        {!busy && !valid && <span className={styles.blocked}>{blockedReason(problems)}</span>}
      </div>
    </form>
  );
}

/**
 * One message per field, in plain language.
 *
 * Deliberately not "invalid input": the brief asks for clear messages, and a
 * message that explains what is wanted is worth more than one that restates
 * that something is wrong.
 */
function validate(
  fullName: string,
  dateOfBirth: Dayjs | null,
  timeOfBirth: Dayjs | null,
): Partial<Record<Field, string>> {
  const problems: Partial<Record<Field, string>> = {};
  const name = fullName.trim();

  if (!name) {
    problems.fullName = 'We need a name to work from.';
  } else if (name.length > MAX_NAME_LENGTH) {
    problems.fullName = 'That name is a little too long for us.';
  } else if (!/\p{L}/u.test(name)) {
    problems.fullName = 'A name needs at least one letter.';
  }

  if (!dateOfBirth) {
    problems.dateOfBirth = 'Pick a date of birth from the calendar.';
  } else if (!dateOfBirth.isValid()) {
    problems.dateOfBirth = 'We could not read that as a date.';
  } else if (dateOfBirth.isAfter(dayjs(), 'day')) {
    problems.dateOfBirth = 'A date of birth cannot be in the future.';
  } else if (dateOfBirth.year() < EARLIEST_YEAR) {
    problems.dateOfBirth = `Our verified calendar data starts at ${EARLIEST_YEAR}.`;
  }

  if (!timeOfBirth) {
    problems.timeOfBirth = 'Pick a time, even if it is a rough one.';
  } else if (!timeOfBirth.isValid()) {
    problems.timeOfBirth = 'We could not read that as a time.';
  }

  return problems;
}

/** Why the submit button is disabled, so it is never a dead end. */
function blockedReason(problems: Partial<Record<Field, string>>): string | null {
  const missing: string[] = [];
  if (problems.fullName) missing.push('a name');
  if (problems.dateOfBirth) missing.push('a date of birth');
  if (problems.timeOfBirth) missing.push('a time of birth');

  if (missing.length === 0) return null;
  if (missing.length === 1) return `Still need ${missing[0]}.`;
  return `Still need ${missing.slice(0, -1).join(', ')} and ${missing.at(-1)}.`;
}
