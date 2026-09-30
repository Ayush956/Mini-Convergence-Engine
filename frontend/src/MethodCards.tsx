import BadgeIcon from '@mui/icons-material/Badge';
import Brightness5Icon from '@mui/icons-material/Brightness5';
import PetsIcon from '@mui/icons-material/Pets';
import RouteIcon from '@mui/icons-material/Route';
import WbSunnyIcon from '@mui/icons-material/WbSunny';
import type { SvgIconComponent } from '@mui/icons-material';

import './MethodCards.scss';
import type { MethodResult } from './reading.models';

/** One icon per method, so the five results are scannable by shape. */
const ICONS: Record<string, SvgIconComponent> = {
  sun_sign: WbSunnyIcon,
  chinese_zodiac: PetsIcon,
  life_path: RouteIcon,
  name_number: BadgeIcon,
  vara: Brightness5Icon,
};

export function MethodCards({ methods }: { methods: MethodResult[] }) {
  return (
    <ul className="cards">
      {methods.map((method, index) => {
        const Icon = ICONS[method.id] ?? WbSunnyIcon;

        return (
          <li
            className="card"
            key={method.id}
            // The stagger is set per card rather than by nth-child, so it
            // keeps working whatever order the backend returns.
            style={{ '--delay': `${index * 70}ms` } as React.CSSProperties}
          >
            <div className="head">
              <Icon fontSize="small" aria-hidden />
              <h3>{method.label}</h3>
            </div>

            <p className="result">{method.result}</p>
            <p className="detail">{method.detail}</p>

            <dl className="basis">
              <dt>How it was derived</dt>
              <dd>{method.basis}</dd>
            </dl>

            {method.notes.length > 0 && (
              <ul className="notes">
                {method.notes.map((note) => (
                  <li key={note}>{note}</li>
                ))}
              </ul>
            )}
          </li>
        );
      })}
    </ul>
  );
}
