import React, { useState } from 'react';
import { ThemeProvider, createTheme, CssBaseline, Box } from '@mui/material';
import Sidebar from './components/Sidebar.jsx';
import Dashboard from './components/Dashboard.jsx';
import Documents from './components/Documents.jsx';
import AskAssistant from './components/AskAssistant.jsx';
import Analytics from './components/Analytics.jsx';

const TOPBAR_HEIGHT = 64;

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary:    { main: '#2196f3' },
    secondary:  { main: '#7c3aed' },
    success:    { main: '#22c55e' },
    background: { default: '#0a0e1a', paper: '#111827' },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: { borderRadius: 12 },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: { borderRadius: 8, textTransform: 'none', fontWeight: 600 },
      },
    },
  },
});

const VIEWS = { dashboard: Dashboard, documents: Documents, ask: AskAssistant, analytics: Analytics };

export default function App() {
  const [activeView, setActiveView] = useState('dashboard');
  const View = VIEWS[activeView] || Dashboard;

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
        <Sidebar activeView={activeView} setActiveView={setActiveView} />
        <Box
          component="main"
          sx={{
            flexGrow: 1,
            mt: `${TOPBAR_HEIGHT}px`,
            p: { xs: 2, md: 4 },
            overflowY: 'auto',
            bgcolor: 'background.default',
          }}
        >
          <View />
        </Box>
      </Box>
    </ThemeProvider>
  );
}
