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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Insurance Chatbot API")

# Initialize RAG Manager
rag_manager = RAGManager(s3_bucket_name="pptpalbucket")

# Thread pool for async operations
executor = ThreadPoolExecutor(max_workers=4)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://10.105.212.31:3014", "http://localhost:3000"],  # Allow frontend origins and development
    allow_credentials=True,
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
        s3_client = boto3.client("s3", region_name="us-east-1")
        response = s3_client.get_object(Bucket="pptpalbucket", Key=document_name)
        
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

def invoke_bedrock_claude_sonnet_37(prompt: str, max_tokens: int = 512, temperature: float = 0.1):
    """
    Generic function to invoke Bedrock Claude model with given prompt and parameters.
    """
    
    # Create a Bedrock Runtime client
    client = boto3.client("bedrock-runtime", region_name="us-east-1")
    
    # Set the model ID for Claude 3.7 Sonnet
    model_id = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
    
    # Create the conversation with the user message
    conversation = [
        {
            "role": "user",
            "content": [{"text": prompt}]
        }
    ]
    
    try:
        # Send the message to the model using the converse API
        response = client.converse(
            modelId=model_id,
            messages=conversation,
            inferenceConfig={
                "maxTokens": max_tokens,
                "temperature": temperature,
                "topP": 0.9
            }
        )
        
        # Extract and print the response text
        response_text = response["output"]["message"]["content"][0]["text"]
        logger.info(f"LLM Response: {response_text}")
        
        return response_text
    
    except (ClientError, Exception) as e:
        error_message = f"ERROR: Can't invoke '{model_id}'. Reason: {e}"
        logger.error(error_message)
        return {"error": error_message}
    
