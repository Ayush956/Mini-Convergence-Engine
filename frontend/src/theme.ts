import { createTheme } from '@mui/material/styles';

/**
 * The colour tokens, defined once.
 *
 * MUI needs them as JavaScript, because it computes hover and focus states
 * from the base colours and cannot do that through a CSS variable. The
 * stylesheets need them as CSS. So they live here and are published to CSS as
 * custom properties at startup - one source, no drift between the two.
 *
 * Values are the Material 3 baseline dark tokens for a violet primary with an
 * orange tertiary, which is what the design was built against.
 */
export const colours = {
  surface: '#141218',
  'surface-container': '#211f26',
  'surface-container-high': '#2b2930',
  'on-surface': '#e6e0e9',
  'on-surface-variant': '#cac4d0',
  'outline-variant': '#49454f',
  primary: '#cfbcff',
  'on-primary': '#381e72',
  tertiary: '#ffb77c',
  error: '#ffb4ab',

  // Trait strength, reused by the matrix bars and the confidence meters.
  strong: '#7ee787',
  medium: '#d9a441',
  weak: '#6b7280',
} as const;

export const colourVariables = Object.fromEntries(
  Object.entries(colours).map(([name, value]) => [`--${name}`, value]),
);

export const theme = createTheme({
  palette: {
    mode: 'dark',
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
  typography: {
    fontFamily: "Inter, 'Helvetica Neue', Helvetica, Arial, sans-serif",
  },
  shape: { borderRadius: 8 },
  components: {
    // The radial gradient on the body should show through the panels, so no
    // component may paint an opaque sheet over it.
    MuiPaper: { styleOverrides: { root: { backgroundImage: 'none' } } },
    MuiTextField: { defaultProps: { variant: 'outlined', fullWidth: true } },
    MuiButton: { defaultProps: { disableElevation: true } },
  },
});
