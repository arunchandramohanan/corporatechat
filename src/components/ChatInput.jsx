
import React, { useState } from 'react';
import { Paper, InputBase, IconButton, Box } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import SearchIcon from '@mui/icons-material/Search';

const ChatInput = ({ onSendMessage }) => {
  const [message, setMessage] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (message.trim()) {
      onSendMessage(message);
      setMessage('');
    }
  };

  return (
    <Box sx={{ position: 'fixed', bottom: 120, left: 0, right: 0, px: 3 }}>
      <Paper
        component="form"
        onSubmit={handleSubmit}
        elevation={2}
        sx={{
          p: '2px 4px',
          display: 'flex',
          alignItems: 'center',
          width: '100%',
          borderRadius: 20,
          border: '1px solid #e0e0e0',
        }}
      >
        <IconButton sx={{ p: '10px' }} aria-label="search">
          <SearchIcon />
        </IconButton>
        <InputBase
          sx={{ ml: 1, flex: 1 }}
          placeholder="Type your question here"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
        />
        <IconButton 
          type="submit" 
          sx={{ p: '10px', color: '#0079C1' }} 
          aria-label="send"
          disabled={!message.trim()}
        >
          <SendIcon />
        </IconButton>
      </Paper>
    </Box>
  );
};

export default ChatInput;
