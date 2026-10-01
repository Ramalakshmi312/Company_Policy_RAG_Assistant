import React, { useEffect, useState } from 'react';
import {
  Box, Typography, Card, CardContent, Alert, CircularProgress, Grid, Chip,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper,
} from '@mui/material';
import { getAnalytics } from '../api.js';

function SummaryCard({ label, value, color }) {
  return (
    <Card sx={{ bgcolor: 'background.paper', border: '1px solid rgba(255,255,255,0.07)', textAlign: 'center' }}>
      <CardContent>
        <Typography variant="h3" sx={{ fontWeight: 700, color }}>{value ?? 0}</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>{label}</Typography>
      </CardContent>
    </Card>
  );
}

export default function Analytics() {
  const [data,    setData]    = useState(null);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState('');

  useEffect(() => {
    getAnalytics()
      .then((r) => setData(r.data))
      .catch(() => setError('Failed to load analytics.'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 8 }}>
        <CircularProgress />
      </Box>
    );
  }
  if (error) return <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>;

  const summary = data?.summary || {};
  const logs    = data?.logs    || [];

  return (
    <Box>
      <Typography variant="h5" sx={{ mb: 0.5, fontWeight: 700 }}>Analytics</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Query performance and usage statistics
      </Typography>

      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={4}>
          <SummaryCard label="Total Questions"   value={summary.total_questions}    color="#2196f3" />
        </Grid>
        <Grid item xs={12} sm={4}>
          <SummaryCard label="Cache Hits"        value={summary.cache_hits}         color="#22c55e" />
        </Grid>
        <Grid item xs={12} sm={4}>
          <SummaryCard label="Avg Response (ms)" value={summary.avg_response_time_ms} color="#f97316" />
        </Grid>
      </Grid>

      <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>Query Log</Typography>

      {logs.length === 0 ? (
        <Alert severity="info">No queries logged yet.</Alert>
      ) : (
        <TableContainer
          component={Paper}
          sx={{ bgcolor: 'background.paper', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 2 }}
        >
          <Table size="small">
            <TableHead>
              <TableRow sx={{ '& th': { fontWeight: 700, borderBottom: '1px solid rgba(255,255,255,0.1)' } }}>
                <TableCell>#</TableCell>
                <TableCell>Question</TableCell>
                <TableCell align="center">Time (ms)</TableCell>
                <TableCell align="center">Chunks</TableCell>
                <TableCell align="center">Cache</TableCell>
                <TableCell>Timestamp</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {logs.map((log) => (
                <TableRow key={log.id} hover>
                  <TableCell sx={{ color: 'text.secondary', fontSize: 12 }}>{log.id}</TableCell>
                  <TableCell sx={{ maxWidth: 320 }}>
                    <Typography variant="body2" noWrap title={log.question}>
                      {log.question}
                    </Typography>
                  </TableCell>
                  <TableCell align="center">{Math.round(log.response_time_ms)}</TableCell>
                  <TableCell align="center">{log.retrieved_chunk_count}</TableCell>
                  <TableCell align="center">
                    <Chip
                      label={log.cache_hit ? 'Hit' : 'Miss'}
                      size="small"
                      color={log.cache_hit ? 'success' : 'default'}
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell>
                    <Typography variant="caption" color="text.secondary">
                      {new Date(log.timestamp).toLocaleString()}
                    </Typography>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );
}
