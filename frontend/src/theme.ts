import { createTheme } from '@mui/material/styles';

export type ThemeMode = 'light' | 'dark';

export type ColourTokens = {
  surface: string;
  'surface-container': string;
  'surface-container-high': string;
  'on-surface': string;
  'on-surface-variant': string;
  'outline-variant': string;
  primary: string;
  'on-primary': string;
  tertiary: string;
  error: string;
  nebula: string;
  moon: string;
  strong: string;
  medium: string;
  weak: string;
};

/** Near-black natal-chart palette, matching the reference calculator look. */
export const darkColours: ColourTokens = {
  surface: '#050505',
  'surface-container': '#121212',
  'surface-container-high': '#1a1a1a',
  'on-surface': '#f4f0e6',
  'on-surface-variant': '#b8b0a3',
  'outline-variant': '#2a2a2a',
  primary: '#e4c76b',
  'on-primary': '#1a1408',
  tertiary: '#d4a15a',
  error: '#f5a8a0',
  nebula: '#2a2218',
  moon: '#e8dfc8',
  strong: '#6ee7d4',
  medium: '#d4a843',
  weak: '#5c6478',
};

/** Warm daylight / solar palette for the default light theme. */
export const lightColours: ColourTokens = {
  surface: '#faf6eb',
  'surface-container': '#fff9e6',
  'surface-container-high': '#f5ecd4',
  'on-surface': '#2a2214',
  'on-surface-variant': '#6b5d45',
  'outline-variant': '#d9c9a3',
  primary: '#b8860b',
  'on-primary': '#fffdf5',
  tertiary: '#c45c26',
  error: '#c62828',
  nebula: '#e8d4a8',
  moon: '#8a7355',
  strong: '#0d9488',
  medium: '#ca8a04',
  weak: '#78716c',
};

export const THEME_STORAGE_KEY = 'mce-theme';

export function coloursForMode(mode: ThemeMode): ColourTokens {
  return mode === 'dark' ? darkColours : lightColours;
}

export function colourVariablesFor(mode: ThemeMode): Record<string, string> {
  const colours = coloursForMode(mode);
  return Object.fromEntries(Object.entries(colours).map(([name, value]) => [`--${name}`, value]));
}

const sharedTypography = {
  fontFamily: "Inter, 'Helvetica Neue', Helvetica, Arial, sans-serif",
  h1: {
    fontFamily: "'Cormorant Garamond', Georgia, 'Times New Roman', serif",
    fontWeight: 600,
    letterSpacing: '0.02em',
  },
  h2: {
    fontFamily: "'Cormorant Garamond', Georgia, 'Times New Roman', serif",
    fontWeight: 600,
    letterSpacing: '0.02em',
  },
  h3: {
    fontFamily: "'Cormorant Garamond', Georgia, 'Times New Roman', serif",
    fontWeight: 600,
    letterSpacing: '0.04em',
  },
} as const;

export function createAppTheme(mode: ThemeMode) {
  const colours = coloursForMode(mode);
  const muiMode = mode === 'dark' ? 'dark' : 'light';

  return createTheme({
    palette: {
      mode: muiMode,
      primary: { main: colours.primary, contrastText: colours['on-primary'] },
      secondary: { main: colours.tertiary },
      error: { main: colours.error },
      background: {
        default: colours.surface,
        paper: colours['surface-container'],
      },
      text: {
        primary: colours['on-surface'],
        secondary: colours['on-surface-variant'],
      },
      divider: colours['outline-variant'],
    },
    typography: sharedTypography,
    shape: { borderRadius: 8 },
    components: {
      MuiPaper: { styleOverrides: { root: { backgroundImage: 'none' } } },
      MuiTextField: { defaultProps: { variant: 'outlined', fullWidth: true } },
      MuiButton: { defaultProps: { disableElevation: true } },
      MuiOutlinedInput: {
        styleOverrides: {
          root: {
            '&:hover .MuiOutlinedInput-notchedOutline': {
              borderColor: colours.moon,
            },
            '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
              borderColor: colours.primary,
            },
          },
        },
      },
    },
  });
}

/** @deprecated Use createAppTheme('dark') — kept so older imports do not break silently. */
export const colours = darkColours;
export const colourVariables = colourVariablesFor('dark');
export const theme = createAppTheme('dark');
