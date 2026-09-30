import GlobalStyles from '@mui/material/GlobalStyles';
import { ThemeProvider } from '@mui/material/styles';
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';

import {
  THEME_STORAGE_KEY,
  colourVariablesFor,
  createAppTheme,
  type ThemeMode,
} from './theme';

function readStoredMode(): ThemeMode {
  try {
    const stored = localStorage.getItem(THEME_STORAGE_KEY);
    return stored === 'dark' ? 'dark' : 'light';
  } catch {
    return 'light';
  }
}

interface ThemeModeContextValue {
  mode: ThemeMode;
  setMode: (mode: ThemeMode) => void;
  toggleMode: () => void;
}

const ThemeModeContext = createContext<ThemeModeContextValue | null>(null);

export function useThemeMode(): ThemeModeContextValue {
  const value = useContext(ThemeModeContext);
  if (!value) {
    throw new Error('useThemeMode must be used within AppThemeProvider');
  }
  return value;
}

interface Props {
  children: ReactNode;
}

export function AppThemeProvider({ children }: Props) {
  const [mode, setModeState] = useState<ThemeMode>(() => readStoredMode());

  const setMode = useCallback((next: ThemeMode) => {
    setModeState(next);
  }, []);

  const toggleMode = useCallback(() => {
    setModeState((current) => (current === 'light' ? 'dark' : 'light'));
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = mode;
    try {
      localStorage.setItem(THEME_STORAGE_KEY, mode);
    } catch {
      // Private mode or blocked storage — still apply the class for this session.
    }
  }, [mode]);

  const muiTheme = useMemo(() => createAppTheme(mode), [mode]);
  const cssVars = useMemo(() => colourVariablesFor(mode), [mode]);

  const contextValue = useMemo(
    () => ({ mode, setMode, toggleMode }),
    [mode, setMode, toggleMode],
  );

  return (
    <ThemeModeContext.Provider value={contextValue}>
      <ThemeProvider theme={muiTheme}>
        <GlobalStyles styles={{ ':root': cssVars }} />
        {children}
      </ThemeProvider>
    </ThemeModeContext.Provider>
  );
}
