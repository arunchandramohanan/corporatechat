import React, { useState, useEffect } from 'react';
import { Typography, Box, Paper, Fade } from '@mui/material';
import ForumIcon from '@mui/icons-material/Forum';

const ExamplePrompts = ({ onSelectPrompt }) => {
  // State to hold the selected prompts
  const [selectedPrompts, setSelectedPrompts] = useState([]);
  
  // Expanded list of 50 example prompts focused on corporate card support
  const allExamplePrompts = [
    // Card Program Basics & Policy Queries
    "What types of corporate cards does BMO offer?",
    "How do I apply for a corporate card for my employees?",
    "What are the credit limits available for corporate cards?",
    "What's the difference between purchasing cards and corporate cards?",
    "What are the eligibility requirements for a corporate card?",
    "Can I get a corporate card with rewards programs?",

    // Card Activation & Setup
    "How do I activate a new corporate card?",
    "What's the process for setting up virtual cards?",
    "How do I add authorized users to my corporate card account?",
    "Can I set spending limits for individual cardholders?",
    "How do I set up online access for my corporate card?",
    "What's the process for issuing cards to new employees?",

    // Transaction Management & Disputes
    "How do I view my recent transactions?",
    "Why was my transaction declined?",
    "How do I dispute a charge on my corporate card?",
    "What's the process for reporting fraudulent transactions?",
    "Can I download transaction history for the past year?",
    "How long does it take to process a transaction dispute?",
    "What documentation is needed to file a dispute?",

    // Expense Management & Reporting
    "How do I download transaction reports for reconciliation?",
    "What expense categories can I use for tracking purchases?",
    "Can I export transaction data to my accounting software?",
    "How do I generate an expense report for tax purposes?",
    "What reports are available for expense policy compliance?",
    "How do I track employee spending across departments?",

    // Card Controls & Security
    "How do I temporarily block a lost or stolen card?",
    "Can I restrict certain merchant categories for employee cards?",
    "What security features are available for corporate cards?",
    "How do I set up transaction alerts and notifications?",
    "Can I set daily spending limits for my card?",
    "What fraud protection is included with my corporate card?",
    "How do I report a compromised card number?",

    // Payment & Billing
    "When are corporate card payments due each month?",
    "How do I set up automatic payments for my corporate card?",
    "What happens if I miss a payment deadline?",
    "Can I request a payment extension for my account?",
    "How do I view my current balance and available credit?",
    "What are the interest rates on outstanding balances?",

    // Travel & International Usage
    "Are there foreign transaction fees on BMO corporate cards?",
    "How do I notify BMO about international travel plans?",
    "What's the daily ATM withdrawal limit for corporate cards?",
    "Can I use my corporate card for online purchases?",
    "Does my card work in all countries?",
    "What travel insurance is included with my corporate card?",

    // Rewards & Benefits
    "What rewards programs are available for corporate cards?",
    "How do I redeem points earned on corporate card purchases?",
    "Does my corporate card include travel insurance?",
    "What purchase protection benefits come with my card?",
    "Can I transfer rewards points to airline programs?",
    "How do I check my current rewards balance?",

    // Account Management
    "How do I update my billing address for my corporate card?",
    "Can I increase my corporate card credit limit?",
    "How do I add or remove cardholders from my account?",
    "What's the process for closing a corporate card account?",
    "How do I change the primary account holder?",
    "Can I convert my card to a different card type?",

    // Digital & Mobile Banking
    "How do I add my corporate card to Apple Pay or Google Pay?",
    "Is there a mobile app for managing corporate cards?",
    "Can I view real-time transactions on my corporate card?",
    "How do I enable push notifications for card activity?",
    "Can I make payments through the mobile app?",

    // Compliance & Documentation
    "What documentation do I need for tax reporting purposes?",
    "How long are transaction records kept in the system?",
    "What are the corporate card usage policies?",
    "How do I ensure compliance with company expense policies?",

    // Technical Support & Troubleshooting
    "I'm having trouble logging into my corporate card portal. What should I do?",
    "My card was declined but I have available credit. Why?",
    "How do I reset my online banking password?",
    "The mobile app isn't syncing my transactions. How can I fix this?",
    "I didn't receive my new card. What should I do?",
    "How do I update my contact information for card notifications?"
  ];
  
  // Function to randomly select 4 prompts from the full list
  const selectRandomPrompts = () => {
    const shuffled = [...allExamplePrompts].sort(() => 0.5 - Math.random());
    return shuffled.slice(0, 4);
  };
  
  // Select random prompts on component mount
  useEffect(() => {
    setSelectedPrompts(selectRandomPrompts());
  }, []);

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
        {selectedPrompts.map((prompt, index) => (
          <Fade 
            key={index}
            in={true} 
            timeout={(index + 1) * 300}
            style={{ transitionDelay: `${index * 50}ms` }}
          >
            <Paper 
              elevation={1}
              onClick={() => onSelectPrompt(prompt)}
              sx={{ 
                p: 2.5, // Increased padding
                cursor: 'pointer', 
                borderRadius: 2,
                border: '2px solid #e0e0e0', // Changed to match the message bubbles
                backgroundColor: '#f2f8fc', // Changed to match user message bubble color
                flexBasis: 'calc(50% - 1rem)',
                minHeight: '4.5rem', // Increased height
                display: 'flex',
                alignItems: 'center',
              }}
            >
              <Typography 
                sx={{ 
                  color: '#000000',
                  lineHeight: 1.6,
                  fontWeight: 500, // Made bolder
                  fontSize: '16px', // Increased font size
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  display: '-webkit-box',
                  WebkitLineClamp: 2,
                  WebkitBoxOrient: 'vertical',
                }}
              >
                {prompt}
              </Typography>
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