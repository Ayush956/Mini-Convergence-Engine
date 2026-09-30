import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';

import { App } from './App';
import { AppThemeProvider } from './AppThemeProvider';
import './styles.scss';

// No CssBaseline: it sets the body background from the palette, and emotion
// injects after the imported stylesheet, so it would paint over the radial
// gradient. styles.scss already does the reset that matters.
createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AppThemeProvider>
      <LocalizationProvider dateAdapter={AdapterDayjs}>
        <App />
      </LocalizationProvider>
    </AppThemeProvider>
  </StrictMode>,
);
