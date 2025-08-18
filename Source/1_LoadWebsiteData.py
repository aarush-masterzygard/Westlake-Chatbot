from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import CharacterTextSplitter
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import tempfile
import PyPDF2
from langchain.schema import Document
import re

load_dotenv(dotenv_path="Environment/API-Key.env")

# Get API key - try multiple sources
OPENAI_API_KEY = None

# First try environment variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# If not found, try reading from secrets file directly
if not OPENAI_API_KEY:
    try:
        secrets_paths = [
            "Source/.streamlit/secrets.toml",
            ".streamlit/secrets.toml"
        ]
        
        for secrets_path in secrets_paths:
            if os.path.exists(secrets_path):
                with open(secrets_path, "r") as f:
                    content = f.read()
                    # Simple parsing for OPENAI_API_KEY
                    for line in content.split('\n'):
                        if 'OPENAI_API_KEY' in line and '=' in line:
                            # Extract the key value
                            key_value = line.split('=', 1)[1].strip().strip('"').strip("'")
                            if key_value and key_value.startswith('sk-'):
                                OPENAI_API_KEY = key_value
                                print(f"✅ Using API key from {secrets_path}")
                                break
                if OPENAI_API_KEY:
                    break
    except Exception as e:
        print(f"⚠️ Could not read secrets file: {e}")

if not OPENAI_API_KEY:
    print("❌ No OpenAI API key found!")
    print("Please set your API key in:")
    print("  - Environment/API-Key.env")
    print("  - Source/.streamlit/secrets.toml")
    exit(1)
else:
    print(f"✅ API key loaded successfully")

'''To switch between URLs, just change the last line:

base_url = test_url (for testing)
base_url = westlake_url (for Westlake High School)
'''

# PDF Processing Configuration
PDF_SIZE_LIMIT = 15 * 1024 * 1024  # 15MB per PDF (increased to handle largest file)
TOTAL_PDF_LIMIT = 100 * 1024 * 1024  # 100MB total across all PDFs (increased for comprehensive processing)
MAX_PAGES_PER_PDF = 100  # Maximum pages to process per PDF
PDF_CHUNK_SIZE = 1000  # Characters per chunk for PDF content
MAX_PDFS_TO_PROCESS = 100  # Process all PDFs found (was 10)

def find_pdf_links(base_url, all_urls):
    """
    Find all PDF links from the scraped website pages
    """
    pdf_links = set()
    
    print(f"\n🔍 Searching for PDF links across {len(all_urls)} pages...")
    
    for i, url in enumerate(all_urls, 1):
        try:
            print(f"📄 Scanning page {i}/{len(all_urls)}: {url}")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all links that point to PDFs
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(url, href)
                
                # Check if it's a PDF link
                if full_url.lower().endswith('.pdf'):
                    pdf_links.add(full_url)
                    print(f"   📄 Found PDF: {full_url}")
            
            # Also search for PDF links in text content using regex
            text_content = soup.get_text()
            pdf_pattern = r'https?://[^\s<>"]+\.pdf'
            regex_pdfs = re.findall(pdf_pattern, text_content, re.IGNORECASE)
            
            for pdf_url in regex_pdfs:
                full_pdf_url = urljoin(url, pdf_url)
                if urlparse(full_pdf_url).netloc == urlparse(base_url).netloc:
                    pdf_links.add(full_pdf_url)
                    print(f"   📄 Found PDF (regex): {full_pdf_url}")
            
            time.sleep(2.5)  # Be respectful - increased delay between web page scraping
            
        except Exception as e:
            print(f"   ⚠️ Error scanning {url}: {e}")
            continue
    
    print(f"\n✅ Found {len(pdf_links)} unique PDF files")
    return list(pdf_links)

