"""
Multi-Agent Architecture for Voice Agent Demo
==============================================
Implements a Router Agent + Specialized Agents pattern for better query handling
"""

import logging
from typing import Tuple, List, Dict, Optional

logger = logging.getLogger("voice_agent")

# ==================== AGENT DEFINITIONS ====================

AGENT_TYPES = {
    "banking": {
        "name": "Banking Specialist",
        "description": "Handles bank accounts, loans, cards, transactions",
        "keywords": ["account", "balance", "loan", "card", "debit", "credit", "transfer", "atm", "upi", "neft", "imps", "cheque", "fd", "deposit", "withdraw", "interest", "emi", "statement"],
        "prompt": """You are a Banking Specialist AI Agent. Your expertise:
- Bank accounts (savings, current, FD)
- Loans (personal, home, car, education)
- Credit/Debit cards
- Fund transfers (UPI, NEFT, IMPS)
- EMI calculations
- Interest rates

Be helpful, direct, and provide specific banking information.
Give detailed answers in 3-4 sentences.""",
    },
    "financial": {
        "name": "Financial Advisor",
        "description": "Handles investments, mutual funds, stocks, tax planning",
        "keywords": ["invest", "mutual fund", "sip", "stock", "share", "portfolio", "tax", "nps", "ppf", "elss", "demat", "trading", "returns", "gold", "bond"],
        "prompt": """You are a Financial Advisor AI Agent. Your expertise:
- Mutual funds and SIP
- Stock market investments
- Tax-saving investments (ELSS, PPF, NPS)
- Portfolio management
- Retirement planning

Provide investment guidance and financial advice.
Give detailed answers in 3-4 sentences.""",
    },
    "insurance": {
        "name": "Insurance Specialist",
        "description": "Handles policy, claims, premium, coverage",
        "keywords": ["insurance", "policy", "claim", "premium", "coverage", "health", "life", "term", "endowment", "maturity", "nominee", "cashless", "hospital"],
        "prompt": """You are an Insurance Specialist AI Agent. Your expertise:
- Health insurance
- Life/Term insurance
- Motor insurance
- Policy management
- Claims processing
- Premium payments

Help with insurance queries and claims.
Give detailed answers in 3-4 sentences.""",
    },
    "support": {
        "name": "Customer Support",
        "description": "Handles general queries, complaints, tickets",
        "keywords": ["complaint", "ticket", "issue", "problem", "help", "support", "refund", "cancel", "password", "login", "error", "not working"],
        "prompt": """You are a Customer Support AI Agent. Your expertise:
- Ticket management
- Issue resolution
- Password/login help
- Complaint handling
- Refund processing

Be empathetic and solution-oriented.
Give detailed answers in 3-4 sentences.""",
    },
    "healthcare": {
        "name": "Healthcare Assistant",
        "description": "Handles appointments, medical records, prescriptions",
        "keywords": ["appointment", "doctor", "hospital", "medicine", "prescription", "lab", "test", "report", "vaccination", "checkup", "consultation"],
        "prompt": """You are a Healthcare Assistant AI Agent. Your expertise:
- Appointment scheduling
- Medical records
- Prescription refills
- Lab reports
- Doctor availability

Be caring and provide helpful healthcare guidance.
Give detailed answers in 3-4 sentences.""",
    }
}


# ==================== ROUTER AGENT ====================

