import React from 'react';
import { AppBar, Toolbar, Box, Typography, Button, Chip } from '@mui/material';
import DashboardRoundedIcon from '@mui/icons-material/DashboardRounded';
import DescriptionRoundedIcon from '@mui/icons-material/DescriptionRounded';
import AutoAwesomeRoundedIcon from '@mui/icons-material/AutoAwesomeRounded';
import BarChartRoundedIcon from '@mui/icons-material/BarChartRounded';
import PolicyRoundedIcon from '@mui/icons-material/PolicyRounded';

const NAV = [
  { id: 'dashboard', label: 'Dashboard',     icon: <DashboardRoundedIcon fontSize="small" /> },
  { id: 'documents', label: 'Documents',     icon: <DescriptionRoundedIcon fontSize="small" /> },
  { id: 'ask',       label: 'Ask Assistant', icon: <AutoAwesomeRoundedIcon fontSize="small" />, badge: 'AI' },
  { id: 'analytics', label: 'Analytics',     icon: <BarChartRoundedIcon fontSize="small" /> },
];

export default function Sidebar({ activeView, setActiveView }) {
  return (
    <AppBar
      position="fixed"
      elevation={0}
      sx={{
        bgcolor: '#0d1117',
        borderBottom: '1px solid rgba(255,255,255,0.07)',
        zIndex: (theme) => theme.zIndex.drawer + 1,
      }}
    >
      <Toolbar sx={{ gap: 1 }}>
        {/* Brand */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mr: 3 }}>
          <Box
            sx={{
              width: 32, height: 32, borderRadius: 2,
              background: 'linear-gradient(135deg, #2196f3 0%, #7c3aed 100%)',
              display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
            }}
          >
            <PolicyRoundedIcon sx={{ fontSize: 18, color: '#fff' }} />
          </Box>
          <Box sx={{ lineHeight: 1 }}>
            <Typography variant="subtitle2" sx={{ color: '#fff', fontWeight: 700, lineHeight: 1.2 }}>
              Policy AI
            </Typography>
            <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.4)', fontSize: 10, lineHeight: 1 }}>
              Intelligence Assistant
            </Typography>
          </Box>
        </Box>

        {/* Spacer */}
        <Box sx={{ flexGrow: 1 }} />

        {/* Nav links on the right */}
        {NAV.map((item) => {
          const active = activeView === item.id;
          return (
            <Button
              key={item.id}
              onClick={() => setActiveView(item.id)}
              startIcon={item.icon}
              endIcon={item.badge ? <Chip label={item.badge} size="small" color="primary" sx={{ height: 16, fontSize: 9, ml: -0.5 }} /> : null}
              sx={{
                color: active ? '#fff' : 'rgba(255,255,255,0.55)',
                fontWeight: active ? 700 : 400,
                bgcolor: active ? 'rgba(33,150,243,0.12)' : 'transparent',
                borderRadius: 2,
                px: 1.5,
                '&:hover': { bgcolor: 'rgba(255,255,255,0.07)', color: '#fff' },
                transition: 'all 0.15s',
              }}
            >
              {item.label}
            </Button>
          );
        })}
      </Toolbar>
    </AppBar>
  );
}