def download_and_process_pdf(pdf_url, max_size=PDF_SIZE_LIMIT):
    """
    Download and extract text from a PDF file with detailed logging
    """
    filename = os.path.basename(pdf_url)
    
    try:
        print(f"   🔄 Step 1: Checking PDF size...")
        
        # Check PDF size before downloading
        head_response = requests.head(pdf_url, timeout=30)
        content_length = head_response.headers.get('content-length')
        
        if content_length:
            size_mb = int(content_length) / (1024 * 1024)
            if int(content_length) > max_size:
                print(f"   ❌ PDF too large: {size_mb:.1f}MB (limit: {max_size/(1024*1024):.1f}MB)")
                return None
            print(f"   ✅ Size check passed: {size_mb:.1f}MB")
        else:
            print(f"   ⚠️ Could not determine PDF size, proceeding with download...")
        
        print(f"   🔄 Step 2: Downloading PDF...")
        # Download the PDF with longer timeout and retry logic
        max_retries = 2
        for attempt in range(max_retries):
            try:
                response = requests.get(pdf_url, timeout=60)  # Increased to 60 seconds
                response.raise_for_status()
                break
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    print(f"   ⚠️ Timeout on attempt {attempt + 1}, retrying...")
                    time.sleep(2)
                    continue
                else:
                    raise
        print(f"   ✅ Download completed: {len(response.content)/1024:.1f}KB")
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(response.content)
            temp_file_path = temp_file.name
        
        try:
            print(f"   🔄 Step 3: Opening PDF and checking structure...")
            # Extract text from PDF
            with open(temp_file_path, 'rb') as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                
                # Check number of pages
                num_pages = len(pdf_reader.pages)
                if num_pages > MAX_PAGES_PER_PDF:
                    print(f"   ❌ PDF has too many pages: {num_pages} (limit: {MAX_PAGES_PER_PDF})")
                    return None
                
                print(f"   ✅ PDF structure valid: {num_pages} pages")
                print(f"   🔄 Step 4: Extracting text from {num_pages} pages...")
                
                # Extract text from all pages
                full_text = ""
                pages_processed = 0
                pages_with_text = 0
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text.strip():  # Only add non-empty pages
                            full_text += f"\n\n--- Page {page_num} ---\n{page_text}"
                            pages_processed += 1
                            pages_with_text += 1
                            
                            # Show progress for larger PDFs
                            if num_pages > 5 and page_num % 5 == 0:
                                print(f"      📄 Processed {page_num}/{num_pages} pages...")
                        
                        # Stop if we hit the page limit
                        if page_num >= MAX_PAGES_PER_PDF:
                            break
                            
                    except Exception as e:
                        print(f"      ⚠️ Error processing page {page_num}: {e}")
                        continue
                
                if full_text.strip():
                    print(f"   ✅ Step 5: Text extraction completed!")
                    print(f"      📊 Pages with text: {pages_with_text}/{num_pages}")
                    print(f"      📊 Total characters: {len(full_text):,}")
                    print(f"      📊 Average chars per page: {len(full_text)//pages_with_text if pages_with_text > 0 else 0}")
                    
                    # Create document with metadata
                    doc = Document(
                        page_content=full_text,
                        metadata={
                            'source': pdf_url,
                            'filename': filename,
                            'type': 'pdf',
                            'pages': pages_processed,
                            'characters': len(full_text),
                            'total_pages': num_pages,
                            'pages_with_text': pages_with_text
                        }
                    )
                    return doc
                else:
                    print(f"   ❌ No readable text found in PDF")
                    print(f"      This might be a scanned/image-based PDF")
                    return None
                    
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
                print(f"   🧹 Temporary file cleaned up")
            except:
                pass
                
    except requests.exceptions.Timeout:
        print(f"   ❌ Download timeout for {filename}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Download error for {filename}: {e}")
        return None
    except Exception as e:
        print(f"   ❌ Unexpected error processing {filename}: {e}")
        return None

