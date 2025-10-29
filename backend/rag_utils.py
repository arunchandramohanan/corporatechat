import os
import logging
import tempfile
from typing import List, Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError
import chromadb
from chromadb.config import Settings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    UnstructuredPowerPointLoader,
    UnstructuredExcelLoader,
    CSVLoader
)
import hashlib
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGManager:
    def __init__(self, s3_bucket_name: str = "teamone-kb", collection_name: str = "corporate_card_docs", base_url: str = "http://10.105.212.69:3009"):
        """
        Initialize the RAG Manager with S3 bucket and ChromaDB configuration
        """
        self.s3_bucket_name = s3_bucket_name
        self.collection_name = collection_name
        self.base_url = base_url
        
        # Initialize S3 client
        self.s3_client = boto3.client("s3", region_name="ca-central-1")
        
        # Initialize embeddings model
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        
        # Initialize ChromaDB client with persistent storage
        self.chroma_client = chromadb.PersistentClient(
            path="./chroma_db",
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Get or create collection
        try:
            self.collection = self.chroma_client.get_collection(name=self.collection_name)
            logger.info(f"Using existing collection: {self.collection_name}")
        except:
            self.collection = self.chroma_client.create_collection(
                name=self.collection_name,
                metadata={"description": "Corporate card documents from S3"}
            )
            logger.info(f"Created new collection: {self.collection_name}")
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Track indexed documents
        self.indexed_docs_file = "./indexed_documents.json"
        self.indexed_docs = self._load_indexed_docs()
    
    def _load_indexed_docs(self) -> Dict[str, Any]:
        """Load the list of already indexed documents"""
        if os.path.exists(self.indexed_docs_file):
            try:
                with open(self.indexed_docs_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_indexed_docs(self):
        """Save the list of indexed documents"""
        with open(self.indexed_docs_file, 'w') as f:
            json.dump(self.indexed_docs, f, indent=2)
    
    def _get_file_hash(self, content: bytes) -> str:
        """Generate a hash for file content"""
        return hashlib.md5(content).hexdigest()
    
    def _get_loader_for_file(self, file_path: str):
        """Get the appropriate document loader based on file extension"""
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.pdf':
            return PyPDFLoader(file_path)
        elif ext in ['.docx', '.doc']:
            return Docx2txtLoader(file_path)
        elif ext in ['.txt', '.md']:
            return TextLoader(file_path)
        elif ext in ['.pptx', '.ppt']:
            return UnstructuredPowerPointLoader(file_path)
        elif ext in ['.xlsx', '.xls']:
            return UnstructuredExcelLoader(file_path)
        elif ext == '.csv':
            return CSVLoader(file_path)
        else:
            # Try text loader as fallback
            return TextLoader(file_path)
    
    def download_and_index_file(self, s3_key: str) -> bool:
        """Download a file from S3 and index it in ChromaDB"""
        try:
            # Check if file is already indexed
            response = self.s3_client.head_object(Bucket=self.s3_bucket_name, Key=s3_key)
            file_size = response['ContentLength']
            last_modified = response['LastModified'].isoformat()
            
            # Check if we've already indexed this exact version
            if s3_key in self.indexed_docs:
                if (self.indexed_docs[s3_key].get('size') == file_size and 
                    self.indexed_docs[s3_key].get('last_modified') == last_modified):
                    logger.info(f"File {s3_key} already indexed and unchanged")
                    return True
            
            # Download file from S3
            logger.info(f"Downloading {s3_key} from S3...")
            response = self.s3_client.get_object(Bucket=self.s3_bucket_name, Key=s3_key)
            file_content = response['Body'].read()
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(s3_key)[1]) as tmp_file:
                tmp_file.write(file_content)
                tmp_file_path = tmp_file.name
            
            try:
                # Load and process the document
                loader = self._get_loader_for_file(tmp_file_path)
                documents = loader.load()
                
                # Split documents into chunks
                texts = self.text_splitter.split_documents(documents)
                
                # Prepare documents for ChromaDB
                doc_texts = [doc.page_content for doc in texts]
                doc_metadatas = [
                    {
                        **doc.metadata,
                        "source": s3_key,
                        "chunk_index": i,
                        "total_chunks": len(texts),
                        "indexed_at": datetime.now().isoformat()
                    } 
                    for i, doc in enumerate(texts)
                ]
                
                # Generate embeddings and add to collection
                embeddings = self.embeddings.embed_documents(doc_texts)
                
                # Generate unique IDs for each chunk
                ids = [f"{s3_key}_chunk_{i}" for i in range(len(texts))]
                
                # First, delete any existing chunks for this document
                try:
                    existing_ids = self.collection.get(
                        where={"source": s3_key}
                    )['ids']
                    if existing_ids:
                        self.collection.delete(ids=existing_ids)
                        logger.info(f"Deleted {len(existing_ids)} existing chunks for {s3_key}")
                except:
                    pass
                
                # Add to ChromaDB
                self.collection.add(
                    embeddings=embeddings,
                    documents=doc_texts,
                    metadatas=doc_metadatas,
                    ids=ids
                )
                
                # Update indexed docs tracking
                self.indexed_docs[s3_key] = {
                    "size": file_size,
                    "last_modified": last_modified,
                    "chunks": len(texts),
                    "indexed_at": datetime.now().isoformat()
                }
                self._save_indexed_docs()
                
                logger.info(f"Successfully indexed {s3_key} with {len(texts)} chunks")
                return True
                
            finally:
                # Clean up temp file
                os.unlink(tmp_file_path)
                
        except ClientError as e:
            logger.error(f"Error downloading {s3_key} from S3: {e}")
            return False
        except Exception as e:
            logger.error(f"Error indexing {s3_key}: {e}")
            return False
    
    def index_all_documents(self) -> Dict[str, int]:
        """Index all documents in the S3 bucket"""
        stats = {"success": 0, "failed": 0, "skipped": 0}
        
        try:
            # List all objects in the bucket
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.s3_bucket_name)
            
            for page in pages:
                for obj in page.get('Contents', []):
                    s3_key = obj['Key']
                    
                    # Skip folders
                    if s3_key.endswith('/'):
                        continue
                    
                    # Check if file type is supported
                    ext = os.path.splitext(s3_key)[1].lower()
                    if ext not in ['.pdf', '.docx', '.doc', '.txt', '.md', '.pptx', '.ppt', '.xlsx', '.xls', '.csv']:
                        logger.info(f"Skipping unsupported file type: {s3_key}")
                        stats["skipped"] += 1
                        continue
                    
                    # Index the file
                    if self.download_and_index_file(s3_key):
                        stats["success"] += 1
                    else:
                        stats["failed"] += 1
            
            logger.info(f"Indexing complete. Success: {stats['success']}, Failed: {stats['failed']}, Skipped: {stats['skipped']}")
            return stats
            
        except ClientError as e:
            logger.error(f"Error listing objects in S3 bucket: {e}")
            return stats
    
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for relevant documents based on the query
        
        Args:
            query: The search query
            k: Number of results to return
            
        Returns:
            List of relevant documents with metadata
        """
        try:
            # Generate embedding for the query
            query_embedding = self.embeddings.embed_query(query)
            
            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            formatted_results = []
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    "content": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "score": 1 - results['distances'][0][i],  # Convert distance to similarity score
                    "source": results['metadatas'][0][i].get('source', 'Unknown')
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
    
    def get_context_for_prompt(self, query: str, k: int = 5) -> str:
        """
        Get relevant context for a prompt by searching the indexed documents
        
        Args:
            query: The user's query
            k: Number of relevant chunks to retrieve
            
        Returns:
            Formatted context string to include in the prompt
        """
        results = self.search(query, k=k)
        
        if not results:
            return ""
        
        # Format the context
        context_parts = []
        sources = set()
        
        for result in results:
            source = result['source']
            metadata = result['metadata']
            page_num = metadata.get('page', 'Unknown')
            # Create URL-encoded document link
            import urllib.parse
            encoded_source = urllib.parse.quote(source)
            doc_link = f"{self.base_url}/documents/{encoded_source}"
            
            sources.add(f"{source} (Page {page_num}) - [View Document]({doc_link})")
            content = result['content'].strip()
            context_parts.append(f"[From {source}, Page {page_num} - Link: {doc_link}]:\n{content}")
        
        context = "\n\n---\n\n".join(context_parts)
        
        # Add source attribution with page numbers and links
        source_list = "\n".join([f"- {source}" for source in sources])
        
        return f"""Based on the following relevant information from corporate card policy documents:

{context}

Sources consulted:
{source_list}"""
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the indexed documents"""
        try:
            # Get total documents in collection
            total_chunks = len(self.collection.get()['ids'])
            
            # Get unique sources
            all_metadata = self.collection.get()['metadatas']
            unique_sources = set(meta.get('source', '') for meta in all_metadata if meta)
            
            return {
                "total_documents": len(self.indexed_docs),
                "total_chunks": total_chunks,
                "unique_sources": len(unique_sources),
                "sources": list(unique_sources),
                "indexed_documents": self.indexed_docs
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {
                "total_documents": 0,
                "total_chunks": 0,
                "unique_sources": 0,
                "sources": [],
                "indexed_documents": {}
            }
    
    def clear_index(self):
        """Clear the entire index"""
        try:
            # Delete and recreate the collection
            self.chroma_client.delete_collection(name=self.collection_name)
            self.collection = self.chroma_client.create_collection(
                name=self.collection_name,
                metadata={"description": "Corporate card documents from S3"}
            )
            
            # Clear indexed docs tracking
            self.indexed_docs = {}
            self._save_indexed_docs()
            
            logger.info("Index cleared successfully")
            return True
        except Exception as e:
            logger.error(f"Error clearing index: {e}")
            return False