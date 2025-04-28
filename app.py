from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid
import os
import time
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# In-memory store for chat sessions and history
# For production, consider using a database like PostgreSQL or MongoDB
chat_sessions = {}

@app.route('/')
def index():
    return jsonify({"status": "online", "message": "SBI Fraud Detection Chatbot API is running"})

@app.route('/chat/start', methods=['POST'])
def start_chat():
    """Initialize a new chat session and return session ID"""
    session_id = str(uuid.uuid4())
    
    # Initialize session with timestamp
    chat_sessions[session_id] = {
        "created_at": datetime.now().isoformat(),
        "chat_history": []
    }
    
    return jsonify({"session_id": session_id})

@app.route('/chat/history/<session_id>', methods=['GET'])
def get_chat_history(session_id):
    """Retrieve chat history for a session"""
    if session_id not in chat_sessions:
        return jsonify({"error": "Session not found"}), 404
    
    return jsonify(chat_sessions[session_id])

@app.route('/chat', methods=['POST'])
def chat():
    """Process user message and provide response"""
    data = request.json
    
    if not data or not 'query' in data or not 'session_id' in data:
        return jsonify({"error": "Missing query or session_id parameter"}), 400
    
    session_id = data['session_id']
    user_query = data['query']
    
    # Check if session exists
    if session_id not in chat_sessions:
        return jsonify({"error": "Invalid or expired session"}), 404
    
    # Process the user query
    # For now, implementing some simple response logic
    # In a real app, you would integrate with a more sophisticated AI system
    response = generate_response(user_query)
    
    # Add message to chat history
    chat_sessions[session_id]["chat_history"].append({
        "timestamp": datetime.now().isoformat(),
        "query": user_query,
        "response": response
    })
    
    return jsonify({
        "response": response,
        "session_id": session_id
    })

def generate_response(query):
    """Generate a chatbot response based on user query"""
    # Lowercase the query for easier matching
    query_lower = query.lower()
    
    # Basic response mapping - expanded for more scenarios
    responses = {
        "hello": "Hello! How can I help you with SBI Fraud Detection today?",
        "hi": "Hi there! How can I assist you with fraud detection?",
        "help": "I can help you understand SBI's fraud detection services, explain how to report suspicious activities, or provide general information about our security features.",
        "fraud": "SBI's fraud detection system uses advanced AI to identify suspicious patterns and activities. We monitor transactions 24/7 to keep your accounts safe.",
        "report": "To report suspicious activity, please use the 'Manual Data Entry' feature in the Detection menu or contact our 24/7 fraud reporting line at 1-800-SBI-FRAUD.",
        "account": "To check if your account is secure, please log in to your SBI online banking and review the 'Security Center' section. You can also set up fraud alerts in your account settings.",
        "suspicious": "If you've noticed suspicious transactions, please immediately call our fraud hotline at 1-800-SBI-FRAUD and freeze your account from the SBI mobile app.",
        "phishing": "Beware of phishing attempts. SBI will never ask for your full password, OTP, or PIN via email or phone. Always use our official website or app for transactions.",
        "otp": "Never share your OTP (One-Time Password) with anyone. SBI representatives will never ask for your OTP over phone or email.",
        "secure": "SBI uses multi-layer security protocols, including biometric authentication, encryption, and AI-based fraud monitoring to keep your accounts secure.",
        "contact": "You can reach our support team at support@sbifraud.com or call our hotline at 1-800-SBI-HELP.",
        "thank": "You're welcome! Is there anything else I can help you with today?",
        "bye": "Thank you for chatting with SBI Fraud Detection Assistant. Have a great day and stay secure!"
    }
    
    # Check for keyword matches
    for keyword, response in responses.items():
        if keyword in query_lower:
            return response
    
    # Default response if no keywords match
    return "Thank you for your question. Our fraud detection system constantly monitors for suspicious activities on your account. Is there anything specific about fraud prevention or detection that you'd like to know more about?"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)