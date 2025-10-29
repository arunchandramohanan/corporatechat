import React from 'react';
import { Box, Paper, Typography, Fade } from '@mui/material';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import AgentBadge from './AgentBadge';

const AgentHandoff = ({ handoff, index }) => {
  if (!handoff) return null;

  const { from_agent, to_agent, reason, timestamp } = handoff;

  return (
    <Fade in={true} timeout={500} style={{ transitionDelay: `${index * 100}ms` }}>
      <Paper
        elevation={0}
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 1.5,
          p: 1.5,
          my: 1,
          backgroundColor: '#f8f9fa',
          border: '1px solid #e0e0e0',
          borderRadius: 2,
          transition: 'all 0.3s ease',
          '&:hover': {
            backgroundColor: '#f0f2f5',
            borderColor: '#1976d2',
            transform: 'translateX(4px)'
          }
        }}
      >
        <AgentBadge agentName={from_agent} variant="minimal" size="small" />

        <ArrowForwardIcon
          sx={{
            fontSize: 20,
            color: '#1976d2',
            animation: 'pulse 2s ease-in-out infinite',
            '@keyframes pulse': {
              '0%, 100%': { opacity: 0.6 },
              '50%': { opacity: 1 }
            }
          }}
        />

        <AgentBadge agentName={to_agent} variant="minimal" size="small" />

        <Box sx={{ flex: 1, ml: 1 }}>
          <Typography
            variant="caption"
            sx={{
              color: '#546e7a',
              fontSize: '0.75rem',
              fontStyle: 'italic',
              display: 'block'
            }}
          >
            {reason || 'Collaborating on your request'}
          </Typography>
        </Box>
      </Paper>
    </Fade>
  );
};

export default AgentHandoff;