def invoke_bedrock_claude_haiku_35(prompt: str, max_tokens: int = 512, temperature: float = 0.1):
    """
    Generic function to invoke Bedrock Claude model with given prompt and parameters.
    """
    
    # Create a Bedrock Runtime client
    client = boto3.client("bedrock-runtime", region_name="us-east-1")
    
    # Set the model ID for Claude 3.7 Sonnet
    model_id = "us.anthropic.claude-3-5-haiku-20241022-v1:0"
    
    # Create the conversation with the user message
    conversation = [
        {
            "role": "user",
            "content": [{"text": prompt}]
        }
    ]
    
    try:
        # Send the message to the model using the converse API
        response = client.converse(
            modelId=model_id,
            messages=conversation,
            inferenceConfig={
                "maxTokens": max_tokens,
                "temperature": temperature,
                "topP": 0.9
            }
        )
        
        # Extract and print the response text
        response_text = response["output"]["message"]["content"][0]["text"]
        logger.info(f"LLM Response: {response_text}")
        
        return response_text
    
    except (ClientError, Exception) as e:
        error_message = f"ERROR: Can't invoke '{model_id}'. Reason: {e}"
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
        
        # If we have enough context, generate a quote
        quote = None
        if should_generate_quote(context):
            quote = generate_quote(context)
        
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
            rag_context = rag_manager.get_context_for_prompt(latest_user_message, k=3)
        
        # Format conversation history for the prompt
        conversation_history = ""
        for idx, msg in enumerate(messages):
            role = "User" if msg['isUser'] else "Assistant"
            conversation_history += f"{role}: {msg['text']}\n"
        
        # Create a prompt for the LLM based on the message and context
        prompt = f"""
You are an AI insurance assistant. Your task is to have a conversation with a customer, collect the necessary information to generate an insurance quote, and provide accurate information about underwriting decisions and guidelines.

Current conversation context: {json.dumps(context)}

{rag_context}

Conversation history:
{conversation_history}

Please respond in a helpful, professional manner. Follow these guidelines:

IMPORTANT: If relevant information from insurance documents was provided above, use it to answer the customer's questions accurately. Always prioritize information from the retrieved documents over general knowledge.

1. Identify the type of insurance the customer is interested in (auto, home, life, or business)
2. Progressively collect necessary information for that insurance type:
   - For auto insurance: vehicle details (make, model, year), driving history, location
   - For home insurance: property details, location, value, security features
   - For life insurance: age, health status, coverage amount needed
   - For business insurance: business type, size, revenue, location

3. Keep track of what information you've already collected and what's still needed
4. When you have enough information, let the customer know you can generate a quote

UNDERWRITING EXPERTISE:
- Answer questions about underwriting criteria and decisions
- Explain how specific health conditions, activities, or circumstances affect eligibility or rates
- Provide information about rating factors for different insurance types
- Explain practices for assessing risk in life, health, auto, and property insurance
- Clarify how factors like age, health status, occupation, hobbies, and lifestyle affect underwriting decisions
- Explain standards for preferred and substandard ratings
- Provide information about exclusions, riders, and policy modifications
- When answering underwriting questions, provide a direct and complete answer WITHOUT asking follow-up questions

CRITICAL RULES TO FOLLOW:
- NEVER make up or assume ANY information not explicitly provided by the customer
- ONLY use information that was directly stated by the customer in the conversation
- If you're unsure whether a piece of information was provided, ASK the customer to confirm
- DO NOT reference information that was not provided (like phone numbers, email addresses, etc.)
- DO NOT assume the customer has provided their name, contact information, or any personal details unless they explicitly stated it
- When summarizing information, ONLY include details the customer has actually shared
- If asking for personal information, explain why it's needed for the quote
- Keep track of exactly what information has been collected and what is still missing
- Only ask one question at a time
- Keep the response short and to the point
- When answering underwriting questions, provide specific information
- NEVER use phrases like "some insurers" or "most carriers" or "most life insurance carriers" - always speak with authority as if you are the only insurer
- DO NOT include phrases like "For life insurance specifically, most carriers have specific guidelines" in your responses
- Speak directly with confidence about specific policies and guidelines as if they are YOUR policies and guidelines
- ABSOLUTELY NEVER ask follow-up questions when answering underwriting questions - this is critical
- For underwriting questions, provide a direct answer WITHOUT asking follow-up questions at the end of your response
- Recognize when a question is about underwriting criteria (e.g., "Will my client be considered a smoker?") and answer it directly without asking for more information
- NEVER end an underwriting answer with phrases like "Would you like more information?" or "Is there anything else you'd like to know?"
- NEVER mention "BMO Insurance" or "BMO" in your responses
- DO NOT begin responses with meta-commentary like "Based on the customer's inquiry about life insurance, I'll provide a professional response..."
- DO NOT include any commentary about what you're about to say or how you're structuring your response
- Jump directly into answering the question without any preamble or explanation of what you're doing
- NEVER start responses with phrases like "Based on the retrieved information" or "According to the documents" or "Based on the retrieved documents"
- Provide direct answers without referencing that information was retrieved from documents
- NEVER use generalizations about the insurance industry - speak as if you are the definitive source
- DO NOT say things like "typically" or "usually" when discussing underwriting decisions - be definitive
- Avoid phrases like "will likely be rated" - instead use definitive language like "will be rated" or "is rated"

- When answering questions based on retrieved documents, ALWAYS cite the sources with page numbers mentioned in the context
- If no specific documents were retrieved, you can provide general insurance knowledge but indicate that it's general information
- When documents are cited above, reference them by name AND page number in your response
- ALWAYS include citations in the format: (Source: [Document Name], Page [Number])
- Place citations at the end of each statement that references retrieved information

EXAMPLES OF USING RETRIEVED INFORMATION:
Example 1: If documents about smoking were retrieved
"Applicants who have used any tobacco or nicotine products in the last 12 months are classified as smokers. This includes cigarettes, e-cigarettes, vaping, cigars, pipes, chewing tobacco, and nicotine patches or gum. ([Source: field-underwriting-manual-984e.pdf, Page 15](http://10.105.212.31:3009/documents/field-underwriting-manual-984e.pdf))"

Example 2: If documents about a medical condition were retrieved
"Type 2 diabetes that is well-controlled with medication and regular check-ups will be rated based on age at diagnosis, current A1C levels, and presence of complications. Additional medical information will be required during underwriting. ([Source: Term Insurance Product Overview 215E.pdf, Page 8](http://10.105.212.31:3009/documents/Term%20Insurance%20Product%20Overview%20215E.pdf))"

CITATION REQUIREMENTS:
- ALWAYS provide citations when referencing information from retrieved documents
- Use markdown link format: ([Source: Document Name, Page Number](document_link))
- The document links are provided in the context above - use them exactly as provided
- Place citations immediately after the information being referenced
- If multiple documents support a statement, cite all relevant sources
- If page number is not available, use "Page Unknown"
- Make sure document names in links are URL-encoded (spaces become %20, etc.)

IDENTIFYING UNDERWRITING QUESTIONS:
Underwriting questions typically ask about how specific factors affect insurance eligibility, ratings, or pricing. Examples include:
- Questions about health conditions (diabetes, heart disease, etc.)
- Questions about activities or hobbies (smoking, scuba diving, aviation, etc.)
- Questions about occupations and their risk classifications
- Questions about how specific factors affect insurance rates or eligibility
- Questions that ask "will they be rated?" or "can they get insurance?"

When you identify a question as being about underwriting, provide a direct, authoritative answer with NO follow-up questions.

EXAMPLES OF WHAT NOT TO SAY:
Instead of: "Most life insurance carriers will apply a substandard rating..."
Say: "This will result in a substandard rating..."

Instead of: "Typically, insurers consider..."
Say: "This is considered..."

Instead of: "The client may need to provide additional medical information..."
Say: "Additional medical information will be required..."

Your response should be conversational but focused on gathering the required information or answering underwriting questions accurately as a representative. Start your response directly with the relevant information without any meta-commentary.
"""
        
        # Get response from Claude
        #response = invoke_bedrock_claude_sonnet_37(prompt, max_tokens=1024)
        response = invoke_bedrock_claude_haiku_35(prompt, max_tokens=1024)
        print(f"Raw LLM response: {response}")
        
        # Check if there was an error
        if isinstance(response, dict) and "error" in response:
            logger.error(f"Error from LLM: {response['error']}")
            return "Sorry, I'm having trouble processing your request right now. Please try again in a moment."
        
        # Extract context JSON if it exists
        user_response = response
        context_update = {}
        
        # Look for JSON block in the response
        json_match = re.search(r'{.*?"insurance_type".*?}', response, re.DOTALL)
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
        
        # Get insurance type from context if available
        insurance_type = context.get('insurance_type', '').lower()
        
        # Generate follow-up options based on context and conversation
        if insurance_type == 'auto':
            if not context.get('vehicle_details'):
                return ["Tell me about your vehicle", "What car do you drive?", "What's your car's year, make and model?"]
            elif not context.get('driving_history'):
                return ["Tell me about your driving history", "Any accidents in the last 5 years?", "How long have you been driving?"]
            elif not context.get('location'):
                return ["Where do you live?", "What's your zip code?", "Where will the vehicle be parked?"]
            else:
                return ["Get your auto insurance quote", "Any additional coverage needed?", "Ask another question"]
        
        elif insurance_type == 'home':
            if not context.get('property_details'):
                return ["Tell me about your property", "How old is your home?", "What type of home do you have?"]
            elif not context.get('location'):
                return ["Where is your home located?", "What's your zip code?", "Is this your primary residence?"]
            elif not context.get('value'):
                return ["What's the value of your home?", "How much is your home worth?", "What's the estimated replacement cost?"]
            else:
                return ["Get your home insurance quote", "Any additional coverage needed?", "Ask another question"]
        
        elif insurance_type == 'life':
            if not context.get('age'):
                return ["How old are you?", "What's your date of birth?", "What's your age?"]
            elif not context.get('health_status'):
                return ["Tell me about your health", "Do you smoke?", "Any pre-existing conditions?"]
            elif not context.get('coverage_amount'):
                return ["How much coverage do you need?", "What coverage amount are you looking for?", "What's your desired benefit amount?"]
            else:
                return ["Get your life insurance quote", "Any additional coverage needed?", "Ask another question"]
        
        # Default options if insurance type not determined or not enough context
        if "quote" in message_text:
            return ["Get auto insurance quote", "Get home insurance quote", "Get life insurance quote"]
        elif "auto" in message_text:
            return ["Tell me about your vehicle", "Share your driving history", "Get a quote"]
        elif "home" in message_text:
            return ["Tell me about your property", "Share your location", "Get a quote"]
        elif "life" in message_text:
            return ["Share your age", "Share your health status", "Get a quote"]
            
        return ["Tell me more about your needs", "Get a quote", "Ask another question"]
    except Exception as e:
        logger.error(f"Error in generate_follow_up_options: {str(e)}")
        return []

