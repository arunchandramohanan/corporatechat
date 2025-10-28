
import React from 'react';
import { AppBar, Toolbar, Typography, Box, Link } from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';

const Header = () => {
  return (
    <AppBar position="static" sx={{ bgcolor: '#0079C1' }}>
      <Toolbar>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Typography variant="h6" component="div" sx={{ mr: 2, color: 'white', fontWeight: 'bold' }}>
            
          </Typography>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1, color: 'white' }}>
            Rovr AI
          </Typography>
        </Box>
        <Box sx={{ flexGrow: 1 }}></Box>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Link color="inherit" underline="hover" sx={{ color: 'white' }}>
            FAQ
          </Link>
          <Typography color="white">|</Typography>
          <Link color="inherit" underline="hover" sx={{ color: 'white' }}>
            Feedback or Need Help?
          </Link>
          <Typography color="white">|</Typography>
          <Link color="inherit" underline="hover" sx={{ color: 'white' }}>
            Français
          </Link>
          <EditIcon sx={{ ml: 2, color: 'white' }} />
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Header;
