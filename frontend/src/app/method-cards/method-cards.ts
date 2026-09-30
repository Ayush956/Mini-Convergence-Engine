import { ChangeDetectionStrategy, Component, input } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';

import { MethodResult } from '../reading.models';

/** One Material icon per method, so the five results are scannable by shape. */
const ICONS: Record<string, string> = {
  sun_sign: 'wb_sunny',
  chinese_zodiac: 'pets',
  life_path: 'route',
  name_number: 'badge',
  vara: 'brightness_5',
};

@Component({
  selector: 'app-method-cards',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [MatIconModule],
  templateUrl: './method-cards.html',
  styleUrl: './method-cards.scss',
})
export class MethodCards {
  readonly methods = input.required<MethodResult[]>();

  iconFor(method: MethodResult): string {
    return ICONS[method.id] ?? 'auto_awesome';
  }
}
