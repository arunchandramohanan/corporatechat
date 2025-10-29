# Multi-Agent AI Ecosystem Implementation Guide

## Overview

This application now features a **multi-agent AI ecosystem** that delivers fast, personalized, and context-aware support through specialized agents. Each agent is an expert in a specific domain, working together to provide comprehensive assistance.

## Architecture

### Agent Types

The system includes **5 specialized agents**:

1. **PolicyAgent** 🔷
   - **Expertise**: Card policies, benefits, fees, rewards programs
   - **Tools**: RAG document search, LLM synthesis
   - **Use Cases**: "What are the foreign transaction fees?", "Tell me about travel insurance"

2. **AccountAgent** 🟢
   - **Expertise**: Account management, balances, credit limits, settings
   - **Tools**: Mock account service, balance retrieval
   - **Use Cases**: "What's my balance?", "Increase my credit limit", "Add authorized user"

3. **TransactionAgent** 🟠
   - **Expertise**: Transaction history, disputes, statements
   - **Tools**: Mock transaction service, dispute filing
   - **Use Cases**: "Show recent transactions", "File a dispute", "Download statement"

4. **AnalyticsAgent** 🟣
   - **Expertise**: Spending analytics, trends, budgets, reports
   - **Tools**: Mock analytics service, data aggregation
   - **Use Cases**: "Show spending by category", "Am I over budget?", "Generate expense report"

5. **EscalationAgent** 🔴
   - **Expertise**: Complex issues, complaints, human handoffs
   - **Tools**: Ticket creation, priority assessment
   - **Use Cases**: "I need to speak to a manager", "File a complaint", "Report fraud"

### LangGraph Orchestration Flow

```
User Query
    ↓
┌─────────────────┐
│ Intent Classify │ ← Determines query type
└────────┬────────┘
         ↓
┌─────────────────┐
│  Route to Agent │ ← Selects best agent (confidence scoring)
└────────┬────────┘
         ↓
┌─────────────────┐
│ Execute Primary │ ← Agent processes with tools
│     Agent       │
└────────┬────────┘
         ↓
┌─────────────────┐
│  Collaboration? │ ← Check if multiple agents needed
└───┬─────────┬───┘
   Yes       No
    ↓         ↓
┌────────┐   │
│Execute │   │
│Second  │   │
│Agents  │   │
└───┬────┘   │
    ↓        ↓
┌─────────────────┐
│   Synthesize    │ ← Combine responses
│    Response     │
└────────┬────────┘
         ↓
┌─────────────────┐
│  Escalation?    │ ← Check if human needed
└───┬─────────┬───┘
   Yes       No
    ↓         ↓
  Escalate  Return
   Agent    Response
```

## File Structure

### Backend

```
backend/
├── agents/
│   ├── __init__.py
│   ├── state.py              # LangGraph state schemas
│   ├── base_agent.py         # Abstract base class
│   ├── tools.py              # Shared tools (RAG, LLM)
│   ├── orchestrator.py       # LangGraph workflow
│   ├── policy_agent.py       # Policy expert
│   ├── account_agent.py      # Account manager
│   ├── transaction_agent.py  # Transaction specialist
│   ├── analytics_agent.py    # Analytics expert
│   └── escalation_agent.py   # Escalation handler
├── mock_services/
│   ├── __init__.py
│   ├── account_service.py    # Mock account data
│   ├── transaction_service.py # Mock transactions
│   └── analytics_service.py   # Mock analytics
└── main.py                    # FastAPI with orchestrator integration
```

### Frontend

```
src/components/
├── AgentBadge.jsx      # Visual agent identifier
├── AgentHandoff.jsx    # Shows agent transitions
├── AgentSteps.jsx      # Expandable reasoning process
├── ChatMessage.jsx     # Updated with agent display
└── ChatbotApp.jsx      # Updated to pass agent data
```

## API Changes

### Enhanced `/chat` Endpoint Response

**New Fields:**
```json
{
  "text": "Response text",
  "isUser": false,
  "followUpOptions": [...],
  "quote": {...},
  "context": {...},

  // NEW MULTI-AGENT FIELDS
  "activeAgent": "policy",
  "consultedAgents": ["policy", "account"],
  "agentSteps": [
    {
      "agent_name": "PolicyAgent",
      "action": "searching_policy_documents",
      "details": "Searching for travel insurance details",
      "timestamp": "2025-01-15T10:30:00",
      "tool_used": "rag_search",
      "tool_output": {...}
    }
  ],
  "agentHandoffs": [
    {
      "from_agent": "policy",
      "to_agent": "account",
      "reason": "Multi-domain query collaboration",
      "timestamp": "2025-01-15T10:30:05"
    }
  ],
  "confidenceScore": 0.95
}
```