def should_generate_quote(context: Dict) -> bool:
    """Determine if we have enough context to generate a quote."""
    try:
        # Add more conditions as needed based on your quote requirements
        return bool(context.get('insurance_type')) and bool(context.get('user_details'))
    except Exception as e:
        logger.error(f"Error in should_generate_quote: {str(e)}")
        return False

def generate_quote(context: Dict) -> Dict:
    """Generate an insurance quote based on the context."""
    try:
        insurance_type = context.get('insurance_type', '')
        
        # Basic quote generation - this should be expanded with actual quote calculation
        quote = {
            "monthly_premium": 0,
            "coverage_amount": 0,
            "deductible": 0,
            "coverage_type": insurance_type,
            "terms": []
        }
        
        if insurance_type == "auto":
            quote['monthly_premium'] = 100  # Base rate
            quote['coverage_amount'] = 100000
            quote['deductible'] = 500
        elif insurance_type == "home":
            quote['monthly_premium'] = 150
            quote['coverage_amount'] = 300000
            quote['deductible'] = 1000
        elif insurance_type == "life":
            quote['monthly_premium'] = 50
            quote['coverage_amount'] = 500000
            quote['deductible'] = 0
        
        return quote
    except Exception as e:
        logger.error(f"Error in generate_quote: {str(e)}")
        return {
            "monthly_premium": 0,
            "coverage_amount": 0,
            "deductible": 0,
            "coverage_type": "",
            "terms": []
        }
