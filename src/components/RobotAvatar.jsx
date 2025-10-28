import React from 'react';
import { Box } from '@mui/material';

const RobotAvatar = () => {
  return (
    <Box
      component="img"
      src="https://cdn-icons-png.flaticon.com/512/4712/4712109.png"
      alt="AI Robot"
      sx={{
        width: 120,
        height: 120,
        objectFit: 'contain',
        borderRadius: '10%',
      }}
    />
  );
};

export default RobotAvatar;