def router_agent_classify(query: str, sector: str) -> str:
    """
    Router Agent: Classifies the user's query and determines the best specialist agent.
    Uses keyword matching first, then falls back to sector default.
    """
    query_lower = query.lower()
    
    logger.info("=" * 60)
    logger.info("🔀 ROUTER AGENT - Query Classification")
    logger.info(f"📝 Input Query: '{query}'")
    logger.info(f"📂 Current Sector: {sector}")
    
    # Score each agent based on keyword matches
    scores = {}
    matched_keywords = {}
    for agent_type, config in AGENT_TYPES.items():
        score = 0
        matches = []
        for keyword in config["keywords"]:
            if keyword in query_lower:
                score += 1
                matches.append(keyword)
                # Boost exact word matches
                if f" {keyword} " in f" {query_lower} ":
                    score += 0.5
        scores[agent_type] = score
        if matches:
            matched_keywords[agent_type] = matches
    
    # Log keyword matching results
    logger.info("🔍 Keyword Matching Scores:")
    for agent_type, score in scores.items():
        if score > 0:
            logger.info(f"   → {agent_type}: {score} (keywords: {matched_keywords.get(agent_type, [])})")
    
    # Find best matching agent
    best_agent = max(scores, key=scores.get)
    best_score = scores[best_agent]
    
    # If good keyword match found, use that agent
    if best_score >= 1:
        logger.info(f"✅ ROUTED TO: {AGENT_TYPES[best_agent]['name']} (score: {best_score})")
        logger.info("=" * 60)
        return best_agent
    
    # Map sector to default agent
    sector_to_agent = {
        "banking": "banking",
        "financial": "financial",
        "insurance": "insurance",
        "bpo": "support",
        "healthcare_appt": "healthcare",
        "healthcare_patient": "healthcare"
    }
    
    default_agent = sector_to_agent.get(sector, "banking")
    logger.info(f"⚡ No strong keyword match - using sector default")
    logger.info(f"✅ ROUTED TO: {AGENT_TYPES[default_agent]['name']} (sector: {sector})")
    logger.info("=" * 60)
    return default_agent


def get_specialist_prompt(agent_type: str) -> str:
    """Get the specialized prompt for the selected agent"""
    return AGENT_TYPES.get(agent_type, AGENT_TYPES["banking"])["prompt"]


def get_agent_name(agent_type: str) -> str:
    """Get the display name of the agent"""
    return AGENT_TYPES.get(agent_type, AGENT_TYPES["banking"])["name"]


# ==================== MULTI-AGENT RESPONSE GENERATOR ====================

def generate_multi_agent_response(
    query: str,
    context_docs: List[str],
    sector: str,
    conversation_history: List[Dict],
    language: str = "en",
    groq_client=None
) -> Tuple[str, bool, Optional[str]]:
    """
    Multi-Agent Response Generator:
    1. Router Agent classifies the query
    2. Specialist Agent generates the response
    """
    
    logger.info("=" * 60)
    logger.info("🤖 MULTI-AGENT SYSTEM - Response Generation")
    logger.info("=" * 60)
    
    if not groq_client:
        logger.error("❌ Groq client not provided")
        return "I'm having trouble connecting. Please try again.", False, None
    
    try:
        # Step 1: Router Agent classifies query
        logger.info("📌 STEP 1: Router Agent Classification")
        agent_type = router_agent_classify(query, sector)
        agent_name = get_agent_name(agent_type)
        specialist_prompt = get_specialist_prompt(agent_type)
        
        # Step 2: Build context from RAG
        logger.info("📌 STEP 2: Building RAG Context")
        context = ""
        if context_docs:
            context = "\n\nRelevant Information:\n" + "\n".join(context_docs[:3])
            logger.info(f"   📚 Using {len(context_docs)} RAG documents")
            for i, doc in enumerate(context_docs[:2]):
                logger.info(f"   📄 Doc {i+1}: {doc[:80]}...")
        else:
            logger.info("   📚 No RAG documents found")
        
        # Step 3: Build conversation history
        logger.info("📌 STEP 3: Building Conversation History")
        history_text = ""
        if conversation_history:
            recent = conversation_history[-6:]  # Last 6 turns
            logger.info(f"   💬 Using last {len(recent)} conversation turns")
            for turn in recent:
                role = "Customer" if turn.get("type") == "user" else "Agent"
                history_text += f"{role}: {turn.get('text', '')}\n"
        else:
            logger.info("   💬 No conversation history")
        
        # Step 4: Language instruction - STRICT language matching
        logger.info("📌 STEP 4: Setting Language Rules")
        if language == "en":
            lang_instruction = """
**CRITICAL - RESPOND IN ENGLISH ONLY**:
- The customer is speaking ENGLISH
- Your response MUST be 100% in ENGLISH
- Do NOT use ANY Hindi, Hinglish, or regional words
- Use simple, clear English sentences
- If you use even ONE Hindi word, you have FAILED
"""
        else:
            lang_instruction = """
**CRITICAL - RESPOND IN HINDI/HINGLISH**:
- The customer is speaking HINDI/HINGLISH  
- Your response MUST be in HINDI or HINGLISH
- Match the customer's language style
- Use Roman script for Hinglish (e.g., "Aapka balance hai...")
"""
        logger.info(f"   🌐 Language mode: {language}")
        
        # Step 5: Build the complete system prompt
        logger.info("📌 STEP 5: Building System Prompt")
        
        # Build context instruction - make it MANDATORY to use
        if context:
            context_instruction = f"""
IMPORTANT - USE THIS INFORMATION TO ANSWER:
{context}

YOU MUST:
- Base your answer ONLY on the information provided above
- Do NOT make up information that is not in the knowledge base
- If the answer is not in the provided information, say "I don't have that specific information"
"""
        else:
            context_instruction = """
NOTE: No specific knowledge base information was found for this query.
Provide a helpful general response based on your training.
"""
        
        system_prompt = f"""{specialist_prompt}

{lang_instruction}

{context_instruction}

RESPONSE FORMAT:
- Give accurate answers based on the knowledge base above
- Keep it SHORT (2-3 sentences for voice call)
- Be professional and clear
"""
        
        # Add conversation history if exists
        if history_text:
            system_prompt += f"\n\nConversation so far:\n{history_text}"
        
        logger.info(f"   📝 System prompt length: {len(system_prompt)} chars")
        
        # Step 6: Generate response using LLM
        logger.info("📌 STEP 6: Generating LLM Response")
        logger.info(f"   🧠 Model: llama-3.1-8b-instant")
        logger.info(f"   🎯 Agent: {agent_name}")
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]
        
        chat_completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            max_tokens=200,  # Increased for better response quality
            temperature=0.5,  # Lower for consistent language following
            top_p=0.9
        )
        
        response = chat_completion.choices[0].message.content.strip()
        
        # Check for human handoff triggers
        handoff_triggers = ["speak to human", "talk to agent", "real person", "supervisor", "manager", "operator"]
        needs_handoff = any(trigger in query.lower() for trigger in handoff_triggers)
        handoff_reason = "Customer requested human agent" if needs_handoff else None
        
        logger.info("=" * 60)
        logger.info(f"✅ RESPONSE GENERATED by {agent_name}")
        logger.info(f"📤 Response ({len(response)} chars): '{response}'")
        if needs_handoff:
            logger.info(f"🚨 HUMAN HANDOFF TRIGGERED: {handoff_reason}")
        logger.info("=" * 60)
        
        return response, needs_handoff, handoff_reason
        
    except Exception as e:
        logger.error(f"❌ Multi-agent response error: {e}")
        return "I'm sorry, I encountered an error. Please try again.", False, None


