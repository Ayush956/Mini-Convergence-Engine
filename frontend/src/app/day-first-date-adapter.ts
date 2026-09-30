import { Injectable } from '@angular/core';
import { NativeDateAdapter } from '@angular/material/core';

const pad = (value: number) => String(value).padStart(2, '0');

/**
 * Displays calendar dates as DD/MM/YYYY.
 *
 * Only the display side is overridden. The date field is readonly and filled
 * from the calendar, so nothing is ever parsed from text - which is the point:
 * 05/06/2002 is two different dates depending on where the reader is from, and
 * a birth date that comes back wrong but plausible is worse than one refused.
 */
@Injectable()
export class DayFirstDateAdapter extends NativeDateAdapter {
  override format(date: Date, displayFormat: Object): string {
    // The timepicker formats its options through this same adapter, asking
    // for hours and minutes. Answering those with a date is how every time in
    // the dropdown ends up reading "30/09/2026".
    const options = displayFormat as Intl.DateTimeFormatOptions | null;
    const wantsTime = Boolean(options?.hour ?? options?.minute ?? options?.second);

    if (wantsTime || !this.isValid(date)) {
      return super.format(date, displayFormat);
    }

    return `${pad(date.getDate())}/${pad(date.getMonth() + 1)}/${date.getFullYear()}`;
  }
}
