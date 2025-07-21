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

load_dotenv(dotenv_path="Environment/API-Key.env")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


'''To switch between URLs, just change the last line (194):

base_url = test_url (currently active)
base_url = beachside_url (to use Beachside)
'''


def get_all_links(base_url, max_pages=50):
    """
    scrape the website to find all internal links
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
            
            # Be respectful - small delay between requests
            time.sleep(1)
            
        except Exception as e:
            print(f"⚠️ Error scraping {current_url}: {e}")
            continue
    
    print(f"✅ Found {len(all_links)} pages to index")
    return all_links

def load_and_process_website(base_url, max_pages=50):
    """
    Load multiple pages from the website and create a comprehensive vector database
    """
    print("🌐 Enhanced Beachside High School Website Loader")
    print("=" * 60)
    
    # Get all links to scrape
    all_urls = get_all_links(base_url, max_pages)
    
    print(f"\n📚 Loading content from {len(all_urls)} pages...")
    
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
    
    print(f"\n📊 Loading Summary:")
    print(f"   ✅ Successfully loaded: {successful_loads} pages")
    print(f"   ❌ Failed to load: {failed_loads} pages")
    print(f"   📄 Total documents before splitting: {len(all_docs)}")
    
    if not all_docs:
        print("❌ No content was successfully loaded!")
        return
    
    # Split all documents into chunks for better embedding
    print(f"\n✂️ Splitting documents into chunks...")
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=800,  # Below 1000 as requested
        chunk_overlap=200,  # Overlap to ensure nothing is missed
        length_function=len
    )
    
    all_chunks = []
    total_chars = 0
    
    for i, doc in enumerate(all_docs):
        chunks = text_splitter.split_documents([doc])
        all_chunks.extend(chunks)
        total_chars += len(doc.page_content)
        print(f"   📄 Document {i+1}: {len(doc.page_content)} chars → {len(chunks)} chunks")
    
    print(f"\n📊 Chunking Summary:")
    print(f"   📄 Total chunks created: {len(all_chunks)}")
    print(f"   📝 Total characters processed: {total_chars:,}")
    print(f"   📊 Average chunk size: {total_chars // len(all_chunks) if all_chunks else 0} chars")
    
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
            
            vectordb = FAISS.from_documents(all_chunks, embeddings_model)
            
            # Note: Actual token usage from OpenAI API is not directly accessible
            # The estimate above is approximate based on text length
            
            # Save the vector database
            index_Faiss_Filepath = "index.faiss"
            print(f"   💾 Saving vector database to {index_Faiss_Filepath}...")
            vectordb.save_local(index_Faiss_Filepath)
            
            print(f"\n🎉 SUCCESS! Enhanced website data loaded and indexed!")
            print(f"📊 Final Database Stats:")
            print(f"   📄 Pages scraped: {successful_loads}")
            print(f"   🧩 Document chunks: {len(all_chunks)}")
            print(f"   🧠 Embeddings created: {len(all_chunks)}")
            print(f"   💾 Vector database size: {vectordb.index.ntotal} vectors")
            
            # Test the database with some sample searches
            # print(f"\n🔍 Testing database with sample searches...")
            # test_queries = ["AICE program", "contact information", "academic programs", "extracurricular activities"]
            # 
            # for query in test_queries:
            #     results = vectordb.similarity_search(query, k=1)
            #     if results:
            #         print(f"   ✅ '{query}': Found relevant content")
            #     else:
            #         print(f"   ⚠️ '{query}': No results")
            
        except Exception as e:
            print(f"❌ Error creating vector database: {e}")
            return
            
    else:
        print("❌ No chunks created - cannot build vector database!")

if __name__ == "__main__":
    # URL Variables - Control which website to scrape
    beachside_url = "https://www-bhs.stjohns.k12.fl.us/"
    test_url = "https://riordan.fandom.com/wiki/Percy_Jackson"
    
    # Choose which URL to use (currently using test_url)
    base_url = beachside_url
    
    # 🛡️ SAFETY CONTROLS - Adjust these based on your needs
    # =====================================================
    
    # Number of pages to scrape (MAIN SAFETY CONTROL)
    max_pages = 5  # Start small and safe - increase gradually if needed
    
    # Recommended settings:
    # max_pages = 5   # Very safe - good for testing
    # max_pages = 15  # Moderate - good balance
    # max_pages = 30  # Comprehensive - use if you need more content
    # max_pages = 50  # Maximum - only if absolutely necessary
    
    print(f"🚀 Starting website scraping with safety limits...")
    print(f"🎯 Target: {base_url}")
    print(f"🛡️ Max pages to scrape: {max_pages}")
    print(f"⏱️ Delay between requests: 0.5 seconds")
    print(f"⏰ Timeout per page: 10 seconds")
    print()
    
    # Safety confirmation for larger scraping jobs
    if max_pages > 20:
        print("⚠️ WARNING: You're about to scrape more than 20 pages.")
        print("This may take several minutes and use more API credits.")
        response = input("Continue? (y/N): ").lower().strip()
        if response != 'y':
            print("❌ Scraping cancelled for safety.")
            exit()
    
    load_and_process_website(base_url, max_pages)
