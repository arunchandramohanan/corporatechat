# RAG Implementation for Insurance Chatbot

This document describes the Retrieval-Augmented Generation (RAG) implementation for the insurance chatbot.

## Overview

The chatbot now uses RAG to search and retrieve relevant information from documents stored in the `pptbalbucket` S3 bucket. This allows the chatbot to provide more accurate and contextual responses based on actual insurance documentation.

## Key Components

### 1. RAG Manager (`rag_utils.py`)

The `RAGManager` class handles:
- **Document Indexing**: Downloads documents from S3 and indexes them into ChromaDB
- **Text Processing**: Splits documents into chunks for better retrieval
- **Semantic Search**: Uses sentence transformers to find relevant document chunks
- **Context Generation**: Formats retrieved information for the LLM

Supported document formats:
- PDF (.pdf)
- Word documents (.docx, .doc)
- Text files (.txt, .md)
- PowerPoint (.pptx, .ppt)
- Excel (.xlsx, .xls)
- CSV (.csv)

### 2. API Integration (`main.py`)

New endpoints:
- `GET /rag/stats`: Get statistics about indexed documents
- `POST /rag/index`: Manually trigger document indexing

The chat endpoint now:
1. Searches for relevant documents based on user queries
2. Includes retrieved context in the LLM prompt
3. Provides more accurate responses based on actual documentation

### 3. Automatic Indexing

Documents are automatically indexed on server startup in the background. This ensures the RAG system is ready to use without blocking the API startup.

## Setup and Usage

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Start the Backend

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The server will automatically start indexing documents from the `pptbalbucket` S3 bucket on startup.

### 3. Test the RAG System

Run the test scripts:

```bash
# Test RAG functionality directly
python test_rag.py

# Test API endpoints
python test_api.py
```

### 4. Monitor RAG Status

Check the indexing status:
```bash
curl http://localhost:8000/rag/stats
```

## How It Works

1. **Document Indexing**:
   - On startup, the system scans the S3 bucket for supported documents
   - Each document is downloaded, processed, and split into chunks
   - Chunks are embedded using sentence transformers
   - Embeddings are stored in ChromaDB for fast retrieval

2. **Query Processing**:
   - When a user asks a question, the system searches for relevant document chunks
   - The top 3 most relevant chunks are retrieved
   - These chunks are included as context in the LLM prompt

3. **Response Generation**:
   - The LLM uses both the conversation history and retrieved context
   - Responses prioritize information from retrieved documents
   - Sources are cited when appropriate

## Configuration

Key configuration options in `rag_utils.py`:

```python
# S3 bucket name
s3_bucket_name = "pptbalbucket"

# ChromaDB collection name
collection_name = "insurance_docs"

# Number of relevant chunks to retrieve
k = 3

# Chunk size for text splitting
chunk_size = 1000
chunk_overlap = 200
```

## Troubleshooting

### Documents not being indexed
- Check S3 bucket permissions
- Verify document formats are supported
- Check logs for specific error messages

### Poor search results
- Ensure documents contain relevant information
- Try adjusting the number of chunks retrieved (k parameter)
- Check if documents are properly formatted

### Performance issues
- ChromaDB data is persisted in `./chroma_db` directory
- Clear the index and reindex if needed: `POST /rag/index {"reindex": true}`

## Future Improvements

1. **Document Management UI**: Add frontend interface for document upload/management
2. **Real-time Updates**: Implement S3 event notifications for automatic reindexing
3. **Advanced Search**: Add filters for document type, date, etc.
4. **Performance Optimization**: Implement caching for frequently accessed documents
5. **Multi-language Support**: Add support for documents in multiple languages