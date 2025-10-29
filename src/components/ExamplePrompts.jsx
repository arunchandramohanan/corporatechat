import React, { useMemo } from 'react';
import { Typography, Box, Paper, Fade, Chip } from '@mui/material';
import ForumIcon from '@mui/icons-material/Forum';
import PolicyIcon from '@mui/icons-material/Policy';
import AccountBalanceIcon from '@mui/icons-material/AccountBalance';
import ReceiptIcon from '@mui/icons-material/Receipt';
import BarChartIcon from '@mui/icons-material/BarChart';
import SupportAgentIcon from '@mui/icons-material/SupportAgent';

const ExamplePrompts = ({ onSelectPrompt }) => {
  // Pool of prompts for each agent - one will be randomly selected per category
  const promptPool = {
    policy: [
      "What are the benefits and rewards of my BMO Corporate Card?",
      "What fees apply to my corporate card?",
      "How do I activate my new card?",
      "What is the foreign transaction fee policy?",
      "What insurance coverage comes with my card?",
      "Can I add authorized users to my account?",
      "What is the annual fee for my card?",
      "What are the credit limit policies?"
    ],
    account: [
      "What's my current balance and available credit?",
      "How do I update my account information?",
      "Show me my account summary",
      "What is my credit limit?",
      "How do I request a credit limit increase?",
      "What are my account settings?",
      "How do I set up spending alerts?",
      "Check my payment due date"
    ],
    transaction: [
      "Show me my recent transactions",
      "Find transactions from last week",
      "How do I dispute a charge?",
      "Show me pending transactions",
      "Download my transaction history",
      "Search for a specific transaction",
      "Show me all travel expenses",
      "How do I file a dispute?"
    ],
    analytics: [
      "Analyze my spending by category this month",
      "Show me my spending trends",
      "Generate an expense report",
      "Compare my spending to budget",
      "What are my top spending categories?",
      "Show me monthly spending analysis",
      "Track my budget vs actual spending",
      "Show me spending patterns over time"
    ],
    escalation: [
      "I want to speak to a manager",
      "File a complaint about a fee",
      "Report unauthorized charges",
      "I need help with a fraud case",
      "Escalate this issue to a supervisor",
      "Report suspicious activity on my account",
      "I'm not satisfied with the service",
      "Request a formal investigation"
    ]
  };

  // Randomly select 4 agents out of 5, then one prompt from each selected category
  const agentPrompts = useMemo(() => {
    const getRandomPrompt = (category) => {
      const prompts = promptPool[category];
      const randomIndex = Math.floor(Math.random() * prompts.length);
      return prompts[randomIndex];
    };

    // Define all 5 agents
    const allAgents = [
      {
        category: 'policy',
        agent: "Policy",
        icon: <PolicyIcon />,
        color: "#7c4dff"
      },
      {
        category: 'account',
        agent: "Account",
        icon: <AccountBalanceIcon />,
        color: "#00897b"
      },
      {
        category: 'transaction',
        agent: "Transaction",
        icon: <ReceiptIcon />,
        color: "#1e88e5"
      },
      {
        category: 'analytics',
        agent: "Analytics",
        icon: <BarChartIcon />,
        color: "#f4511e"
      },
      {
        category: 'escalation',
        agent: "Escalation",
        icon: <SupportAgentIcon />,
        color: "#e53935"
      }
    ];

    // Randomly select 4 out of 5 agents
    const shuffled = [...allAgents].sort(() => Math.random() - 0.5);
    const selectedAgents = shuffled.slice(0, 4);

    // Generate prompts for the selected agents
    return selectedAgents.map(agentConfig => ({
      text: getRandomPrompt(agentConfig.category),
      agent: agentConfig.agent,
      icon: agentConfig.icon,
      color: agentConfig.color
    }));
  }, []); // Empty dependency array ensures this runs once per component mount

  return (
    <Box sx={{ mb: 4 }}>
      <Box sx={{ 
        display: 'flex', 
        alignItems: 'center', 
        mb: 2.5,
        borderBottom: '2px solid #e0e0e0',
        pb: 1
      }}>
        <ForumIcon sx={{ 
          mr: 1.5, 
          color: '#1e88e5', // Changed to match the app's blue color theme
          fontSize: 28 // Increased size for better visibility
        }} />
        <Typography 
          sx={{ 
            fontWeight: 600,
            color: '#424242',
            letterSpacing: '0.5px',
            fontSize: '20px' // Increased font size
          }}
        >
          Try asking ...
        </Typography>
      </Box>
      
      <Box sx={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: 2,
        justifyContent: 'space-between'
      }}>
        {agentPrompts.map((promptObj, index) => (
          <Fade
            key={index}
            in={true}
            timeout={(index + 1) * 300}
            style={{ transitionDelay: `${index * 50}ms` }}
          >
            <Paper
              elevation={1}
              onClick={() => onSelectPrompt(promptObj.text)}
              sx={{
                p: 2.5,
                cursor: 'pointer',
                borderRadius: 2,
                border: '2px solid #e0e0e0',
                backgroundColor: '#f2f8fc',
                flexBasis: 'calc(50% - 1rem)',
                minHeight: '5rem',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                transition: 'all 0.2s ease-in-out',
                '&:hover': {
                  transform: 'translateY(-2px)',
                  boxShadow: 3,
                  borderColor: promptObj.color,
                }
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1.5 }}>
                <Box sx={{
                  color: promptObj.color,
                  display: 'flex',
                  alignItems: 'center',
                  mt: 0.5
                }}>
                  {promptObj.icon}
                </Box>
                <Typography
                  sx={{
                    color: '#000000',
                    lineHeight: 1.6,
                    fontWeight: 500,
                    fontSize: '16px',
                    flex: 1
                  }}
                >
                  {promptObj.text}
                </Typography>
              </Box>
              <Chip
                label={`${promptObj.agent} Agent`}
                size="small"
                sx={{
                  alignSelf: 'flex-start',
                  mt: 1,
                  backgroundColor: `${promptObj.color}15`,
                  color: promptObj.color,
                  fontWeight: 600,
                  fontSize: '11px',
                  height: '22px',
                  border: `1px solid ${promptObj.color}40`
                }}
              />
            </Paper>
          </Fade>
        ))}
      </Box>
      
      <Typography 
        sx={{ 
          display: 'block', 
          textAlign: 'center', 
          mt: 3,
          color: '#546e7a',
          fontStyle: 'italic',
          fontSize: '14px', // Slightly increased font size
          fontWeight: 500 // Made bolder
        }}
      >
        Click any prompt to start a conversation or type your own question
      </Typography>
    </Box>
  );
};

export default ExamplePrompts;