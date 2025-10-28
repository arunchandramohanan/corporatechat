
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
      <Typography variant="caption" color="textSecondary">
        <Box component="span" fontWeight="bold">Disclaimer:</Box>
        {" "}The Rovr AI bot is an automated system powered by Microsoft Azure AI. The Rovr AI is intended to provide access to  Insurance Underwriting documentation and results are for reference only. Results are not a substitute for professional advice and should be used as a starting point only. Information should be verified from trusted sources.
      </Typography>
 
    </Paper>
  );
};

export default Disclaimer;
