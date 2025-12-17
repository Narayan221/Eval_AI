
import asyncio
import os
from typing import Dict, List
from groq import AsyncGroq
from app.core.config import settings

class ChatService:
    def __init__(self):
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self.session_title = ""
        self.session_description = ""
        self.conversation_history: List[Dict] = []
        self.session_active = False
        self.session_context = ""
        self.conversation_mode = "gitter"

    async def start_session(self, title: str, description: str) -> str:
        self.session_title = title
        self.session_description = description.strip() if description else ""
        self.session_active = True
        self.conversation_history = []
        self.conversation_mode = "gitter"

        # Check if description is provided
        has_description = bool(self.session_description)
        
        if has_description:
            # With description - focused session
            self.session_context = f"""You are Alex, an AI session leader. Your ONLY allowed topic is: {title}

Description: {description}

ABSOLUTE RULES:
- You can ONLY discuss {title} - nothing else
- NEVER discuss any other topic under any circumstances
- If asked about other topics, redirect to {title}
- You are FORBIDDEN from changing topics

Your sole purpose is discussing {title}. Give a brief welcome about {title}. NO formatting."""
        else:
            # Without description - focused conversation
            self.session_context = f"""You are Alex, an AI conversation partner. Your ONLY allowed topic is: {title}

ABSOLUTE RULES:
- You can ONLY discuss {title} - nothing else
- NEVER discuss any other topic under any circumstances  
- If asked about other topics, redirect to {title}
- You are FORBIDDEN from changing topics

Your sole purpose is discussing {title}. Introduce {title} and ask what aspects they'd like to explore. NO formatting."""

        response = await self.client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "system", "content": self.session_context}],
            max_tokens=80
        )

        ai_response = response.choices[0].message.content
        self.conversation_history.append({"role": "assistant", "content": ai_response})
        return ai_response

    def _classify_message(self, message: str) -> str:
        """Classify message to determine conversation mode"""
        bargain_keywords = [
            "decide", "choose", "negotiate", "price", "deal", "agree", "option", 
            "decision", "select", "pick", "conclude", "finalize", "settle"
        ]
        
        gitter_keywords = [
            "tell me", "explain", "what about", "how", "why", "interesting", 
            "think", "feel", "experience", "story", "example"
        ]
        
        message_lower = message.lower()
        
        bargain_score = sum(1 for keyword in bargain_keywords if keyword in message_lower)
        gitter_score = sum(1 for keyword in gitter_keywords if keyword in message_lower)
        
        if bargain_score > gitter_score:
            return "bargain"
        return "gitter"

    async def process_user_input(self, user_message: str) -> str:
        if not self.session_active:
            return "Please start a session first by providing a title and description."

        # Classify the conversation mode based on user input
        detected_mode = self._classify_message(user_message)
        
        # Switch modes if needed
        if detected_mode != self.conversation_mode:
            self.conversation_mode = detected_mode

        self.conversation_history.append({"role": "user", "content": user_message})

        # Build smart system prompt
        mode_context = self._get_mode_context()
        
        system_prompt = f"""{self.session_context}

{mode_context}

ABSOLUTE RULE: You can ONLY discuss {self.session_title}. NEVER discuss any other topic.

If user asks about anything else, respond: "I'm here to focus specifically on {self.session_title}. Let's explore that topic instead. What aspect of {self.session_title} interests you?"

You are FORBIDDEN from discussing any topic other than {self.session_title}. Always redirect to {self.session_title}.

Respond about {self.session_title} only. Keep it brief (2-3 sentences). NO formatting."""

        response = await self.client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                *self.conversation_history[-6:]  # Keep recent context
            ],
            max_tokens=80
        )

        ai_response = response.choices[0].message.content
        self.conversation_history.append({"role": "assistant", "content": ai_response})
        return ai_response

    def _get_mode_context(self) -> str:
        """Get context for current conversation mode"""
        if self.conversation_mode == "bargain":
            return "Be decisive and solution-oriented. Provide clear recommendations and help them make decisions."
        else:
            return "Be exploratory and engaging. Ask thoughtful questions and share interesting insights."
