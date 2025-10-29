import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  Divider,
  Fade
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import BuildIcon from '@mui/icons-material/Build';
import PsychologyIcon from '@mui/icons-material/Psychology';
import AgentBadge from './AgentBadge';

const STEP_ICONS = {
  searching: '🔍',
  analyzing: '🧠',
  retrieving: '📥',
  generating: '✨',
  processing: '⚙️',
  checking: '✓',
  creating: '🎯',
  complete: '✅'
};

const getStepIcon = (action) => {
  const actionLower = action.toLowerCase();

  if (actionLower.includes('search')) return STEP_ICONS.searching;
  if (actionLower.includes('analyz')) return STEP_ICONS.analyzing;
  if (actionLower.includes('retriev')) return STEP_ICONS.retrieving;
  if (actionLower.includes('generat')) return STEP_ICONS.generating;
  if (actionLower.includes('process')) return STEP_ICONS.processing;
  if (actionLower.includes('check')) return STEP_ICONS.checking;
  if (actionLower.includes('creat')) return STEP_ICONS.creating;
  if (actionLower.includes('complete')) return STEP_ICONS.complete;

  return '▪️';
};

const AgentSteps = ({ steps, consultedAgents }) => {
  const [expanded, setExpanded] = useState(false);

  if (!steps || steps.length === 0) {
    return null;
  }

  // Group steps by agent
  const stepsByAgent = steps.reduce((acc, step) => {
    const agent = step.agent_name || 'Unknown';
    if (!acc[agent]) acc[agent] = [];
    acc[agent].push(step);
    return acc;
  }, {});

  return (
    <Fade in={true} timeout={500}>
      <Box sx={{ my: 2 }}>
        <Accordion
          expanded={expanded}
          onChange={(e, isExpanded) => setExpanded(isExpanded)}
          elevation={0}
          sx={{
            backgroundColor: '#f5f7fa',
            border: '1px solid #e0e0e0',
            borderRadius: '8px !important',
            '&:before': { display: 'none' },
            overflow: 'hidden'
          }}
        >
          <AccordionSummary
            expandIcon={<ExpandMoreIcon />}
            sx={{
              backgroundColor: '#ffffff',
              borderBottom: expanded ? '1px solid #e0e0e0' : 'none',
              '&:hover': {
                backgroundColor: '#fafbfc'
              }
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
              <PsychologyIcon sx={{ color: '#1976d2', fontSize: 24 }} />
              <Box sx={{ flex: 1 }}>
                <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#1976d2' }}>
                  How I Helped ({steps.length} steps)
                </Typography>
                <Typography variant="caption" sx={{ color: '#546e7a' }}>
                  {consultedAgents && consultedAgents.length > 1
                    ? `${consultedAgents.length} agents collaborated`
                    : 'Click to see reasoning process'}
                </Typography>
              </Box>
              {consultedAgents && consultedAgents.length > 0 && (
                <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                  {consultedAgents.map((agent, idx) => (
                    <AgentBadge key={idx} agentName={agent} variant="minimal" size="small" showIcon={false} />
                  ))}
                </Box>
              )}
            </Box>
          </AccordionSummary>

          <AccordionDetails sx={{ p: 2 }}>
            {Object.entries(stepsByAgent).map(([agentName, agentSteps], agentIdx) => (
              <Box key={agentIdx} sx={{ mb: agentIdx < Object.keys(stepsByAgent).length - 1 ? 3 : 0 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5 }}>
                  <AgentBadge agentName={agentName} variant="minimal" size="small" />
                  <Chip
                    label={`${agentSteps.length} steps`}
                    size="small"
                    sx={{ height: 20, fontSize: '0.7rem' }}
                  />
                </Box>

                <Box sx={{ pl: 2, borderLeft: '2px solid #e0e0e0' }}>
                  {agentSteps.map((step, stepIdx) => (
                    <Fade
                      key={stepIdx}
                      in={expanded}
                      timeout={300}
                      style={{ transitionDelay: `${stepIdx * 50}ms` }}
                    >
                      <Box
                        sx={{
                          mb: 1.5,
                          pl: 2,
                          position: 'relative',
                          '&:before': {
                            content: '""',
                            position: 'absolute',
                            left: -6,
                            top: 6,
                            width: 10,
                            height: 10,
                            borderRadius: '50%',
                            backgroundColor: stepIdx === agentSteps.length - 1 ? '#4caf50' : '#1976d2',
                            border: '2px solid white',
                            boxShadow: '0 0 0 2px #e0e0e0'
                          }
                        }}
                      >
                        <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                          <Typography
                            component="span"
                            sx={{ fontSize: '1rem', lineHeight: '1.5' }}
                          >
                            {getStepIcon(step.action)}
                          </Typography>
                          <Box sx={{ flex: 1 }}>
                            <Typography
                              variant="body2"
                              sx={{
                                fontWeight: 500,
                                color: '#212121',
                                mb: 0.5
                              }}
                            >
                              {step.details}
                            </Typography>

                            {step.tool_used && (
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: 0.5 }}>
                                <BuildIcon sx={{ fontSize: 14, color: '#757575' }} />
                                <Typography variant="caption" sx={{ color: '#757575', fontSize: '0.7rem' }}>
                                  Used: {step.tool_used}
                                </Typography>
                              </Box>
                            )}

                            {step.tool_output && Object.keys(step.tool_output).length > 0 && (
                              <Paper
                                elevation={0}
                                sx={{
                                  mt: 0.5,
                                  p: 1,
                                  backgroundColor: '#f8f9fa',
                                  border: '1px solid #e0e0e0',
                                  borderRadius: 1,
                                  fontSize: '0.7rem'
                                }}
                              >
                                <Typography variant="caption" sx={{ color: '#546e7a', fontFamily: 'monospace' }}>
                                  {JSON.stringify(step.tool_output, null, 2).slice(0, 200)}
                                  {JSON.stringify(step.tool_output).length > 200 && '...'}
                                </Typography>
                              </Paper>
                            )}
                          </Box>
                        </Box>
                      </Box>
                    </Fade>
                  ))}
                </Box>

                {agentIdx < Object.keys(stepsByAgent).length - 1 && (
                  <Divider sx={{ my: 2 }} />
                )}
              </Box>
            ))}

            <Box
              sx={{
                mt: 2,
                pt: 2,
                borderTop: '1px solid #e0e0e0',
                display: 'flex',
                alignItems: 'center',
                gap: 1
              }}
            >
              <CheckCircleIcon sx={{ color: '#4caf50', fontSize: 20 }} />
              <Typography variant="caption" sx={{ color: '#4caf50', fontWeight: 600 }}>
                Response generated successfully
              </Typography>
            </Box>
          </AccordionDetails>
        </Accordion>
      </Box>
    </Fade>
  );
};

export default AgentSteps;
