import DarkModeOutlinedIcon from '@mui/icons-material/DarkModeOutlined';
import LightModeOutlinedIcon from '@mui/icons-material/LightModeOutlined';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';

import { useThemeMode } from './AppThemeProvider';
import styles from './ThemeToggle.module.scss';
import type { ThemeMode } from './theme';

export function ThemeToggle() {
  const { mode, setMode } = useThemeMode();

  const onChange = (_event: React.MouseEvent<HTMLElement>, next: ThemeMode | null) => {
    if (next) {
      setMode(next);
    }
  };

  return (
    <ToggleButtonGroup
      className={styles.group}
      value={mode}
      exclusive
      size="small"
      onChange={onChange}
      aria-label="Colour theme"
    >
      <ToggleButton value="light" aria-label="Light theme" className={styles.btn}>
        <LightModeOutlinedIcon fontSize="small" />
        <span className={styles.label}>Light</span>
      </ToggleButton>
      <ToggleButton value="dark" aria-label="Dark theme" className={styles.btn}>
        <DarkModeOutlinedIcon fontSize="small" />
        <span className={styles.label}>Dark</span>
      </ToggleButton>
    </ToggleButtonGroup>
  );
}
