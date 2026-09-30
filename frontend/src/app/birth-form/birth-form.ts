import { Component, output, input, ChangeDetectionStrategy } from '@angular/core';
import {
  FormBuilder,
  ReactiveFormsModule,
  Validators,
  AbstractControl,
  ValidationErrors,
} from '@angular/forms';
import { inject } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { DateAdapter, MatNativeDateModule } from '@angular/material/core';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

import { DayFirstDateAdapter } from '../day-first-date-adapter';
import { ReadingRequest } from '../reading.models';

/** Bounds of the verified Chinese calendar table, mirrored from the API. */
const EARLIEST_YEAR = 1902;
const LATEST_YEAR = 2100;

/** A name has to contain at least one letter for the Chaldean table to score. */
function mustContainALetter(control: AbstractControl): ValidationErrors | null {
  const value = (control.value ?? '').toString();
  if (!value.trim()) {
    return null; // `required` already covers this; do not stack two messages.
  }
  return /\p{L}/u.test(value) ? null : { noLetters: true };
}

@Component({
  selector: 'app-birth-form',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    ReactiveFormsModule,
    MatButtonModule,
    MatDatepickerModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
    MatNativeDateModule,
    MatProgressSpinnerModule,
  ],
  templateUrl: './birth-form.html',
  styleUrl: './birth-form.scss',
  providers: [{ provide: DateAdapter, useClass: DayFirstDateAdapter }],
})
export class BirthForm {
  /** Disables the form while a request is in flight. */
  readonly busy = input(false);

  /** A server-side error, shown above the button rather than in a toast. */
  readonly serverError = input<string | null>(null);

  readonly submitted = output<ReadingRequest>();

  readonly minDate = new Date(EARLIEST_YEAR, 0, 1);
  readonly maxDate = new Date(LATEST_YEAR, 11, 31);

  private readonly fb = inject(FormBuilder);

  readonly form = this.fb.nonNullable.group({
    fullName: ['', [Validators.required, Validators.maxLength(120), mustContainALetter]],
    dateOfBirth: [null as Date | null, [Validators.required]],
    timeOfBirth: ['', [Validators.required, Validators.pattern(/^([01]\d|2[0-3]):[0-5]\d$/)]],
  });

  /**
   * One message per field, in plain language.
   *
   * Deliberately not "invalid input": the brief asks for clear messages, and
   * a message that explains what is wanted is worth more than one that
   * restates that something is wrong.
   */
  errorFor(field: 'fullName' | 'dateOfBirth' | 'timeOfBirth'): string | null {
    const control = this.form.controls[field];
    if (!control.touched || control.valid) {
      return null;
    }

    switch (field) {
      case 'fullName':
        if (control.hasError('required')) return 'We need a name to work from.';
        if (control.hasError('maxlength')) return 'That name is a little too long for us.';
        if (control.hasError('noLetters')) return 'A name needs at least one letter.';
        return null;
      case 'dateOfBirth':
        if (control.hasError('required')) return 'Pick a date of birth.';
        if (control.hasError('matDatepickerMin'))
          return `Our verified calendar data starts at ${EARLIEST_YEAR}.`;
        if (control.hasError('matDatepickerMax'))
          return `Our verified calendar data stops at ${LATEST_YEAR}.`;
        if (control.hasError('matDatepickerParse')) return "We could not read that as a date.";
        return null;
      case 'timeOfBirth':
        if (control.hasError('required')) return 'Enter a time, even if it is a rough one.';
        if (control.hasError('pattern')) return 'Use 24-hour time, like 09:30 or 21:05.';
        return null;
    }
  }

  /** Why the submit button is disabled, so it is never a dead end. */
  get blockedReason(): string | null {
    if (this.busy()) return null;
    if (this.form.valid) return null;

    const missing: string[] = [];
    if (this.form.controls.fullName.invalid) missing.push('a name');
    if (this.form.controls.dateOfBirth.invalid) missing.push('a date of birth');
    if (this.form.controls.timeOfBirth.invalid) missing.push('a time of birth');

    if (missing.length === 0) return null;
    if (missing.length === 1) return `Still need ${missing[0]}.`;
    return `Still need ${missing.slice(0, -1).join(', ')} and ${missing.at(-1)}.`;
  }

  submit(): void {
    if (this.form.invalid || this.busy()) {
      // Touch everything so every outstanding problem becomes visible at
      // once, rather than the user discovering them one at a time.
      this.form.markAllAsTouched();
      return;
    }

    const { fullName, dateOfBirth, timeOfBirth } = this.form.getRawValue();
    this.submitted.emit({
      full_name: fullName.trim(),
      date_of_birth: this.toIsoDate(dateOfBirth!),
      time_of_birth: timeOfBirth,
    });
  }

  /**
   * Local calendar date as YYYY-MM-DD.
   *
   * Not toISOString(), which converts to UTC first and can shift the date by
   * a day for anyone east or west of Greenwich - which would silently change
   * the sun sign and the Chinese animal.
   */
  private toIsoDate(date: Date): string {
    const month = `${date.getMonth() + 1}`.padStart(2, '0');
    const day = `${date.getDate()}`.padStart(2, '0');
    return `${date.getFullYear()}-${month}-${day}`;
  }
}
