import React from 'react';
import {
  Box, Typography, Accordion, AccordionSummary, AccordionDetails, Chip,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

export default function RetrievedChunks({ chunks }) {
  if (!chunks || chunks.length === 0) return null;

  return (
    <Box sx={{ mt: 2 }}>
      <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1.5 }}>
        Retrieved Chunks ({chunks.length})
      </Typography>
      {chunks.map((chunk, idx) => (
        <Accordion
          key={chunk.chunk_id}
          disableGutters
          sx={{
            bgcolor: 'background.paper',
            border: '1px solid rgba(255,255,255,0.07)',
            borderRadius: '8px !important',
            mb: 1,
            '&:before': { display: 'none' },
            '&.Mui-expanded': { borderColor: 'rgba(33,150,243,0.3)' },
          }}
        >
          <AccordionSummary expandIcon={<ExpandMoreIcon sx={{ color: 'text.secondary' }} />}>
            <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', flexWrap: 'wrap' }}>
              <Typography variant="body2" sx={{ fontWeight: 600, mr: 0.5 }}>
                #{idx + 1}
              </Typography>
              <Chip label={chunk.document_name} size="small" variant="outlined" sx={{ maxWidth: 180 }} />
              <Chip label={`Page ${chunk.page_number}`} size="small" color="primary" variant="outlined" />
              <Chip
                label={`Score: ${chunk.score}`}
                size="small"
                sx={{ bgcolor: 'rgba(124,58,237,0.12)', color: '#a78bfa', border: '1px solid rgba(124,58,237,0.3)' }}
              />
            </Box>
          </AccordionSummary>
          <AccordionDetails sx={{ pt: 0 }}>
            <Typography
              variant="body2"
              sx={{
                whiteSpace: 'pre-wrap', color: 'text.secondary',
                lineHeight: 1.75, borderTop: '1px solid rgba(255,255,255,0.07)', pt: 1.5,
              }}
            >
              {chunk.text}
            </Typography>
          </AccordionDetails>
        </Accordion>
      ))}
    </Box>
  );
}
