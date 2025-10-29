
import React from 'react';
import { Typography, Box, Paper } from '@mui/material';

const Disclaimer = () => {
  return (
    <Paper 
      elevation={0} 
      sx={{ 
        p: 2, 
        backgroundColor: '#f5f5f5', 
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        borderTop: '1px solid #e0e0e0',
        zIndex: 1000, // Ensure disclaimer stays on top
        maxHeight: '100px', // Control the height
        overflow: 'auto' // Add scrolling if content is too large
      }}
    >
      <Typography variant="caption" color="textSecondary" align="center">
        The Corporate Card AI bot is an automated system powered by AI. It is intended to provide access to BMO Corporate Card documentation and support resources.
      </Typography>
 
    </Paper>
  );
};

export default Disclaimer;
