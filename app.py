from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid
import os
import fitz  # PyMuPDF for PDF reading
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import openai

# ===== CONFIGURATION =====
PDF_FILE = 'SBI.pdf'  # your PDF
EMBED_MODEL = 'all-MiniLM-L6-v2'
openai.api_key = os.getenv('OPENAI_API_KEY')  # Set your OpenAI API Key in environment

# ===== SETUP =====
app = Flask(__name__)
CORS(app)

# In-memory session storage
chat_sessions = {}

# Load embedder
embedder = SentenceTransformer(EMBED_MODEL)

# FAISS index setup
embedding_dimension = 384  # Dimension of 'all-MiniLM-L6-v2' model
index = faiss.IndexFlatL2(embedding_dimension)

# Document chunks and corresponding texts
doc_chunks = []  # List of text chunks


def load_and_split_pdf(pdf_path, chunk_size=500):
    """Load the PDF and split it into chunks"""
    doc = fitz.open(pdf_path)
    texts = []
    for page in doc:
        text = page.get_text()
        # Split into small chunks (by sentence/words approx)
        words = text.split()
        for i in range(0, len(words), chunk_size):
            chunk = ' '.join(words[i:i+chunk_size])
            texts.append(chunk)
    return texts


def create_vector_store(texts):
    """Create embeddings and build FAISS index"""
    embeddings = embedder.encode(texts)
    index.add(np.array(embeddings).astype('float32'))
    return embeddings


def retrieve_relevant_chunks(query, top_k=3):
    """Retrieve top_k relevant chunks"""
    query_embedding = embedder.encode([query]).astype('float32')
    distances, indices = index.search(query_embedding, top_k)
    retrieved_texts = [doc_chunks[idx] for idx in indices[0] if idx < len(doc_chunks)]
    return retrieved_texts


def generate_answer(context, query):
    """Generate an answer using OpenAI"""
    prompt = f"""You are an assistant specialized in SBI's fraud detection system.
Use the following context from the official document to answer the user's question.

Context:
{context}

Question: {query}

Answer:"""
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=500
    )
    return response['choices'][0]['message']['content'].strip()


# ===== Load documents on startup =====
print("Loading and indexing the document...")
doc_chunks = load_and_split_pdf(PDF_FILE)
create_vector_store(doc_chunks)
print(f"Loaded {len(doc_chunks)} chunks.")


# ===== ROUTES =====

@app.route('/')
def index():
    return jsonify({"status": "online", "message": "SBI Fraud Detection RAG API running"})

@app.route('/chat/start', methods=['POST'])
def start_chat():
    session_id = str(uuid.uuid4())
    chat_sessions[session_id] = {
        "created_at": uuid.uuid1().time,
        "chat_history": []
    }
    return jsonify({"session_id": session_id})

@app.route('/chat/history/<session_id>', methods=['GET'])
def get_history(session_id):
    if session_id not in chat_sessions:
        return jsonify({"error": "Invalid session ID"}), 404
    return jsonify(chat_sessions[session_id])

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    if not data or 'query' not in data or 'session_id' not in data:
        return jsonify({"error": "Missing parameters"}), 400

    session_id = data['session_id']
    query = data['query']

    if session_id not in chat_sessions:
        return jsonify({"error": "Invalid session ID"}), 404

    retrieved_chunks = retrieve_relevant_chunks(query)
    context = "\n\n".join(retrieved_chunks)

    response_text = generate_answer(context, query)

    # Save to history
    chat_sessions[session_id]["chat_history"].append({
        "query": query,
        "response": response_text
    })

    return jsonify({
        "response": response_text,
        "session_id": session_id
    })


# ===== Run the app =====
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