### New `/agents/info` Endpoint

```bash
GET /agents/info
```

**Response:**
```json
{
  "multi_agent_enabled": true,
  "agents": [
    {
      "name": "policy",
      "display_name": "PolicyAgent",
      "description": "Expert in corporate card policies...",
      "tools": ["rag_search", "call_llm"]
    },
    ...
  ],
  "total_agents": 5
}
```

## Environment Variables

Add to `.env`:

```bash
# Multi-Agent Configuration
USE_MULTI_AGENT=true  # Enable/disable multi-agent system

# Existing variables
S3_BUCKET_NAME=teamone-kb
LAMBDA_FUNCTION_NAME=claude-api-function
LAMBDA_REGION=ca-central-1
RAG_TOP_K=3
```

## Installation & Setup

### 1. Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

**New dependencies added:**
- `langgraph>=0.0.55` - Agent orchestration framework
- `langchain-anthropic>=0.1.0` - Claude integration

### 2. Run the Backend

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 3009
```

### 3. Run the Frontend

```bash
npm install
npm run dev
```

## Usage Examples

### Example 1: Policy Query

**User:** "What are the foreign transaction fees?"

**Agent Flow:**
1. Intent classified as `policy_query`
2. Routed to **PolicyAgent** (confidence: 0.95)
3. Agent steps:
   - Searching policy documents (RAG)
   - Found 3 relevant sections
   - Generating response with citations
4. Response with source citations and page numbers

**UI Shows:**
- 🔷 Policy Expert badge
- "How I Helped" section with 3 steps
- Citations to policy documents

### Example 2: Multi-Agent Collaboration

**User:** "What's my balance and show me spending by category?"

**Agent Flow:**
1. Intent classified as `multi_domain`
2. Primary: **AccountAgent**
3. Secondary: **AnalyticsAgent**
4. Collaboration:
   - AccountAgent retrieves balance
   - AnalyticsAgent generates category breakdown
   - Responses synthesized
5. Agent handoff shown in UI

**UI Shows:**
- 🟢 Account Manager → 🟣 Analytics Expert handoff
- Combined response from both agents
- "How I Helped" showing both agents' steps

### Example 3: Escalation

**User:** "I want to speak to a manager about this charge"

**Agent Flow:**
1. Intent classified as `escalation`
2. Routed to **EscalationAgent**
3. Ticket created with:
   - Case number
   - Priority level
   - Expected response time
   - Assigned team

**UI Shows:**
- 🔴 Escalation Manager badge
- Ticket details in response
- Next steps clearly outlined

## UI Components

### AgentBadge

Visual identifier for which agent is responding.

**Colors:**
- 🔷 Blue - PolicyAgent
- 🟢 Green - AccountAgent
- 🟠 Orange - TransactionAgent
- 🟣 Purple - AnalyticsAgent
- 🔴 Red - EscalationAgent

**Features:**
- Hover tooltip with agent description
- Icons for each agent type
- Compact and minimal variants

### AgentHandoff

Shows transitions between agents during collaboration.

**Display:**
```
[Policy Expert] → [Account Manager]
Reason: Multi-domain query collaboration
```

**Features:**
- Animated arrow
- Transition reason
- Fade-in animation

### AgentSteps

Expandable accordion showing the agent's reasoning process.

**Sections:**
- Steps grouped by agent
- Tool usage indicated
- Tool outputs shown (if available)
- Timeline visualization
- Success indicator

**Icons:**
- 🔍 Searching
- 🧠 Analyzing
- 📥 Retrieving
- ✨ Generating
- ⚙️ Processing
- ✓ Checking
- 🎯 Creating
- ✅ Complete

## Key Features

### 1. Intelligent Routing
- Keyword-based intent classification
- Confidence scoring for agent selection
- Automatic fallback to PolicyAgent

### 2. Multi-Agent Collaboration
- Multiple agents can work together
- Shared state and context
- Response synthesis

### 3. Transparent Operations
- Every agent action logged
- Reasoning process visible to users
- Tool usage tracked

### 4. Escalation Handling
- Automatic detection of complex issues
- Ticket creation with SLA
- Priority assessment

### 5. Context Awareness
- Conversation context maintained
- Agent-specific context updates
- Handoff context passed between agents

## Monitoring & Metrics

### Agent Metrics (Future Enhancement)

Track:
- Agent invocation frequency
- Average response time per agent
- Confidence scores distribution
- Escalation rate
- User satisfaction by agent
- Multi-agent collaboration frequency

### Logs

Check backend logs for:
```
[PolicyAgent] searching_policy_documents: Searching for...
[Orchestrator] Routed to policy agent (confidence: 0.95)
[AccountAgent] retrieving_balance: Fetching account...
```

## Development Guide

### Adding a New Agent

1. Create agent file in `backend/agents/`:
```python
from .base_agent import BaseAgent
from .state import AgentState

