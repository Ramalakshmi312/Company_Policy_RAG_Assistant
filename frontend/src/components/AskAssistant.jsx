import React, { useState } from 'react';
import {
  Box, Typography, TextField, Button, Card, CardContent,
  Alert, Chip, CircularProgress, Divider,
} from '@mui/material';
import SendRoundedIcon from '@mui/icons-material/SendRounded';
import CachedRoundedIcon from '@mui/icons-material/CachedRounded';
import AutoAwesomeRoundedIcon from '@mui/icons-material/AutoAwesomeRounded';
import FormatQuoteRoundedIcon from '@mui/icons-material/FormatQuoteRounded';
import RetrievedChunks from './RetrievedChunks.jsx';
import { askQuestion } from '../api.js';

const SAMPLES = [
  'What policies are mentioned in the uploaded documents?',
  'Summarize the key rules from the documents.',
  'What are the responsibilities mentioned?',
  'What are the important conditions?',
  'Compare the two uploaded policy documents.',
];

export default function AskAssistant() {
  const [question, setQuestion] = useState('');
  const [result,   setResult]   = useState(null);
  const [loading,  setLoading]  = useState(false);
  const [error,    setError]    = useState('');

  const handleAsk = () => {
    if (!question.trim()) return;
    setLoading(true);
    setError('');
    setResult(null);
    askQuestion(question)
      .then((r) => setResult(r.data))
      .catch((e) => setError(e.response?.data?.detail || 'Failed to get answer. Is the backend running?'))
      .finally(() => setLoading(false));
  };

  return (
    <Box>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h5" sx={{ fontWeight: 700 }}>Ask Assistant</Typography>
        <Typography variant="body2" color="text.secondary">
          Ask any question about your uploaded policy documents
        </Typography>
      </Box>

      {/* Sample question chips */}
      <Box sx={{ mb: 2, display: 'flex', flexWrap: 'wrap', gap: 0.75 }}>
        {SAMPLES.map((q) => (
          <Chip
            key={q}
            label={q}
            size="small"
            variant="outlined"
            clickable
            onClick={() => setQuestion(q)}
            sx={{ fontSize: 11, cursor: 'pointer', '&:hover': { bgcolor: 'rgba(33,150,243,0.08)' } }}
          />
        ))}
      </Box>

      {/* Input row */}
      <Box sx={{ display: 'flex', gap: 1.5, mb: 3, alignItems: 'flex-start' }}>
        <TextField
          fullWidth
          multiline
          maxRows={5}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="e.g. What are the leave policy rules?"
          variant="outlined"
          onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleAsk(); } }}
          sx={{ '& .MuiOutlinedInput-root': { borderRadius: 2 } }}
        />
        <Button
          variant="contained"
          endIcon={loading ? <CircularProgress size={16} color="inherit" /> : <SendRoundedIcon />}
          onClick={handleAsk}
          disabled={loading || !question.trim()}
          sx={{ minWidth: 100, height: 56 }}
        >
          Ask
        </Button>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>{error}</Alert>}

      {/* Results */}
      {result && (
        <Box>
          {/* Answer card */}
          <Card
            sx={{
              mb: 2, bgcolor: 'background.paper',
              border: '1px solid rgba(33,150,243,0.25)',
            }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <AutoAwesomeRoundedIcon sx={{ color: '#2196f3', fontSize: 20 }} />
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>Answer</Typography>
                </Box>
                <Box sx={{ display: 'flex', gap: 0.75 }}>
                  {result.cache_hit && (
                    <Chip icon={<CachedRoundedIcon />} label="Cached" size="small" color="success" />
                  )}
                  <Chip label={`${Math.round(result.response_time_ms)}ms`} size="small" variant="outlined" />
                  <Chip label={`${result.retrieved_chunks?.length ?? 0} chunks`} size="small" variant="outlined" />
                </Box>
              </Box>
              <Typography
                variant="body1"
                sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.85, color: 'rgba(255,255,255,0.87)' }}
              >
                {result.answer}
              </Typography>
            </CardContent>
          </Card>

          {/* Citations */}
          {result.sources?.length > 0 && (
            <Card
              sx={{
                mb: 2, bgcolor: 'background.paper',
                border: '1px solid rgba(255,255,255,0.07)',
              }}
            >
              <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <FormatQuoteRoundedIcon sx={{ color: 'text.secondary', fontSize: 18 }} />
                  <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>Citations</Typography>
                </Box>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.75 }}>
                  {result.sources.map((s, i) => (
                    <Chip
                      key={i}
                      label={`${s.document_name}  —  Page ${s.page_number}`}
                      size="small"
                      color="primary"
                      variant="outlined"
                    />
                  ))}
                </Box>
              </CardContent>
            </Card>
          )}

          {/* Retrieved chunks accordion */}
          <RetrievedChunks chunks={result.retrieved_chunks} />
        </Box>
      )}
    </Box>
  );
}