# ==================== GREETING GENERATOR ====================

def get_sector_greeting(sector: str) -> str:
    """Get a natural greeting for the sector"""
    greetings = {
        "banking": "Hello! Welcome to Banking Services. I'm your AI banking assistant. How can I help you with your banking needs today?",
        "financial": "Good day! Welcome to Financial Services. I'm your AI financial advisor. How can I assist with your investment or financial queries?",
        "insurance": "Hello! Welcome to Insurance Services. I'm your AI insurance assistant. How can I help with your policy or claims today?",
        "bpo": "Hello! Welcome to Customer Support. I'm your AI support agent. How can I assist you today?",
        "healthcare_appt": "Hello! Welcome to Healthcare Services. I'm your AI healthcare assistant. How can I help with appointments today?",
        "healthcare_patient": "Hello! Welcome to Patient Services. I'm your AI healthcare assistant. How can I help with your medical queries?"
    }
    return greetings.get(sector, "Hello! I'm your AI assistant. How can I help you today?")


# ==================== FAREWELL GENERATOR ====================

def get_farewell_response(sector: str) -> str:
    """Get a natural farewell for the sector"""
    farewells = {
        "banking": "Thank you for banking with us! Have a great day. Feel free to call again if you need any help.",
        "financial": "Thank you for consulting with us! Wishing you great returns on your investments. Take care!",
        "insurance": "Thank you for contacting Insurance Services! Stay protected and have a wonderful day.",
        "bpo": "Thank you for contacting support! We're here 24/7 if you need any further assistance.",
        "healthcare_appt": "Thank you for choosing our healthcare services! Take care of your health. Have a great day!",
        "healthcare_patient": "Thank you for using our patient services! Wishing you good health. Take care!"
    }
    return farewells.get(sector, "Thank you for calling! Have a great day!")