class MyNewAgent(BaseAgent):
    def __init__(self, tools):
        super().__init__(
            name="MyNewAgent",
            description="Expert in..."
        )
        self.tools_instance = tools
        self.tools = ["tool1", "tool2"]

    def can_handle(self, state: AgentState) -> tuple[bool, float]:
        # Logic to determine if this agent should handle the query
        query = state.get("user_query", "").lower()
        if "keyword" in query:
            return True, 0.90
        return False, 0.0

    async def execute(self, state: AgentState) -> Dict[str, Any]:
        # Main agent logic
        self.add_step(state, "doing_something", "Description of action")
        # ... perform work ...
        return self.format_response(
            text="Response text",
            follow_up_options=["Option 1", "Option 2"]
        )
```

2. Register in `orchestrator.py`:
```python
from .my_new_agent import MyNewAgent

self.agents = {
    # ...existing agents...
    "mynew": MyNewAgent(self.tools)
}
```

3. Add UI color in `AgentBadge.jsx`:
```javascript
mynew: {
  label: 'My New Expert',
  color: '#00bcd4',
  icon: MyIcon,
  description: 'Specialized in...'
}
```

### Testing Agents

```python
# backend/tests/test_my_agent.py
import pytest
from agents.my_new_agent import MyNewAgent
from agents.tools import AgentTools

@pytest.mark.asyncio
async def test_can_handle():
    agent = MyNewAgent(AgentTools())
    state = {"user_query": "test query with keyword"}
    can_handle, confidence = agent.can_handle(state)
    assert can_handle == True
    assert confidence > 0.5
```

## Troubleshooting

### Multi-Agent Not Working

1. Check environment variable:
   ```bash
   USE_MULTI_AGENT=true
   ```

2. Check orchestrator initialization:
   ```bash
   # Backend logs should show:
   "Multi-agent orchestrator initialized"
   ```

3. Verify dependencies installed:
   ```bash
   pip list | grep langgraph
   ```

### Agent Not Being Selected

- Check `can_handle()` logic
- Verify keywords in query
- Check confidence scores in logs
- Review intent classification

### Frontend Not Showing Agent Info

- Check API response includes new fields
- Verify props passed to ChatMessage
- Check browser console for errors

## Performance Optimization

### Caching

Consider adding:
- RAG result caching
- Agent decision caching
- Tool output caching

### Parallel Execution

Currently sequential. Future enhancement:
- Parallel secondary agent execution
- Concurrent tool calls
- Async processing

## Security Considerations

### Current Implementation
- No authentication (development mode)
- Mock data only
- Open CORS

### Production Requirements
- Add API authentication
- Integrate real account/transaction APIs
- Implement rate limiting
- Add input validation
- Enable CORS restrictions

## Next Steps

1. **Real API Integration**
   - Replace mock services with real banking APIs
   - Add authentication/authorization
   - Implement secure data handling

2. **Advanced Features**
   - Voice input/output
   - Multi-turn planning
   - Proactive suggestions
   - Learning from feedback

3. **Analytics Dashboard**
   - Agent performance metrics
   - User satisfaction tracking
   - Usage analytics
   - A/B testing framework

4. **Testing**
   - Unit tests for each agent
   - Integration tests for workflows
   - End-to-end testing
   - Load testing

## Support

For questions or issues:
- Check logs: `backend/logs/`
- Review agent steps in UI
- Test with `/agents/info` endpoint
- Enable debug logging

---

**Implementation Status:** ✅ Complete

**Files Created:** 23
**Files Modified:** 3
**Agents Implemented:** 5
**UI Components:** 3

**Ready for Testing!** 🚀
