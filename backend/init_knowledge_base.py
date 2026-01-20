import chromadb
import os

def initialize_knowledge_base():
    """Initialize ChromaDB with demo documents"""
    
    # Use persistent ChromaDB storage
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chroma_db_v2')
    client = chromadb.PersistentClient(path=db_path)
    
    # Demo documents directory
    demo_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'knowledge_base')
    
    # Sector to document mapping
    sector_docs = {
        "banking": "DEMO 1 BANKING - Account & Loan Support.txt",
        "financial": "DEMO 2 FINANCIAL SERVICES - Investment & Wealth Management.txt",
        "insurance": "DEMO 3 INSURANCE - Policy & Claim Support.txt",
        "bpo": "DEMO 4 BPOKPO - Customer Support & Ticketing.txt",
        "healthcare_appt": "DEMO 5 HEALTHCARE - Appointment Scheduling & Clinic Services.txt",
        "healthcare_patient": "DEMO 6 HEALTHCARE - Patient Support & Medical Records.txt"
    }
    
    for sector, filename in sector_docs.items():
        filepath = os.path.join(demo_dir, filename)
        
        if not os.path.exists(filepath):
            print(f"Warning: {filename} not found. Skipping {sector}.")
            continue
        
        # Read document content
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split into chunks (simple paragraph-based chunking)
        chunks = [chunk.strip() for chunk in content.split('\n\n') if chunk.strip()]
        
        # Create or get collection
        collection_name = f"{sector}_knowledge"
        try:
            # Try to delete existing collection first
            try:
                client.delete_collection(name=collection_name)
                print(f"  Deleted existing {sector} collection")
            except:
                pass  # Collection doesn't exist, that's fine
            
            # Create fresh collection
            collection = client.create_collection(name=collection_name)
            
            # Add documents to collection
            if chunks:
                collection.add(
                    documents=chunks,
                    ids=[f"{sector}_{i}" for i in range(len(chunks))],
                    metadatas=[{"sector": sector, "chunk_id": i} for i in range(len(chunks))]
                )
                print(f"✓ Initialized {sector} knowledge base with {len(chunks)} chunks")
        except Exception as e:
            print(f"Error initializing {sector}: {str(e)}")
    
    print("\n✅ Knowledge base initialization complete!")

if __name__ == "__main__":
    initialize_knowledge_base()
