import { Injectable } from '@angular/core';
import { NativeDateAdapter } from '@angular/material/core';

/** DD/MM/YYYY or DD-MM-YYYY, with a one- or two-digit day and month. */
const DAY_FIRST = /^\s*(\d{1,2})[\/\-.](\d{1,2})[\/\-.](\d{4})\s*$/;

const pad = (value: number) => String(value).padStart(2, '0');

/**
 * Reads and writes dates day-first.
 *
 * Material's native adapter hands the string to the Date constructor, which
 * reads 15/08/1995 as invalid and 08/15/1995 as August - so a user typing the
 * format our own placeholder asks for gets their input rejected. Typing is the
 * fast path for a birth date decades back, well faster than clicking through
 * the year picker, so it has to work.
 */
@Injectable()
export class DayFirstDateAdapter extends NativeDateAdapter {
  override parse(value: unknown): Date | null {
    if (typeof value !== 'string') {
      return super.parse(value);
    }

    const parts = DAY_FIRST.exec(value);
    if (!parts) {
      return super.parse(value);
    }

    const [, day, month, year] = parts.map(Number);
    const parsed = new Date(year, month - 1, day);

    // Rejects 31/02 rather than letting it roll into March, which would
    // silently change the answer the engine gives back.
    const rolled =
      parsed.getDate() !== day ||
      parsed.getMonth() !== month - 1 ||
      parsed.getFullYear() !== year;

    return rolled ? null : parsed;
  }

  override format(date: Date, displayFormat: Object): string {
    if (!this.isValid(date)) {
      return super.format(date, displayFormat);
    }

    return `${pad(date.getDate())}/${pad(date.getMonth() + 1)}/${date.getFullYear()}`;
  }
}
