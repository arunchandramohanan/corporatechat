import React, { useState, useEffect } from 'react';
import { Typography, Box, Paper, Fade } from '@mui/material';
import ForumIcon from '@mui/icons-material/Forum';

const ExamplePrompts = ({ onSelectPrompt }) => {
  // State to hold the selected prompts
  const [selectedPrompts, setSelectedPrompts] = useState([]);
  
  // Expanded list of 50 example prompts focused on underwriting questions
  const allExamplePrompts = [
    // Age and Amount Requirements
    "My client is applying for Universal Life. What underwriting requirements are needed?",
    "What medical requirements are needed for a senior applying for Preferred Term?",
    "My client wants Critical Illness coverage. What tests will be required?",
    
    // Smoking Status & Preferred Ratings
    "My client smokes cigars occasionally. Can they qualify for non-smoker rates?",
    "My client quit smoking recently but still uses nicotine gum. What's their smoking status?",
    "What's the difference between Preferred Plus and Preferred non-smoker requirements?",
    "My client stopped using marijuana several years ago. Can they get Preferred Plus rates?",
    
    // Medical History & Conditions
    "My client has Type 2 diabetes controlled with medication. What rating can they expect?",
    "My client had a heart attack years ago but has been stable since. Are they insurable?",
    "My client has sleep apnea and uses a CPAP machine. How will this affect their application?",
    "My client takes medication for high blood pressure. Will they qualify for Preferred rates?",
    "My client had bariatric surgery and lost significant weight. How will this be viewed?",
    "My client has asthma controlled with an inhaler. What's the underwriting outlook?",
    
    // Family History
    "My client's father died of a heart attack at a young age. How does this affect Preferred eligibility?",
    "My client has siblings with cancer diagnosed before age 60. Can they get Preferred rates?",
    "What family history would disqualify someone from Preferred Plus rates?",
    
    // Build/Height/Weight
    "Does my client meet Preferred build requirements with their current height and weight?",
    "What's the maximum weight for Preferred Plus at average height?",
    "My client is slightly over the Preferred build table. What options do they have?",
    
    // Blood Pressure & Cholesterol
    "My client has elevated blood pressure on medication. Can they get Preferred rates?",
    "What cholesterol levels are acceptable for Preferred Plus?",
    "My client has high cholesterol. What classification can they expect?",
    
    // Occupational Ratings
    "My client is a commercial pilot. Will there be an occupational rating?",
    "My client works as a police officer. Is this considered high-risk?",
    "My client is a firefighter applying for coverage. What rating should I expect?",
    "My client works offshore on oil rigs. Will this affect their application?",
    
    // Aviation & Recreational Activities
    "My client is a student pilot. What aviation questionnaire is needed?",
    "My client skydives recreationally. Will this require a rating?",
    "My client rock climbs and does mountaineering. How will this affect their rating?",
    "My client scuba dives to significant depths. What information is needed?",
    
    // DUI/Motor Vehicle
    "My client had a DUI several years ago with no other incidents. How will this be rated?",
    "My client has multiple speeding tickets in recent years. Will this affect Preferred eligibility?",
    "What's the policy on motor vehicle violations for Preferred classes?",
    
    // Financial Underwriting
    "My client wants substantial coverage with modest income. Will financial documentation be required?",
    "What financial proof is needed for a high-value Universal Life application?",
    "My client is self-employed. What income verification will be accepted?",
    "For business insurance, what's the maximum amount for key person coverage?",
    
    // Critical Illness Specific
    "My client was treated for depression in the past. Can they get Critical Illness coverage?",
    "What conditions automatically disqualify someone from Critical Illness insurance?",
    "My client has a family history of hereditary disease. Are they eligible for CI?",
    "What's the maximum Critical Illness coverage that will be considered?",
    
    // Foreign Travel & Residency
    "My client travels to developing countries frequently for work. How will this be rated?",
    "My client is a permanent resident who arrived recently. What coverage is available?",
    "My client works under a Provincial Nominee Program. What are their insurance options?",

    
    // APS & Medical Requirements
    "When will an Attending Physician's Statement be automatically ordered?",
    "My client saw their doctor recently for a check-up. Will an APS be required?",
    "My client has a specialist appointment soon. Should we wait to apply?",
    "What medical conditions typically trigger an APS request?",
    
    // Policy Changes & Reinstatement
    "My client wants to change from smoker to non-smoker status. What's required?",
    "My client's policy lapsed. What's needed for reinstatement?",
    "My client wants to add a Critical Illness rider to their existing Universal Life policy. What's required?",
    "Can my client add a term rider without full underwriting?",
    
    // Temporary Insurance Agreement
    "What's the maximum coverage available under the Temporary Insurance Agreement?",
    "My client paid first premium with their application. When does TIA coverage begin?",
    "Under what circumstances would Temporary Insurance Agreement coverage be terminated?",
    
    // Special Situations
    "My client is applying for coverage on their child. What are the requirements?",
    "My client wants life insurance for charitable giving purposes. How is this evaluated?",
    "My client is a non-working spouse. What coverage amounts will be considered?",
    "My client is a recent university graduate with no income. What options are available?",
    
    // Product-Specific Questions
    "What's the difference in underwriting between Preferred Term options?",
    "My client is a senior. What products are still available to them?",
    "What's the maximum issue age for Universal Life products?",
    "Can my client get simplified issue insurance if they already have existing coverage?"
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