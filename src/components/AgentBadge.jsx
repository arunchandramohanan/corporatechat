import React from 'react';
import { Box, Chip, Tooltip } from '@mui/material';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import PolicyIcon from '@mui/icons-material/Policy';
import AccountBalanceIcon from '@mui/icons-material/AccountBalance';
import ReceiptIcon from '@mui/icons-material/Receipt';
import BarChartIcon from '@mui/icons-material/BarChart';
import SupportAgentIcon from '@mui/icons-material/SupportAgent';

const AGENT_CONFIG = {
  policy: {
    label: 'Policy Expert',
    color: '#1976d2',
    icon: PolicyIcon,
    description: 'Specializes in card policies, benefits, and program information'
  },
  account: {
    label: 'Account Manager',
    color: '#2e7d32',
    icon: AccountBalanceIcon,
    description: 'Handles account information, balances, and settings'
  },
  transaction: {
    label: 'Transaction Specialist',
    color: '#ed6c02',
    icon: ReceiptIcon,
    description: 'Manages transaction inquiries and disputes'
  },
  analytics: {
    label: 'Analytics Expert',
    color: '#9c27b0',
    icon: BarChartIcon,
    description: 'Provides spending analytics and reports'
  },
  escalation: {
    label: 'Escalation Manager',
    color: '#d32f2f',
    icon: SupportAgentIcon,
    description: 'Handles complex issues requiring human intervention'
  },
  legacy_agent: {
    label: 'AI Assistant',
    color: '#546e7a',
    icon: SmartToyIcon,
    description: 'General purpose assistant'
  }
};

const AgentBadge = ({ agentName, variant = 'standard', showIcon = true, size = 'small' }) => {
  const config = AGENT_CONFIG[agentName?.toLowerCase()] || AGENT_CONFIG.legacy_agent;
  const Icon = config.icon;

  if (variant === 'minimal') {
    return (
      <Tooltip title={config.description} arrow>
        <Chip
          icon={showIcon ? <Icon sx={{ fontSize: 16 }} /> : undefined}
          label={config.label}
          size={size}
          sx={{
            backgroundColor: `${config.color}15`,
            color: config.color,
            fontWeight: 600,
            fontSize: '0.75rem',
            height: size === 'small' ? 24 : 32,
            '& .MuiChip-icon': {
              color: config.color
            }
          }}
        />
      </Tooltip>
    );
  }

  return (
    <Tooltip title={config.description} arrow placement="top">
      <Box
        sx={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 0.5,
          px: 1.5,
          py: 0.5,
          borderRadius: 2,
          backgroundColor: `${config.color}10`,
          border: `1.5px solid ${config.color}40`,
          transition: 'all 0.2s ease',
          cursor: 'help',
          '&:hover': {
            backgroundColor: `${config.color}20`,
            transform: 'translateY(-1px)',
            boxShadow: `0 2px 8px ${config.color}30`
          }
        }}
      >
        {showIcon && <Icon sx={{ fontSize: 18, color: config.color }} />}
        <Box
          component="span"
          sx={{
            fontSize: '0.8rem',
            fontWeight: 600,
            color: config.color,
            letterSpacing: '0.3px'
          }}
        >
          {config.label}
        </Box>
      </Box>
    </Tooltip>
  );
};

export default AgentBadge;