def process_all_pdfs(pdf_links, max_pdfs_limit=MAX_PDFS_TO_PROCESS):
    """
    Process found PDF files with comprehensive limits and detailed logging
    """
    if not pdf_links:
        print("📄 No PDF files found to process")
        return []
    
    # Limit the number of PDFs to process
    pdfs_to_process = pdf_links[:max_pdfs_limit]
    
    print(f"\n📚 Found {len(pdf_links)} PDF files, processing first {len(pdfs_to_process)}...")
    print(f"🛡️ Safety limits:")
    print(f"   📊 Max PDFs to process: {max_pdfs_limit}")
    print(f"   📊 Max size per PDF: {PDF_SIZE_LIMIT/(1024*1024):.1f}MB")
    print(f"   📊 Max total PDF content: {TOTAL_PDF_LIMIT/(1024*1024):.1f}MB")
    print(f"   📄 Max pages per PDF: {MAX_PAGES_PER_PDF}")
    
    # Show all PDFs that will be processed
    print(f"\n📋 PDFs to be processed:")
    for i, pdf_url in enumerate(pdfs_to_process, 1):
        filename = os.path.basename(pdf_url)
        print(f"   {i}. {filename}")
        print(f"      URL: {pdf_url}")
    
    if len(pdf_links) > max_pdfs_limit:
        print(f"\n⚠️ Note: {len(pdf_links) - max_pdfs_limit} additional PDFs found but skipped due to limit")
        print("   Skipped PDFs:")
        for i, pdf_url in enumerate(pdf_links[max_pdfs_limit:], max_pdfs_limit + 1):
            filename = os.path.basename(pdf_url)
            print(f"   {i}. {filename}")
    
    pdf_documents = []
    total_size = 0
    successful_pdfs = 0
    failed_pdfs = 0
    
    print(f"\n🔄 Starting PDF processing...")
    print("=" * 60)
    
    for i, pdf_url in enumerate(pdfs_to_process, 1):
        filename = os.path.basename(pdf_url)
        print(f"\n📄 Processing PDF {i}/{len(pdfs_to_process)}: {filename}")
        print(f"🔗 URL: {pdf_url}")
        
        # Check if we've hit the total size limit
        if total_size > TOTAL_PDF_LIMIT:
            print(f"⚠️ Reached total PDF size limit ({TOTAL_PDF_LIMIT/(1024*1024):.1f}MB)")
            print(f"   Stopping processing. Remaining PDFs will be skipped.")
            break
        
        doc = download_and_process_pdf(pdf_url)
        
        if doc:
            pdf_documents.append(doc)
            content_size = len(doc.page_content)
            total_size += content_size
            successful_pdfs += 1
            
            print(f"   ✅ SUCCESS: {doc.metadata['filename']}")
            print(f"   📊 Pages processed: {doc.metadata.get('pages', 'unknown')}")
            print(f"   📊 Content size: {content_size/1024:.1f}KB")
            print(f"   📊 Running total: {total_size/(1024*1024):.1f}MB")
        else:
            failed_pdfs += 1
            print(f"   ❌ FAILED: Could not process {filename}")
        
        # Add delay between PDF processing to be respectful to the server
        if i < len(pdfs_to_process):  # Don't delay after the last PDF
            time.sleep(5)  # Increased delay between PDF processing
    
    print(f"\n" + "=" * 60)
    print(f"📊 PDF Processing Complete!")
    print(f"   ✅ Successfully processed: {successful_pdfs} PDFs")
    print(f"   ❌ Failed to process: {failed_pdfs} PDFs")
    print(f"   📝 Total PDF content: {total_size/(1024*1024):.1f}MB")
    print(f"   📄 Total PDF documents: {len(pdf_documents)}")
    
    if successful_pdfs > 0:
        print(f"\n📋 Successfully processed PDFs:")
        for i, doc in enumerate(pdf_documents, 1):
            filename = doc.metadata.get('filename', 'unknown.pdf')
            pages = doc.metadata.get('pages', 'unknown')
            size_kb = len(doc.page_content) / 1024
            print(f"   {i}. {filename} ({pages} pages, {size_kb:.1f}KB)")
    
    return pdf_documents

