from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import logging
import boto3
from botocore.exceptions import ClientError
import re
from rag_utils import RAGManager
import asyncio
from concurrent.futures import ThreadPoolExecutor
import io
import urllib.parse
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Corporate Card Support API")

# Get configuration from environment variables
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "teamone-kb")
LAMBDA_FUNCTION_NAME = os.getenv("LAMBDA_FUNCTION_NAME", "claude-api-function")
LAMBDA_REGION = os.getenv("LAMBDA_REGION", "ca-central-1")
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "3"))
CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000").split(",")

# Initialize RAG Manager
rag_manager = RAGManager(s3_bucket_name=S3_BUCKET_NAME)

# Thread pool for async operations
executor = ThreadPoolExecutor(max_workers=4)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for public deployment
    allow_credentials=False,  # Must be False when allow_origins is "*"
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Type", "Authorization"],
)

class ChatMessage(BaseModel):
    text: str
    isUser: bool

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    context: Dict = {}

class ChatResponse(BaseModel):
    text: str
    isUser: bool
    followUpOptions: List[str] = []
    quote: Dict[str, Any] | None = None
    context: Dict = {}

class IndexRequest(BaseModel):
    reindex: bool = False

class IndexResponse(BaseModel):
    status: str
    message: str
    stats: Optional[Dict[str, int]] = None

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "corporate-chat-backend"}

@app.on_event("startup")
async def startup_event():
    """Initialize and index documents on startup"""
    try:
        # Run indexing in background thread to not block startup
        async def index_in_background():
            loop = asyncio.get_event_loop()
            stats = await loop.run_in_executor(executor, rag_manager.index_all_documents)
            logger.info(f"Background indexing completed with stats: {stats}")
        
        asyncio.create_task(index_in_background())
        logger.info("Started background document indexing")
    except Exception as e:
        logger.error(f"Error during startup indexing: {e}")

@app.get("/rag/stats")
async def get_rag_stats():
    """Get statistics about the RAG index"""
    try:
        stats = rag_manager.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting RAG stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rag/index", response_model=IndexResponse)
async def index_documents(request: IndexRequest):
    """Manually trigger document indexing"""
    try:
        if request.reindex:
            # Clear existing index first
            rag_manager.clear_index()
            message = "Cleared existing index. "
        else:
            message = ""
        
        # Run indexing in executor to avoid blocking
        loop = asyncio.get_event_loop()
        stats = await loop.run_in_executor(executor, rag_manager.index_all_documents)
        
        return IndexResponse(
            status="success",
            message=message + f"Indexed {stats['success']} documents successfully",
            stats=stats
        )
    except Exception as e:
        logger.error(f"Error indexing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/{document_name}")
