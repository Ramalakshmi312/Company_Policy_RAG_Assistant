import React, { useEffect, useState } from 'react';
import {
  Grid, Card, CardContent, Typography, Box, Chip,
  CircularProgress, Alert, Skeleton,
} from '@mui/material';
import DescriptionRoundedIcon from '@mui/icons-material/DescriptionRounded';
import LayersRoundedIcon from '@mui/icons-material/LayersRounded';
import QuestionAnswerRoundedIcon from '@mui/icons-material/QuestionAnswerRounded';
import SpeedRoundedIcon from '@mui/icons-material/SpeedRounded';
import { getAnalytics } from '../api.js';

function StatCard({ icon, label, value, gradient }) {
  return (
    <Card
      sx={{
        background: gradient,
        border: 'none',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      <CardContent sx={{ p: 2.5 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Box>
            <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.7)', mb: 0.5 }}>
              {label}
            </Typography>
            <Typography variant="h4" sx={{ fontWeight: 700, color: '#fff' }}>
              {value ?? <Skeleton width={60} />}
            </Typography>
          </Box>
          <Box
            sx={{
              bgcolor: 'rgba(255,255,255,0.15)', borderRadius: 2, p: 1,
              '& svg': { fontSize: 24, color: '#fff' },
            }}
          >
            {icon}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
}

export default function Dashboard() {
  const [data, setData]     = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]   = useState('');

  useEffect(() => {
    getAnalytics()
      .then((r) => setData(r.data))
      .catch(() => setError('Failed to load dashboard. Is the backend running on port 8000?'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh' }}>
        <CircularProgress />
      </Box>
    );
  }
  if (error) return <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>;

  const summary = data?.summary || {};
  const logs    = data?.logs    || [];

  const STATS = [
    { icon: <DescriptionRoundedIcon />,      label: 'Total Documents',    value: summary.total_documents ?? 0,      gradient: 'linear-gradient(135deg,#1565c0,#1976d2)' },
    { icon: <LayersRoundedIcon />,           label: 'Total Chunks',       value: summary.total_chunks ?? 0,          gradient: 'linear-gradient(135deg,#6a1b9a,#8e24aa)' },
    { icon: <QuestionAnswerRoundedIcon />,   label: 'Questions Asked',    value: summary.total_questions ?? 0,       gradient: 'linear-gradient(135deg,#1b5e20,#2e7d32)' },
    { icon: <SpeedRoundedIcon />,            label: 'Avg Response (ms)',  value: summary.avg_response_time_ms ?? 0,  gradient: 'linear-gradient(135deg,#e65100,#f57c00)' },
  ];

  return (
    <Box>
      <Typography variant="h5" sx={{ mb: 0.5, fontWeight: 700 }}>Dashboard</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Overview of your Policy Document Intelligence Assistant
      </Typography>

      <Grid container spacing={3} sx={{ mb: 4 }}>
        {STATS.map((s) => (
          <Grid item xs={12} sm={6} lg={3} key={s.label}>
            <StatCard {...s} />
          </Grid>
        ))}
      </Grid>

      <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>Recent Activity</Typography>
      {logs.length === 0 ? (
        <Alert severity="info">
          No questions asked yet. Head to <strong>Ask Assistant</strong> to get started.
        </Alert>
      ) : (
        logs.slice(0, 6).map((log) => (
          <Card
            key={log.id}
            sx={{
              mb: 1.5, bgcolor: 'background.paper',
              border: '1px solid rgba(255,255,255,0.06)',
              '&:hover': { borderColor: 'rgba(33,150,243,0.3)' },
              transition: 'border-color 0.2s',
            }}
          >
            <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 1 }}>
                <Typography variant="body2" sx={{ flex: 1 }} noWrap title={log.question}>
                  {log.question}
                </Typography>
                <Box sx={{ display: 'flex', gap: 0.75, flexShrink: 0 }}>
                  <Chip
                    label={log.cache_hit ? 'Cached' : 'Fresh'}
                    size="small"
                    color={log.cache_hit ? 'success' : 'primary'}
                    variant="outlined"
                  />
                  <Chip label={`${Math.round(log.response_time_ms)}ms`} size="small" variant="outlined" />
                </Box>
              </Box>
              <Typography variant="caption" color="text.secondary">{log.timestamp}</Typography>
            </CardContent>
          </Card>
        ))
      )}
    </Box>
  );
}
