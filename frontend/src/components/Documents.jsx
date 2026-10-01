import React, { useEffect, useState } from 'react';
import {
  Box, Typography, Button, Alert, CircularProgress, Chip,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper,
} from '@mui/material';
import CloudUploadRoundedIcon from '@mui/icons-material/CloudUploadRounded';
import { getDocuments, ingestDocuments } from '../api.js';

export default function Documents() {
  const [docs,      setDocs]      = useState([]);
  const [loading,   setLoading]   = useState(true);
  const [ingesting, setIngesting] = useState(false);
  const [message,   setMessage]   = useState('');
  const [error,     setError]     = useState('');

  const fetchDocs = () => {
    setLoading(true);
    getDocuments()
      .then((r) => setDocs(r.data.documents || []))
      .catch(() => setError('Failed to load documents. Is the backend running?'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchDocs(); }, []);

  const handleIngest = () => {
    setIngesting(true);
    setMessage('');
    setError('');
    ingestDocuments()
      .then((r) => { setMessage(r.data.message); fetchDocs(); })
      .catch((e) => setError(e.response?.data?.detail || 'Ingestion failed.'))
      .finally(() => setIngesting(false));
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h5" sx={{ fontWeight: 700 }}>Documents</Typography>
          <Typography variant="body2" color="text.secondary">
            Manage PDF ingestion from the <code>.pdf/</code> folder
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={ingesting ? <CircularProgress size={16} color="inherit" /> : <CloudUploadRoundedIcon />}
          onClick={handleIngest}
          disabled={ingesting}
          sx={{ minWidth: 160 }}
        >
          {ingesting ? 'Ingesting…' : 'Ingest Documents'}
        </Button>
      </Box>

      {message && <Alert severity="success" sx={{ mb: 2 }} onClose={() => setMessage('')}>{message}</Alert>}
      {error   && <Alert severity="error"   sx={{ mb: 2 }} onClose={() => setError('')}>{error}</Alert>}

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 8 }}>
          <CircularProgress />
        </Box>
      ) : docs.length === 0 ? (
        <Alert severity="info">
          No documents ingested yet. Place PDF files in the <code>.pdf/</code> folder then click
          <strong> Ingest Documents</strong>.
        </Alert>
      ) : (
        <TableContainer
          component={Paper}
          sx={{ bgcolor: 'background.paper', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 2 }}
        >
          <Table>
            <TableHead>
              <TableRow sx={{ '& th': { fontWeight: 700, borderBottom: '1px solid rgba(255,255,255,0.1)' } }}>
                <TableCell>#</TableCell>
                <TableCell>Document Name</TableCell>
                <TableCell align="center">Pages</TableCell>
                <TableCell align="center">Chunks</TableCell>
                <TableCell>Ingested At</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {docs.map((doc) => (
                <TableRow key={doc.id} hover>
                  <TableCell sx={{ color: 'text.secondary' }}>{doc.id}</TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Chip label="PDF" size="small" color="primary" variant="outlined" sx={{ fontSize: 10 }} />
                      <Typography variant="body2">{doc.filename}</Typography>
                    </Box>
                  </TableCell>
                  <TableCell align="center">{doc.page_count}</TableCell>
                  <TableCell align="center">
                    <Chip label={doc.chunk_count} size="small" sx={{ bgcolor: 'rgba(124,58,237,0.15)', color: '#a78bfa' }} />
                  </TableCell>
                  <TableCell>
                    <Typography variant="caption" color="text.secondary">
                      {new Date(doc.created_at).toLocaleString()}
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
