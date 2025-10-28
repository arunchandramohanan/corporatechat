import React, { useState } from 'react';
import { API_CONFIG } from '../config/api';

// User Avatar Component
const UserAvatar = () => (
  <div style={{ 
    backgroundColor: '#6B9ACC',
    color: 'white',
    borderRadius: '50%',
    height: '32px',
    width: '32px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontWeight: 'bold',
    fontSize: '14px'
  }}>
    Y
  </div>
);

// Robot Avatar Component
const RobotAvatar = () => (
  <img
    src="https://cdn-icons-png.flaticon.com/512/4712/4712109.png"
    alt="AI Robot"
    style={{
      width: '32px',
      height: '32px',
      objectFit: 'contain',
    }}
  />
);

// Copy Icon Component
const CopyIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect x="6" y="6" width="13" height="13" rx="2" stroke="#666" strokeWidth="2" />
    <path d="M5 15H4C2.89543 15 2 14.1046 2 13V4C2 2.89543 2.89543 2 4 2H13C14.1046 2 15 2.89543 15 4V5" stroke="#666" strokeWidth="2" />
  </svg>
);

// Thumbs Up Icon Component
const ThumbsUpIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M7 10V20M7 10L4 9.99998V20L7 20M7 10L12.6972 10C13.1668 10 13.5902 9.68112 13.7236 9.21983L15.5 3L16.4549 3C16.7076 3 16.9304 3.17979 17 3.42701L17.8944 7.60289C17.9605 7.84252 17.9137 8.10211 17.7678 8.30065L17 9.33333C16.619 9.85714 16.619 10.4762 17 11L18.5 13C18.8333 13.5 19 13.75 19 14.5L18.5 18.5C18.3162 19.6205 17.2649 20.5 16 20.5H12L7 20" stroke="#3366BB" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

// Thumbs Down Icon Component
const ThumbsDownIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M7 14V4M7 14L4 14V4.00002L7 4M7 14L12.6972 14C13.1668 14 13.5902 14.3189 13.7236 14.7802L15.5 21L16.4549 21C16.7076 21 16.9304 20.8202 17 20.573L17.8944 16.3971C17.9605 16.1575 17.9137 15.8979 17.7678 15.6993L17 14.6667C16.619 14.1429 16.619 13.5238 17 13L18.5 11C18.8333 10.5 19 10.25 19 9.5L18.5 5.5C18.3162 4.37945 17.2649 3.5 16 3.5H12L7 4" stroke="#3366BB" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

