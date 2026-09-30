import { ChangeDetectionStrategy, Component, input } from '@angular/core';

@Component({
  selector: 'app-skeleton',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './skeleton.html',
  styleUrl: './skeleton.scss',
})
export class Skeleton {
  /** Set once the wait has run long enough to need explaining. */
  readonly slow = input(false);

  readonly cards = [0, 1, 2, 3, 4];
  readonly rows = [0, 1, 2, 3, 4, 5];
}