def get_all_links(base_url, max_pages=50):
    """
    Scrape the website to find all internal links
    """
    visited = set()
    to_visit = [base_url]
    all_links = []
    
    print(f"🕷️ Starting to scrape {base_url}...")
    
    while to_visit and len(all_links) < max_pages:
        current_url = to_visit.pop(0)
        
        if current_url in visited:
            continue
            
        visited.add(current_url)
        
        try:
            print(f"📄 Scraping: {current_url}")
            response = requests.get(current_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Add current URL to our list
            all_links.append(current_url)
            
            # Find all links on this page
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(current_url, href)
                
                # Only include links from the same domain
                if urlparse(full_url).netloc == urlparse(base_url).netloc:
                    # Skip certain file types and fragments
                    if not any(full_url.lower().endswith(ext) for ext in ['.pdf', '.jpg', '.png', '.gif', '.doc', '.docx']):
                        if '#' not in full_url and full_url not in visited and full_url not in to_visit:
                            to_visit.append(full_url)
            
            # Be respectful - increased delay between wets
            time.sleep(1)
            
        except Exception as e:
            print(f"⚠️ Error scraping {current_url}: {e}")
            continue
    
    print(f"✅ Found {len(all_links)} pages to index")
    return all_links

def load_and_process_website(base_url, max_pages=50, max_pdfs=10):
    """
    Load multiple pages from the website and create a comprehensive vector database with PDF support
    """
    print("🌐 Enhanced Westlake High School Website + PDF Loader")
    print("=" * 60)
    
    # Get all links to scrape
    all_urls = get_all_links(base_url, max_pages)
    
    # Find and process PDF files
    pdf_links = find_pdf_links(base_url, all_urls)
    pdf_documents = process_all_pdfs(pdf_links, max_pdfs)
    
    print(f"\n📚 Loading content from {len(all_urls)} web pages...")
    
    # Load content from all URLs
    all_docs = []
    successful_loads = 0
    failed_loads = 0
    
    for i, url in enumerate(all_urls, 1):
        try:
            print(f"📖 Loading content from ({i}/{len(all_urls)}): {url}")
            loader = WebBaseLoader(url)
            docs = loader.load()
            
            # Verify we got content
            if docs and docs[0].page_content.strip():
                all_docs.extend(docs)
                successful_loads += 1
                print(f"   ✅ Loaded {len(docs[0].page_content)} characters")
            else:
                print(f"   ⚠️ No content found")
                failed_loads += 1
                
        except Exception as e:
            print(f"   ❌ Failed to load: {e}")
            failed_loads += 1
            continue
    
    # Add PDF documents to the main document collection
    all_docs.extend(pdf_documents)
    
    print(f"\n📊 Loading Summary:")
    print(f"   ✅ Successfully loaded web pages: {successful_loads}")
    print(f"   ✅ Successfully loaded PDFs: {len(pdf_documents)}")
    print(f"   ❌ Failed to load: {failed_loads} pages")
    print(f"   📄 Total documents before splitting: {len(all_docs)} (web + PDF)")
    
    if not all_docs:
        print("❌ No content was successfully loaded!")
        return
    
    # Split all documents into chunks for better embedding
    print(f"\n✂️ Splitting documents into chunks...")
    
    # Use different splitters for web content vs PDF content
    web_text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=600,  # Smaller chunks for web content
        chunk_overlap=100,
        length_function=len
    )
    
    pdf_text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=PDF_CHUNK_SIZE,  # Larger chunks for PDF content
        chunk_overlap=150,  # More overlap for PDFs to maintain context
        length_function=len
    )
    
    all_chunks = []
    total_chars = 0
    max_chunk_size = 0
    
    for i, doc in enumerate(all_docs):
        # Skip documents that are extremely large
        if len(doc.page_content) > 200000:  # Skip docs over 200k characters (increased for PDFs)
            print(f"   ⚠️ Document {i+1}: {len(doc.page_content)} chars - TOO LARGE, SKIPPING")
            continue
        
        # Determine document type and use appropriate splitter
        is_pdf = doc.metadata.get('type') == 'pdf'
        splitter = pdf_text_splitter if is_pdf else web_text_splitter
        doc_type = "PDF" if is_pdf else "Web"
        
        chunks = splitter.split_documents([doc])
        
        # Filter out chunks that are still too large
        valid_chunks = []
        for chunk in chunks:
            chunk_tokens = len(chunk.page_content.split()) * 1.3  # Rough token estimate
            if chunk_tokens < 8000:  # Well below 8192 token limit
                # Add source type to chunk metadata
                chunk.metadata['content_type'] = doc_type.lower()
                if is_pdf:
                    chunk.metadata['filename'] = doc.metadata.get('filename', 'unknown.pdf')
                    chunk.metadata['source_pages'] = doc.metadata.get('pages', 'unknown')
                
                valid_chunks.append(chunk)
                max_chunk_size = max(max_chunk_size, len(chunk.page_content))
            else:
                print(f"   ⚠️ Skipping oversized chunk: {int(chunk_tokens)} tokens")
        
        all_chunks.extend(valid_chunks)
        total_chars += len(doc.page_content)
        
        if is_pdf:
            filename = doc.metadata.get('filename', 'unknown.pdf')
            pages = doc.metadata.get('pages', 'unknown')
            print(f"   📄 {doc_type} {i+1} ({filename}, {pages} pages): {len(doc.page_content)} chars → {len(valid_chunks)} valid chunks")
        else:
            print(f"   📄 {doc_type} {i+1}: {len(doc.page_content)} chars → {len(valid_chunks)} valid chunks")
    
    print(f"\n📊 Chunking Summary:")
    print(f"   📄 Total chunks created: {len(all_chunks)}")
    print(f"   📝 Total characters processed: {total_chars:,}")
    print(f"   📊 Average chunk size: {total_chars // len(all_chunks) if all_chunks else 0} chars")
    print(f"   📊 Largest chunk size: {max_chunk_size} chars")
    print(f"   📊 Estimated max tokens per chunk: {int(max_chunk_size * 1.3)} tokens")
    
    # Create embeddings and save to vector database
    if all_chunks:
        print(f"\n🧠 Creating embeddings and building vector database...")
        print(f"   🔄 Processing {len(all_chunks)} chunks with OpenAI embeddings...")
        
        try:
            # Initialize embeddings model
            embeddings_model = OpenAIEmbeddings(
                openai_api_key=OPENAI_API_KEY, 
                model="text-embedding-3-small"
            )
            
            # Create FAISS vector database from all chunks
            print(f"   🔄 Converting text to embeddings...")
            
            # Calculate estimated token usage and cost
            total_tokens_estimate = sum(len(chunk.page_content.split()) * 1.3 for chunk in all_chunks)  # ~1.3 tokens per word
            
            # OpenAI text-embedding-3-small pricing information
            cost_per_1k_tokens = 0.00002  # $0.00002 per 1,000 tokens
            estimated_cost = (total_tokens_estimate / 1000) * cost_per_1k_tokens
            
            print(f"   📊 OpenAI Model: text-embedding-3-small")
            print(f"   📊 Max Token Limit: 8,192 tokens")
            print(f"   📊 Embedding Dimension: 1,536")
            print(f"   📊 Estimated tokens to be processed: {int(total_tokens_estimate):,}")
            print(f"   💰 Estimated cost: ${estimated_cost:.6f} (${cost_per_1k_tokens} per 1K tokens)")
            
            # Process chunks in smaller batches to avoid API limits
            batch_size = 50  # Process 50 chunks at a time
            print(f"   🔄 Processing {len(all_chunks)} chunks in batches of {batch_size}...")
            
            if len(all_chunks) <= batch_size:
                # Small number of chunks - process all at once
                vectordb = FAISS.from_documents(all_chunks, embeddings_model)
            else:
                # Large number of chunks - process in batches
                print(f"   📦 Batch 1/{(len(all_chunks) + batch_size - 1) // batch_size}: Processing first {min(batch_size, len(all_chunks))} chunks...")
                vectordb = FAISS.from_documents(all_chunks[:batch_size], embeddings_model)
                
                # Add remaining chunks in batches
                for i in range(batch_size, len(all_chunks), batch_size):
                    batch_num = (i // batch_size) + 1
                    total_batches = (len(all_chunks) + batch_size - 1) // batch_size
                    batch_end = min(i + batch_size, len(all_chunks))
                    batch_chunks = all_chunks[i:batch_end]
                    
                    print(f"   📦 Batch {batch_num}/{total_batches}: Processing chunks {i+1}-{batch_end}...")
                    batch_vectordb = FAISS.from_documents(batch_chunks, embeddings_model)
                    vectordb.merge_from(batch_vectordb)
                    
                    # Small delay between batches to be respectful to API
                    time.sleep(1)
            
            # Save the vector database
            index_Faiss_Filepath = "index.faiss"
            print(f"   💾 Saving vector database to {index_Faiss_Filepath}...")
            vectordb.save_local(index_Faiss_Filepath)
            
            print(f"\n🎉 SUCCESS! Enhanced website data with PDF support loaded and indexed!")
            print(f"📊 Final Database Stats:")
            print(f"   🌐 Web pages scraped: {successful_loads}")
            print(f"   📄 PDF files processed: {len(pdf_documents)}")
            print(f"   🧩 Total document chunks: {len(all_chunks)}")
            print(f"   🧠 Embeddings created: {len(all_chunks)}")
            print(f"   💾 Vector database size: {vectordb.index.ntotal} vectors")
            
            # Count chunks by type
            web_chunks = sum(1 for chunk in all_chunks if chunk.metadata.get('content_type') == 'web')
            pdf_chunks = sum(1 for chunk in all_chunks if chunk.metadata.get('content_type') == 'pdf')
            print(f"   📊 Web content chunks: {web_chunks}")
            print(f"   📊 PDF content chunks: {pdf_chunks}")
            
        except Exception as e:
            print(f"❌ Error creating vector database: {e}")
            return
            
    else:
        print("❌ No chunks created - cannot build vector database!")

if __name__ == "__main__":
    # URL Variables - Control which website to scrape
    westlake_url = "https://whs.conejousd.org/"
    test_url = "https://riordan.fandom.com/wiki/Percy_Jackson"
    
    # Choose which URL to use
    base_url = westlake_url
    
    # 🛡️ SAFETY CONTROLS - Adjust these based on your needs
    # =====================================================
    
    # Number of pages to scrape (MAIN SAFETY CONTROL)
    max_pages = 150  # Start small and safe - increase gradually if needed
    
    # PDF Processing limits
    max_pdfs = 150  # Number of PDFs to process (reduced for better reliability)
    
    # Recommended settings:
    # max_pages = 5   # Very safe - good for testing
    # max_pages = 15  # Moderate - good balance
    # max_pages = 30  # Comprehensive - use if you need more content
    # max_pages = 50  # Maximum - only if absolutely necessary
    
    # PDF settings:
    # max_pdfs = 3   # Very safe - good for testing
    # max_pdfs = 5   # Moderate - good balance (current setting)
    # max_pdfs = 10  # Comprehensive - use if you need more PDFs
    # max_pdfs = 15  # Maximum - only if absolutely necessary
    
    print(f"🚀 Starting website + PDF processing with safety limits...")
    print(f"🎯 Target: {base_url}")
    print(f"🛡️ Max pages to scrape: {max_pages}")
    print(f"📄 Max PDFs to process: {max_pdfs}")
    print(f"⏱️ Delay between requests: 1.0 seconds")
    print(f"⏰ Timeout per page: 10 seconds")
    print()
    
    # Safety confirmation for larger scraping jobs
    if max_pages > 20 or max_pdfs > 5:
        print("⚠️ WARNING: You're about to process a large amount of content.")
        print("This may take several minutes and use more API credits.")
        response = input("Continue? (Y/N): ").lower().strip()
        if response != 'y':
            print("❌ Processing cancelled for safety.")
            exit()
    
    load_and_process_website(base_url, max_pages, max_pdfs)