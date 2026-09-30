import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';

import { BirthForm } from './birth-form/birth-form';
import { MethodCards } from './method-cards/method-cards';
import { Reading, ReadingRequest } from './reading.models';
import { ReadingService } from './reading.service';

@Component({
  selector: 'app-root',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [BirthForm, MethodCards],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App {
  private readonly service = inject(ReadingService);

  readonly reading = signal<Reading | null>(null);
  readonly busy = signal(false);
  readonly error = signal<string | null>(null);

  run(request: ReadingRequest): void {
    this.busy.set(true);
    this.error.set(null);

    this.service.getReading(request).subscribe({
      next: (reading) => {
        this.reading.set(reading);
        this.busy.set(false);
      },
      error: (failure: { message: string }) => {
        this.error.set(failure.message);
        this.busy.set(false);
      },
    });
  }

  reset(): void {
    this.reading.set(null);
    this.error.set(null);
  }
}
