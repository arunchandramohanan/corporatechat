import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Box, Typography, Paper, Button, IconButton, Fade, Zoom, Drawer, List, ListItem, ListItemText, ListItemButton, ListItemIcon, Divider } from '@mui/material';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import AddIcon from '@mui/icons-material/Add';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import ChatIcon from '@mui/icons-material/Chat';
import Header from './Header';
import RobotAvatar from './RobotAvatar';
import ChatMessage from './ChatMessage';
import ExamplePrompts from './ExamplePrompts';
import ChatInput from './ChatInput';
import Disclaimer from './Disclaimer';
import { API_CONFIG } from '../config/api';

// Chat session management - stored in frontend
const STORAGE_KEY = 'chatbot_sessions';

// Load chat sessions from localStorage or initialize empty
const loadChatSessions = () => {
  try {
    const storedSessions = localStorage.getItem(STORAGE_KEY);
    if (storedSessions) {
      return JSON.parse(storedSessions);
    }
  } catch (error) {
    console.error('Error loading chat sessions:', error);
  }
  // Return empty array if no sessions found or error occurred
  return [];
};

const ChatbotApp = () => {
  const [messages, setMessages] = useState([]);
  const [showExamples, setShowExamples] = useState(true);
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);
  const [context, setContext] = useState({});
  const [followUpOptions, setFollowUpOptions] = useState([]);
  const [quote, setQuote] = useState(null);
  const [leftPanelOpen, setLeftPanelOpen] = useState(false);
  const [chatSessions, setChatSessions] = useState(loadChatSessions);
  const [activeSessionId, setActiveSessionId] = useState(null);

  const toggleLeftPanel = useCallback(() => {
    setLeftPanelOpen(prev => !prev);
  }, []);

  // Save chat sessions to localStorage whenever they change
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(chatSessions));
    } catch (error) {
      console.error('Error saving chat sessions:', error);
    }
  }, [chatSessions]);

  // Save current chat state to session storage
  const saveChatState = useCallback(() => {
    if (!activeSessionId) return;

    setChatSessions(prev => prev.map(session =>
      session.id === activeSessionId
      ? {
          ...session,
          messages: messages, // These are the current messages in state
          context: context, // Current context in state
          followUpOptions: followUpOptions // Current followUpOptions in state
        }
      : session
    ));
  }, [activeSessionId, messages, context, followUpOptions]);


  const handleNewChat = useCallback(() => {
    const newSession = {
      id: Date.now(), // Simple unique ID
      title: "New Conversation",
      timestamp: new Date().toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      }),
      messages: [],
      context: {},
      followUpOptions: []
    };
    setChatSessions(prev => [newSession, ...prev]);
    setActiveSessionId(newSession.id); // This will trigger the loading useEffect
    // Resetting UI state directly here is fine as it's a new chat
    setMessages([]);
    setShowExamples(true);
    setContext({});
    setFollowUpOptions([]);
    setQuote(null);
  }, []); // setChatSessions, setActiveSessionId etc. are stable

  // Initialize with a new chat session or set active from existing
  useEffect(() => {
    if (chatSessions.length === 0) {
      handleNewChat();
    } else if (!activeSessionId && chatSessions.length > 0) {
      // If there's no active session ID set (e.g., on first load with existing sessions)
      // set the most recent chat as active.
      setActiveSessionId(chatSessions[0].id);
    }
    // The actual loading of chat data for activeSessionId is handled by the useEffect below.
  }, []); // eslint-disable-line react-hooks/exhaustive-deps
  // Using empty dependency array is intentional as this should only run once on mount logic.

  // Effect to load chat data when activeSessionId changes or chatSessions list updates (e.g. initial load)
  useEffect(() => {
    if (activeSessionId) {
      const activeChat = chatSessions.find(session => session.id === activeSessionId);
      if (activeChat) {
        setMessages(activeChat.messages || []);
        setContext(activeChat.context || {});
        setFollowUpOptions(activeChat.followUpOptions || []);
        setShowExamples((activeChat.messages || []).length === 0);
        // Quote is not typically stored per session in this setup, but reset if needed
        // setQuote(activeChat.quote || null); 
      } else if (chatSessions.length > 0) {
         // Active ID points to a session that no longer exists, select first available
         setActiveSessionId(chatSessions[0].id);
      } else {
        // Active ID exists but no sessions, implies we need a new one
        handleNewChat();
      }
    } else if (chatSessions.length > 0) {
        // No active ID, but sessions exist (e.g. after deleting all, then one is added by some other means)
        setActiveSessionId(chatSessions[0].id);
    } else {
        // No active ID and no sessions, make a new one (should be caught by init useEffect mostly)
        handleNewChat();
    }
  }, [activeSessionId, chatSessions, handleNewChat]);


  const handleClearChat = useCallback(() => {
    if (!activeSessionId) return;
    setChatSessions(prev => prev.map(session =>
      session.id === activeSessionId
      ? { ...session, messages: [], context: {}, followUpOptions: [] }
      : session
    ));
    // UI state will be updated by the useEffect listening to activeSessionId & chatSessions,
    // or we can set them directly for immediate feedback:
    setMessages([]);
    setShowExamples(true);
    setContext({});
    setFollowUpOptions([]);
    setQuote(null);
  }, [activeSessionId]);

  const handleSelectChat = useCallback((sessionId) => {
    if (sessionId === activeSessionId) return;
    if (activeSessionId) {
      saveChatState(); // Save state of the chat we are leaving
    }
    setActiveSessionId(sessionId); // Change active session, useEffect will load its data
  }, [activeSessionId, saveChatState]);

  // Save chat state before unloading
  useEffect(() => {
    const handleBeforeUnload = () => {
      saveChatState();
    };
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [saveChatState]);

  const handleDeleteSession = useCallback((sessionIdToDelete, event) => {
    event.stopPropagation();
    const currentActiveId = activeSessionId;

    setChatSessions(prevSessions => {
      const updatedSessions = prevSessions.filter(session => session.id !== sessionIdToDelete);
      if (sessionIdToDelete === currentActiveId) {
        if (updatedSessions.length > 0) {
          setActiveSessionId(updatedSessions[0].id); // useEffect will load this
        } else {
          handleNewChat(); // This will create a new session and set it as active
        }
      }
      return updatedSessions;
    });
  }, [activeSessionId, handleNewChat]); // Dependencies


  const handleSendMessage = useCallback(async (text) => {
    const newUserMessage = { text, isUser: true };

    // Optimistically update UI with user's message
    setMessages(prevMessages => [...prevMessages, newUserMessage]);
    setShowExamples(false);
    setIsTyping(true); // Show typing indicator

    // Prepare data for API: use the `messages` state from closure (before adding newUserMessage) and append newUserMessage
    const messagesForApi = [...messages, newUserMessage];
    const currentContextForApi = context; // Capture context from closure for the API call

    let sessionTitleUpdatePayload = {};
    // Determine if session title needs update (i.e., if this is the first message)
    if (messages.length === 0 && activeSessionId) { 
        sessionTitleUpdatePayload.title = text.length > 30 ? `${text.substring(0, 27)}...` : text;
    }

    try {
      const response = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.CHAT}`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({
          messages: messagesForApi, // Send the user message included
          context: currentContextForApi // Send current context
        }),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json(); // Bot's response { text, isUser, context, followUpOptions, quote }

      // Update UI with bot's message. `prevMessages` will include the user's message from the first `setMessages` call.
      setMessages(prevMessages => [...prevMessages, data]);
      setContext(data.context || {});
      setFollowUpOptions(data.followUpOptions || []);
      setQuote(data.quote);

      // Update the session in chatSessions state ONCE with all new information
      setChatSessions(prevSessions => prevSessions.map(session =>
        session.id === activeSessionId
        ? {
            ...session,
            ...sessionTitleUpdatePayload, // Apply title update here
            messages: [...messagesForApi, data], // Persist full chat history
            context: data.context || {},
            followUpOptions: data.followUpOptions || []
          }
        : session
      ));
    } catch (error) {
      console.error('Error:', error);
      const errorMessage = {
         text: 'Sorry, there was an error processing your request. Please try again.',
         isUser: false
       };
      // Update UI to show error message. `prevMessages` includes the user's message.
      setMessages(prevMessages => [...prevMessages, errorMessage]);
      
      // Update session with error message, still applying title update if applicable
      setChatSessions(prevSessions => prevSessions.map(session =>
        session.id === activeSessionId
        ? { 
            ...session, 
            ...sessionTitleUpdatePayload, // Apply title update
            messages: [...messagesForApi, errorMessage] // Persist user message + error message
          }
        : session
      ));
    } finally {
      setIsTyping(false);
    }
  }, [messages, context, activeSessionId, API_CONFIG.BASE_URL, API_CONFIG.ENDPOINTS.CHAT, setMessages, setShowExamples, setIsTyping, setContext, setFollowUpOptions, setQuote, setChatSessions]); // Added all relevant dependencies

  const handleSelectPrompt = useCallback((prompt) => {
    handleSendMessage(prompt);
  }, [handleSendMessage]);

  // Scroll to bottom whenever messages change or typing indicator appears/disappears
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  return (
    <Box sx={{
       height: '100vh',
       background: '#ffffff',
      display: 'flex',
      flexDirection: 'column',
       width: '100%',
      overflow: 'hidden'
    }}>
      {/* Header */}
      <Box sx={{
         borderBottom: '1px solid rgba(0,0,0,0.08)',
         p: 1,
        backgroundColor: '#ffffff'
       }}>
        <Header />
      </Box>
      {/* Container for Drawer and Main Chat Area */}
      <Box sx={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Left Panel */}
        <Box
          sx={{
            width: leftPanelOpen ? 280 : 56,
            flexShrink: 0,
            position: 'relative',
            transition: (theme) => theme.transitions.create('width', {
              easing: theme.transitions.easing.sharp,
              duration: theme.transitions.duration.enteringScreen,
            }),
            borderRight: '1px solid rgba(0,0,0,0.08)',
            background: '#ffffff',
            height: '100%',
            zIndex: 1,
            overflow: 'visible',
          }}
        >
          <Drawer
            variant="persistent"
            anchor="left"
            open={true}
            sx={{
              width: '100%',
              height: '100%',
              '& .MuiDrawer-paper': {
                position: 'static',
                width: '100%',
                boxSizing: 'border-box',
                background: '#ffffff',
                borderRight: 'none',
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'flex-start',
                alignItems: leftPanelOpen ? 'stretch' : 'center',
                overflow: 'hidden',
              },
            }}
          >
            {!leftPanelOpen && (
              <Box
                 sx={{
                   display: 'flex',
                   flexDirection: 'column',
                   alignItems: 'center',
                  width: '100%',
                  pt: 2
                }}
              >
                <IconButton
                   onClick={toggleLeftPanel}
                  aria-label="Expand panel"
                   sx={{ color: '#546e7a', mb: 2 }}
                >
                  <ChevronRightIcon />
                </IconButton>
                <IconButton
                   onClick={handleNewChat}
                  aria-label="New chat"
                  sx={{ color: '#1e88e5', mb: 2 }}
                >
                  <AddIcon />
                </IconButton>
                <Box sx={{ mt: 1 }}>
                  {chatSessions.slice(0, 5).map((chat) => ( // Corrected: chatSessions
                    <IconButton
                       key={chat.id}
                      onClick={() => handleSelectChat(chat.id)}
                      sx={{
                         color: activeSessionId === chat.id ? '#1e88e5' : '#757575', // Corrected: activeSessionId
                        display: 'block',
                        mb: 1
                      }}
                    >
                      <ChatIcon fontSize="small" />
                    </IconButton>
                  ))}
                </Box>
              </Box>
            )}
            {leftPanelOpen && (
              <>
                <Box sx={{
                   p: 2,
                   display: 'flex',
                   alignItems: 'center',
                   justifyContent: 'space-between',
                  minHeight: 64,
                  flexShrink: 0
                }}>
                  <Typography variant="h6" sx={{ fontWeight: 600, color: '#1e88e5', flexShrink: 0 }}>Chat History</Typography>
                  <IconButton onClick={toggleLeftPanel} size="small" sx={{ color: '#546e7a', flexShrink: 0 }}>
                    <ChevronLeftIcon />
                  </IconButton>
                </Box>
                <Box sx={{ p: 1, flexShrink: 0 }}>
                  <Button
                    variant="contained"
                    fullWidth
                    startIcon={<AddIcon />}
                    onClick={handleNewChat}
                    sx={{
                      borderRadius: 2,
                      textTransform: 'none',
                      fontWeight: 600,
                      mb: 2,
                      bgcolor: '#1e88e5',
                      '&:hover': { bgcolor: '#1976d2' }
                    }}
                  >
                    New Chat
                  </Button>
                  <Button
                     variant="outlined"
                     color="error"
                     onClick={handleClearChat}
                    startIcon={<DeleteOutlineIcon />}
                    fullWidth
                    sx={{
                       borderRadius: 2,
                      textTransform: 'none',
                      fontWeight: 600,
                      mb: 2
                    }}
                  >
                    Clear Current Chat
                  </Button>
                </Box>
                <Divider />
                <List sx={{ overflow: 'auto', flex: 1 }}>
                  {chatSessions.map((session) => (
                    <ListItemButton
                       key={session.id}
                       selected={activeSessionId === session.id}
                      onClick={() => handleSelectChat(session.id)}
                      sx={{
                        borderRadius: 1,
                        mx: 1,
                        '&.Mui-selected': {
                          backgroundColor: 'rgba(30, 136, 229, 0.1)',
                          '&:hover': { backgroundColor: 'rgba(30, 136, 229, 0.15)' }
                        }
                      }}
                    >
                      <ListItemIcon sx={{ minWidth: 36 }}>
                        <ChatIcon fontSize="small" color="primary" />
                      </ListItemIcon>
                      <ListItemText
                         primary={session.title}
                         secondary={session.timestamp}
                        primaryTypographyProps={{ noWrap: true, fontWeight: 500 }}
                        secondaryTypographyProps={{ noWrap: true, fontSize: '0.75rem' }}
                      />
                      <IconButton
                         onClick={(e) => handleDeleteSession(session.id, e)}
                        size="small"
                        edge="end"
                        aria-label="delete"
                        sx={{
                           opacity: 0.6,
                          '&:hover': { opacity: 1, color: 'error.main' }
                        }}
                      >
                        <DeleteOutlineIcon fontSize="small" />
                      </IconButton>
                    </ListItemButton>
                  ))}
                </List>
              </>
            )}
          </Drawer>
        </Box>
        {/* Main Chat Interface */}
        <Box sx={{
           display: 'flex',
          flexDirection: 'column',
          flex: 1,
          overflow: 'hidden',
          height: '100%'
        }}>
          {/* Messages area - Adjusted to have proper spacing */}
          <Box sx={{
             display: 'flex',
             flexDirection: 'column',
             py: 1,
             px: { xs: 1, sm: 2 },
             overflow: 'auto',
             flex: 1,
             maxHeight: 'calc(100% - 140px)', // Increased height reduction to make more space for input
             mb: 3 // Add bottom margin to create more space above input
          }}>
            {messages.length === 0 && (
              <Zoom in={messages.length === 0}>
                <Box sx={{
                   display: 'flex',
                   flexDirection: 'column',
                   alignItems: 'center',
                   justifyContent: 'center',
                  py: 2,
                  px: 2,
                  background: '#ffffff',
                  borderBottom: '1px solid rgba(0,0,0,0.05)'
                }}>
                  <Box sx={{ mb: 0.5 }}>
                    <RobotAvatar />
                  </Box>
                  <Typography variant="h4" sx={{
                     mt: 1,
                    fontWeight: 600,
                    color: '#1e88e5',
                    fontSize: '24px'
                  }}>
                    Rovr AI
                  </Typography>
                  <Typography
                     variant="body1"
                     align="center"
                     sx={{
                       mt: 1,
                      maxWidth: '80%',
                      color: '#546e7a',
                      fontWeight: 500,
                      fontSize: '15px',
                      lineHeight: 1.5
                    }}
                  >
                    Hello! I'm your BMO Insurance assistant. I can help you with insurance questions and underwriting guidelines.
                  </Typography>
                </Box>
              </Zoom>
            )}
            <Box sx={{ display: 'flex', flexDirection: 'column', flex: 1 }}>
              {messages.length > 0 && (
                <Box
                   sx={{
                     flex: 1,
                    overflow: 'auto',
                    p: 2,
                    display: 'flex',
                    flexDirection: 'column',
                    minHeight: '200px', // Ensure some min height
                    bgcolor: '#ffffff',
                    pb: 5 // Increased bottom padding to ensure more space between messages and input
                  }}
                >
                  {messages.map((msg, index) => (
                    <Fade key={index} in={true} timeout={500}>
                      <Box>
                        <ChatMessage text={msg.text} isUser={msg.isUser} />
                      </Box>
                    </Fade>
                  ))}
                  {isTyping && (
                    <Fade in={isTyping} timeout={300}>
                      <Box>
                        <ChatMessage isUser={false} isTyping={true} botName="Rovr AI" />
                      </Box>
                    </Fade>
                  )}
                  <div ref={messagesEndRef} />
                </Box>
              )}
              {showExamples &&
                <Box sx={{
                   mb: 2,
                   mt: messages.length === 0 ? 0 : 2, // Adjust margin based on messages
                  px: 2,
                  overflow: 'visible' // Ensure prompts aren't clipped if they have shadows/borders
                }}>
                  <ExamplePrompts onSelectPrompt={handleSelectPrompt} />
                </Box>
              }
            </Box>
          </Box>
          
          {/* Fixed Input Area - Now properly separated from the messages */}
          <Box 
            sx={{
              py: 2,
              px: { xs: 1, sm: 2 },
              background: '#ffffff',
              backdropFilter: 'blur(10px)',
              borderTop: '1px solid rgba(0,0,0,0.05)',
              width: '100%',
              position: 'relative', // Ensure this stays at the bottom
              bottom: 0,
              mt: 'auto', // Push to bottom if flex space available
              flexShrink: 0 // Don't allow this to shrink
            }}
          >
            <Box sx={{ width: '100%', maxWidth: '100%' }}> 
              <ChatInput onSendMessage={handleSendMessage} />
            </Box>
          </Box>
          
          <Disclaimer />
        </Box>
      </Box>
    </Box>
  );
};

export default ChatbotApp;