async def get_document(document_name: str):
    """Serve documents from S3 bucket"""
    try:
        # URL decode the document name
        document_name = urllib.parse.unquote(document_name)
        
        # Get the document from S3
        s3_client = boto3.client("s3", region_name=os.getenv("AWS_DEFAULT_REGION", "ca-central-1"))
        response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=document_name)
        
        # Create a streaming response
        file_content = response['Body'].read()
        
        # Determine content type based on file extension
        content_type = "application/pdf"
        if document_name.lower().endswith('.pdf'):
            content_type = "application/pdf"
        elif document_name.lower().endswith(('.doc', '.docx')):
            content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        elif document_name.lower().endswith(('.xls', '.xlsx')):
            content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        elif document_name.lower().endswith(('.ppt', '.pptx')):
            content_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        
        return StreamingResponse(
            io.BytesIO(file_content),
            media_type=content_type,
            headers={
                "Content-Disposition": f"inline; filename={document_name}",
                "Content-Type": content_type
            }
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            raise HTTPException(status_code=404, detail="Document not found")
        else:
            logger.error(f"Error retrieving document {document_name}: {e}")
            raise HTTPException(status_code=500, detail="Error retrieving document")
    except Exception as e:
        logger.error(f"Error serving document {document_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def invoke_lambda_claude(prompt: str, max_tokens: int = 1024):
    """
    Invoke AWS Lambda function that calls Claude API.
    The Lambda function uses Claude Sonnet 4.5 model.

    Args:
        prompt: The prompt to send to Claude
        max_tokens: Maximum tokens to generate (default: 1024)

    Returns:
        str: The response text from Claude, or dict with error if failed
    """
    try:
        # Create Lambda client
        lambda_client = boto3.client("lambda", region_name=LAMBDA_REGION)

        # Prepare payload for Lambda function
        payload = {
            "prompt": prompt,
            "max_tokens": max_tokens
        }

        # Invoke Lambda function
        response = lambda_client.invoke(
            FunctionName=LAMBDA_FUNCTION_NAME,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )

        # Parse response
        response_payload = json.loads(response['Payload'].read())

        # Check if Lambda execution was successful
        if response_payload.get('statusCode') != 200:
            error_body = json.loads(response_payload.get('body', '{}'))
            error_message = f"Lambda error: {error_body.get('error', 'Unknown error')}"
            logger.error(error_message)
            return {"error": error_message}

        # Extract the response text from Lambda response
        body = json.loads(response_payload['body'])
        response_text = body.get('response', '')

        # Log usage information
        usage = body.get('usage', {})
        logger.info(f"LLM Response received. Model: {body.get('model', 'unknown')}, "
                   f"Input tokens: {usage.get('input_tokens', 0)}, "
                   f"Output tokens: {usage.get('output_tokens', 0)}")

        return response_text

    except (ClientError, Exception) as e:
        error_message = f"ERROR: Can't invoke Lambda '{LAMBDA_FUNCTION_NAME}'. Reason: {e}"
        logger.error(error_message)
        return {"error": error_message}    

@app.post("/chat", response_model=ChatResponse)
async def get_chat_response(request: Request):
    try:
        # Get the request body
        body = await request.json()
        logger.info(f"Received request: {body}")
        
        # Validate the request
        if not isinstance(body.get('messages'), list):
            raise HTTPException(status_code=400, detail="Invalid request format: messages must be a list")
        
        # Get the latest user message
        messages = body['messages']
        latest_message = next(msg for msg in messages[::-1] if msg['isUser'])
        
        # Get the context from the request or initialize it
        context = body.get('context', {})
        logger.info(f"Received context: {context}")
        
        # Process the message and generate response
        response_text = process_message(messages, context)
        logger.info(f"Final context after processing: {context}")
        
        # Generate follow-up options based on conversation context
        follow_up_options = generate_follow_up_options(messages, context)

        # If we have enough context, generate a card summary
        quote = None
        if should_show_card_summary(context):
            quote = generate_card_summary(context)
        
        # Create response object
        response = ChatResponse(
            text=response_text,
            isUser=False,
            followUpOptions=follow_up_options,
            quote=quote,
            context=context  # Include updated context in the response
        )
        
        logger.info(f"Sending response: {response}")
        return response
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

def process_message(messages: List[Dict], context: Dict) -> str:
    """Process the incoming message and generate a response."""
    try:
        # Get the latest user message for RAG search
        latest_user_message = ""
        for msg in reversed(messages):
            if msg['isUser']:
                latest_user_message = msg['text']
                break
        
        # Search for relevant documents using RAG
        rag_context = ""
        if latest_user_message:
            rag_context = rag_manager.get_context_for_prompt(latest_user_message, k=RAG_TOP_K)
        
        # Format conversation history for the prompt
        conversation_history = ""
        for idx, msg in enumerate(messages):
            role = "User" if msg['isUser'] else "Assistant"
            conversation_history += f"{role}: {msg['text']}\n"
        
        # Create a prompt for the LLM based on the message and context
        prompt = f"""
You are a BMO Corporate Card AI assistant. Your task is to provide fast, personalized, and context-aware support to corporate card holders through a conversational interface. You handle policy queries, account data, transactions, analytics, and escalations to reduce support costs and enhance user satisfaction.

Current conversation context: {json.dumps(context)}

{rag_context}

Conversation history:
{conversation_history}

Please respond in a helpful, professional manner. Follow these guidelines:

IMPORTANT: If relevant information from corporate card policy documents was provided above, use it to answer the cardholder's questions accurately. Always prioritize information from the retrieved documents over general knowledge.

SUPPORT CATEGORIES - Identify what the cardholder needs help with:
1. Policy Queries: Card types, benefits, eligibility, credit limits, rewards programs, fees
2. Transaction Management: View transactions, dispute charges, report fraud, download statements
3. Account Management: Activate cards, add users, update information, set spending limits, security settings
4. Analytics & Reporting: Spending trends, expense reports, compliance reporting, budget tracking
5. Technical Support: Login issues, password resets, mobile app problems, payment processing
6. Escalations: Complex issues requiring human intervention

CONTEXT TRACKING - Keep track of:
- support_category: The type of help needed (policy/transactions/account/analytics/technical/escalation)
- card_number_last4: Last 4 digits of card (if provided)
- transaction_details: Specific transaction information for disputes or inquiries
- issue_description: Clear description of the problem or question
- resolution_status: Whether the issue is resolved or needs escalation

CORPORATE CARD EXPERTISE:
- Explain card program features, benefits, and policies
- Guide users through transaction management and dispute processes
- Provide information about spending limits, rewards, and fees
- Explain security features and fraud protection
- Help with expense tracking and reporting requirements
- Clarify compliance and documentation requirements
- Provide step-by-step instructions for common tasks
- When answering policy questions, provide a direct and complete answer WITHOUT asking unnecessary follow-up questions

CRITICAL RULES TO FOLLOW:
- NEVER make up or assume information not explicitly provided by the cardholder
- ONLY use information directly stated by the cardholder or retrieved from official documents
- DO NOT reference personal information unless the cardholder provided it
- Keep track of exactly what information has been collected and what is still needed
- Only ask one question at a time
- Keep responses clear, concise, and actionable
- Speak with authority about BMO Corporate Card policies and procedures
- DO NOT use phrases like "some banks" or "most credit card companies" - speak as BMO's representative
- DO NOT begin responses with meta-commentary like "Based on the cardholder's inquiry..."
- Jump directly into answering the question without preamble
- NEVER start responses with phrases like "Based on the retrieved information" or "According to the documents"
- Provide direct answers without referencing that information was retrieved
- Use definitive language - avoid "typically," "usually," "might," etc.
- For straightforward policy questions, provide the answer directly without asking follow-up questions

SELF-SERVICE SUPPORT:
- Empower cardholders to resolve issues independently when possible
- Provide clear step-by-step instructions for common tasks
- Offer links to relevant documentation or tools
- Explain what cardholders can do themselves vs. what requires support team assistance
- Reduce escalations by providing comprehensive self-service guidance

ESCALATION HANDLING:
When an issue requires human intervention:
- Clearly explain why escalation is needed
- Summarize all information collected
- Provide expected next steps and timeframes
- Offer ticket/reference number format if applicable
- Ensure cardholders know how to follow up

CITATION REQUIREMENTS:
- When answering questions based on retrieved documents, ALWAYS cite sources with page numbers
- Use markdown link format: ([Source: Document Name, Page Number](document_link))
- Place citations at the end of each statement that references retrieved information
- If multiple documents support a statement, cite all relevant sources
- Make sure document names in links are URL-encoded (spaces become %20, etc.)

EXAMPLES OF USING RETRIEVED INFORMATION:
Example 1: Policy question about foreign transaction fees
"There are no foreign transaction fees on BMO corporate cards for purchases made outside Canada. This applies to both in-store and online international purchases. ([Source: BMO Corporate Card Policy Guide.pdf, Page 12](http://10.105.212.31:3009/documents/BMO%20Corporate%20Card%20Policy%20Guide.pdf))"

Example 2: Dispute process question
"Transaction disputes must be filed within 60 days of the statement date. You'll need to provide the transaction date, merchant name, amount, and reason for dispute. Submit through the online portal or mobile app under 'Dispute Transaction.' ([Source: Corporate Card FAQ.pdf, Page 8](http://10.105.212.31:3009/documents/Corporate_Card_FAQ.pdf))"

EXAMPLES OF GOOD RESPONSES:
Instead of: "Most corporate cards have a dispute process..."
Say: "Your BMO corporate card allows you to dispute transactions within 60 days..."

Instead of: "Typically, cardholders can..."
Say: "You can activate your card by calling the number on the sticker or through the mobile app..."

Instead of: "This might require approval from..."
Say: "Credit limit increases require approval from your account administrator..."

Your response should be conversational, solution-focused, and empowering. Provide specific, actionable information that helps cardholders resolve their issues quickly. Start your response directly with the relevant information without any meta-commentary.
"""
        
        # Get response from Claude via Lambda
        response = invoke_lambda_claude(prompt, max_tokens=1024)
        print(f"Raw LLM response: {response}")
        
        # Check if there was an error
        if isinstance(response, dict) and "error" in response:
            logger.error(f"Error from LLM: {response['error']}")
            return "Sorry, I'm having trouble processing your request right now. Please try again in a moment."
        
        # Extract context JSON if it exists
        user_response = response
        context_update = {}
        
        # Look for JSON block in the response
        json_match = re.search(r'{.*?"support_category".*?}', response, re.DOTALL)
        if json_match:
            try:
                # Extract and parse the JSON
                json_str = json_match.group(0)
                context_update = json.loads(json_str)
                
                # Remove the JSON block from the response
                user_response = response.replace(json_str, '').strip()
                
                # Update the context with the new information
                context.update(context_update)
                logger.info(f"Updated context: {context}")
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing context JSON: {e}")
        
        return user_response
        
    except Exception as e:
        logger.error(f"Error in process_message: {str(e)}")
        return "Sorry, there was an error processing your request. Please try again."

def generate_follow_up_options(messages: List[Dict], context: Dict) -> List[str]:
    """Generate relevant follow-up options based on the conversation."""
    try:
        # Get the latest user message
        latest_message = next(msg for msg in messages[::-1] if msg['isUser'])
        message_text = latest_message['text'].lower()

        # Get support category from context if available
        support_category = context.get('support_category', '').lower()

        # Generate follow-up options based on context and conversation
        if support_category == 'transactions':
            if not context.get('transaction_details'):
                return ["View recent transactions", "Search for specific transaction", "Download transaction history"]
            elif context.get('dispute_needed'):
                return ["File a dispute", "Check dispute status", "Upload supporting documents"]
            else:
                return ["Export to Excel", "Set up transaction alerts", "Ask another question"]

        elif support_category == 'account':
            if 'activate' in message_text:
                return ["Activate by phone", "Activate through mobile app", "Activate online"]
            elif 'limit' in message_text:
                return ["Check current limit", "Request limit increase", "Set spending alerts"]
            elif 'lost' in message_text or 'stolen' in message_text:
                return ["Block card immediately", "Order replacement card", "Review recent transactions"]
            else:
                return ["Update account info", "Add authorized users", "Manage card settings"]

        elif support_category == 'rewards':
            if not context.get('rewards_balance_checked'):
                return ["Check rewards balance", "View redemption options", "See earning rates"]
            else:
                return ["Redeem for travel", "Redeem for cash back", "Transfer to partners"]

        elif support_category == 'analytics':
            return ["View spending by category", "Generate expense report", "Download year-to-date summary", "Track budget vs. actual"]

        elif support_category == 'technical':
            if 'login' in message_text:
                return ["Reset password", "Unlock account", "Set up two-factor authentication"]
            elif 'app' in message_text:
                return ["Update mobile app", "Clear app cache", "Reinstall app"]
            else:
                return ["Contact technical support", "View system status", "Access user guide"]

        # Keyword-based suggestions when category not yet determined
        if any(word in message_text for word in ['transaction', 'charge', 'purchase', 'payment']):
            return ["View my transactions", "Dispute a charge", "Download statement"]
        elif any(word in message_text for word in ['activate', 'new card', 'replacement']):
            return ["Activate my card", "Check card status", "Order replacement"]
        elif any(word in message_text for word in ['limit', 'credit', 'increase']):
            return ["Check my credit limit", "Request limit increase", "View available credit"]
        elif any(word in message_text for word in ['rewards', 'points', 'redeem']):
            return ["Check rewards balance", "Redeem rewards", "Learn about rewards program"]
        elif any(word in message_text for word in ['report', 'expense', 'statement']):
            return ["Generate expense report", "Download statement", "View spending summary"]
        elif any(word in message_text for word in ['dispute', 'fraud', 'unauthorized']):
            return ["Report fraudulent transaction", "File a dispute", "Block my card"]
        elif any(word in message_text for word in ['fee', 'charge', 'interest']):
            return ["View fee schedule", "Understand my charges", "Ask about interest rates"]
        elif any(word in message_text for word in ['travel', 'international', 'foreign']):
            return ["Set travel notification", "Check foreign transaction fees", "View travel benefits"]

        return ["View account summary", "Check recent transactions", "Ask another question"]
    except Exception as e:
        logger.error(f"Error in generate_follow_up_options: {str(e)}")
        return []

def should_show_card_summary(context: Dict) -> bool:
    """Determine if we have enough context to show a card account summary."""
    try:
        # Show summary if user has requested account info or we have card details
        return bool(context.get('show_summary')) or bool(context.get('card_number_last4'))
    except Exception as e:
        logger.error(f"Error in should_show_card_summary: {str(e)}")
        return False

def generate_card_summary(context: Dict) -> Dict:
    """Generate a corporate card account summary based on the context."""
    try:
        support_category = context.get('support_category', '')

        # Basic card summary - this should be expanded with actual API calls to get real data
        summary = {
            "current_balance": 0,
            "available_credit": 0,
            "credit_limit": 0,
            "rewards_points": 0,
            "statement_date": "",
            "payment_due_date": "",
            "card_type": ""
        }

        # Placeholder data based on support category
        if support_category == "account":
            summary['current_balance'] = 2500.00
            summary['available_credit'] = 7500.00
            summary['credit_limit'] = 10000.00
            summary['card_type'] = "BMO Corporate Card"
        elif support_category == "rewards":
            summary['rewards_points'] = 15000
            summary['card_type'] = "BMO Corporate Rewards Card"
            summary['current_balance'] = 3200.00
            summary['available_credit'] = 16800.00
            summary['credit_limit'] = 20000.00
        elif support_category == "transactions":
            summary['current_balance'] = 1800.00
            summary['available_credit'] = 13200.00
            summary['credit_limit'] = 15000.00
            summary['statement_date'] = "2024-01-31"
            summary['payment_due_date'] = "2024-02-15"
        else:
            # Default summary
            summary['current_balance'] = 2000.00
            summary['available_credit'] = 8000.00
            summary['credit_limit'] = 10000.00
            summary['card_type'] = "BMO Corporate Card"

        return summary
    except Exception as e:
        logger.error(f"Error in generate_card_summary: {str(e)}")
        return {
            "current_balance": 0,
            "available_credit": 0,
            "credit_limit": 0,
            "rewards_points": 0,
            "statement_date": "",
            "payment_due_date": "",
            "card_type": ""
        }