// Individual Chat Message Component
const ChatMessage = ({ text, isUser, userName, botName, isTyping = false }) => {
  // Function to parse text and make links clickable
  const renderTextWithLinks = (text) => {
    if (!text) return '';
    
    // Multiple patterns to catch various link formats
    const patterns = [
      // Standard markdown links: [text](url)
      /\[([^\]]+)\]\(([^)]+)\)/g,
      // Parenthetical source links: (Source: filename, Page X)
      /\(Source:\s*([^,)]+),\s*(Page\s*[^)]+)\)/g,
      // Simple URL pattern as fallback
      /(https?:\/\/[^\s)]+)/g
    ];
    
    const parts = [];
    let lastIndex = 0;
    let allMatches = [];
    
    // Find all matches from all patterns
    patterns.forEach((pattern, patternIndex) => {
      let match;
      const regex = new RegExp(pattern.source, pattern.flags);
      while ((match = regex.exec(text)) !== null) {
        allMatches.push({
          index: match.index,
          length: match[0].length,
          fullMatch: match[0],
          text: patternIndex === 0 ? match[1] : (patternIndex === 1 ? `Source: ${match[1]}, ${match[2]}` : match[1]),
          url: patternIndex === 0 ? match[2] : (patternIndex === 1 ? `${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.DOCUMENTS}/${encodeURIComponent(match[1])}` : match[1]),
          type: 'link'
        });
      }
    });
    
    // Sort matches by position
    allMatches.sort((a, b) => a.index - b.index);
    
    // Remove overlapping matches (keep the first one)
    const filteredMatches = [];
    let lastEnd = 0;
    allMatches.forEach(match => {
      if (match.index >= lastEnd) {
        filteredMatches.push(match);
        lastEnd = match.index + match.length;
      }
    });
    
    // Build parts array
    lastIndex = 0;
    filteredMatches.forEach(match => {
      // Add text before the link
      if (match.index > lastIndex) {
        parts.push({
          type: 'text',
          content: text.substring(lastIndex, match.index)
        });
      }
      
      // Add the link
      parts.push({
        type: 'link',
        text: match.text,
        url: match.url
      });
      
      lastIndex = match.index + match.length;
    });
    
    // Add remaining text after the last link
    if (lastIndex < text.length) {
      parts.push({
        type: 'text',
        content: text.substring(lastIndex)
      });
    }
    
    // If no links found, return text as is
    if (parts.length === 0) {
      return text;
    }
    
    // Render the parts
    return parts.map((part, index) => {
      if (part.type === 'link') {
        return (
          <a 
            key={index}
            href={part.url}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              color: '#1e88e5',
              textDecoration: 'underline',
              fontWeight: '600',
              cursor: 'pointer'
            }}
            onClick={(e) => {
              // Ensure the link works
              if (!part.url.startsWith('http')) {
                e.preventDefault();
                window.open(`http://${part.url}`, '_blank');
              }
            }}
          >
            {part.text}
          </a>
        );
      } else {
        return <span key={index}>{part.content}</span>;
      }
    });
  };

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        marginBottom: '24px',
        width: '100%',
        alignItems: isUser ? 'flex-start' : 'flex-end',
        fontFamily: 'Heebo, sans-serif',
      }}
    >
      {/* Message content */}
      <div
        style={{
          width: '85%',
        }}
      >
        <div
          style={{
            padding: '16px',
            borderRadius: '4px',
            backgroundColor: isUser ? '#F2F8FC' : '#fff',
            border: isUser ? '2px solid #D3D7DB' : '2px solid #E0E0E0',
            boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
          }}
        >
          {/* User or Bot header with avatar inside the box */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              marginBottom: '12px',
            }}
          >
            {isUser ? (
              <UserAvatar />
            ) : (
              <div style={{ width: '32px', height: '32px' }}>
                <RobotAvatar />
              </div>
            )}
            <span
              style={{
                marginLeft: '8px',
                fontWeight: '600',
                fontSize: '18px',
                fontFamily: 'Heebo, sans-serif',
              }}
            >
              {isUser ? userName || 'You' : botName || 'Rovr AI'}
            </span>
          </div>
          
          {/* Message Content - Either text or typing indicator */}
          {!isTyping ? (
            <div
              style={{
                whiteSpace: 'pre-wrap',
                lineHeight: 1.6,
                color: '#000',
                fontWeight: '500',
                fontSize: '16px',
                fontFamily: 'Heebo, sans-serif',
              }}
            >
              {renderTextWithLinks(text)}
            </div>
          ) : (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'flex-start',
                padding: '8px 0',
              }}
            >
              {[0, 1, 2].map((dot) => (
                <div
                  key={dot}
                  style={{
                    width: '10px',
                    height: '10px',
                    borderRadius: '50%',
                    backgroundColor: '#1e88e5',
                    margin: '0 6px',
                    opacity: 0.8,
                    animation: `pulse 1s infinite ${dot * 0.2}s`
                  }}
                />
              ))}
              <style>
                {`
                  @keyframes pulse {
                    0%, 100% { opacity: 0.3; transform: scale(0.8); }
                    50% { opacity: 1; transform: scale(1.2); }
                  }
                `}
              </style>
            </div>
          )}

          {/* Sources section for bot messages */}
          {!isUser && !isTyping && (
            <>
              {/* Action buttons inside the chat box */}
              <div
                style={{
                  display: 'flex',
                  gap: '16px',
                  borderTop: '2px solid #E0E0E0',
                  paddingTop: '12px',
                  marginTop: '8px',
                  fontSize: '16px',
                  fontWeight: '500',
                }}
              >
                <div
                  style={{
                    border: '2px solid #D3D7DB',
                    borderRadius: '4px',
                    padding: '4px',
                    display: 'flex',
                    alignItems: 'center',
                    cursor: 'pointer',
                  }}
                >
                  <CopyIcon />
                </div>
                <div
                  style={{
                    color: '#3366BB',
                    cursor: 'pointer',
                  }}
                >
                  <ThumbsUpIcon />
                </div>
                <div
                  style={{
                    color: '#3366BB',
                    cursor: 'pointer',
                  }}
                >
                  <ThumbsDownIcon />
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChatMessage;