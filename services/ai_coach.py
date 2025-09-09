"""
AI Coach Service - Integrates with Gemini and DeepSeek LLMs.
Provides context-aware, personality-driven responses.
"""
import os
import json
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import google.generativeai as genai
import openai
from flask import current_app
from models import db, User, Goal, Task, Habit, JournalEntry, ChatHistory


class RateLimiter:
    """Simple in-memory rate limiter for API calls."""
    
    def __init__(self, max_requests: int = 10, window_minutes: int = 1):
        self.max_requests = max_requests
        self.window_minutes = window_minutes
        self.requests = {}
    
    def is_allowed(self, user_id: int) -> bool:
        """Check if user has exceeded rate limit."""
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=self.window_minutes)
        
        # Clean old requests
        if user_id in self.requests:
            self.requests[user_id] = [
                req_time for req_time in self.requests[user_id]
                if req_time > window_start
            ]
        
        # Check limit
        if user_id not in self.requests:
            self.requests[user_id] = []
        
        if len(self.requests[user_id]) >= self.max_requests:
            return False
        
        # Record new request
        self.requests[user_id].append(now)
        return True


class AICoach:
    """Main AI Coach class handling LLM interactions."""
    
    # Personality prompts for different avatar types
    PERSONALITY_PROMPTS = {
        'sage': """You are the Sage, a wise and philosophical AI life coach. You speak with depth and 
                   wisdom, often using metaphors and asking profound questions that help users reflect 
                   deeply on their life journey. Your tone is calm, thoughtful, and enlightening.
                   Start with brief responses (2-4 sentences), but expand naturally when the conversation deepens.""",
        
        'champion': """You are the Champion, an enthusiastic and energetic AI life coach! You're like a 
                       personal cheerleader, celebrating every win (no matter how small) and providing 
                       high-energy motivation. Use encouraging language and excitement!
                       Start with energetic, punchy responses but expand when celebrating achievements or planning next steps.""",
        
        'friend': """You are the Friend, a warm and empathetic AI life coach. You speak like a caring, 
                     supportive friend who truly understands. Your tone is casual, kind, and 
                     non-judgmental. You listen well and provide gentle guidance.
                     Respond naturally and conversationally, adjusting length based on what the user needs to hear.""",
        
        'strategist': """You are the Strategist, an analytical and practical AI life coach. You focus on 
                         data, patterns, and actionable strategies. Your responses are clear, structured, 
                         and results-oriented. You help users optimize their approach to goals.
                         Start concise but provide detailed frameworks and action plans when strategy is discussed.""",
        
        'zen_master': """You are the Zen Master, a calm and mindful AI life coach. You emphasize presence, 
                         acceptance, and inner peace. Your responses are serene, focusing on mindfulness, 
                         breathing, and finding balance in the present moment.
                         Begin with mindful brevity but expand with guided practices when deeper reflection is needed."""
    }
    
    def __init__(self):
        """Initialize the AI Coach with configured LLM provider."""
        self.provider = current_app.config.get('LLM_PROVIDER', 'gemini')
        self.max_tokens = current_app.config.get('LLM_MAX_TOKENS', 2048)
        self.temperature = current_app.config.get('LLM_TEMPERATURE', 0.7)
        self.rate_limiter = RateLimiter(
            max_requests=current_app.config.get('LLM_RATE_LIMIT', 10)
        )
        
        # Initialize the appropriate LLM client
        if self.provider == 'gemini':
            self._init_gemini()
        elif self.provider == 'deepseek':
            self._init_deepseek()
        elif self.provider == 'moonshot':
            self._init_moonshot()
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
    
    def _init_gemini(self):
        """Initialize Google Gemini API."""
        api_key = current_app.config.get('GEMINI_API_KEY')
        if not api_key or api_key == 'your_gemini_api_key_here':
            raise ValueError("GEMINI_API_KEY not configured in .env file")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
    
    def _init_deepseek(self):
        """Initialize DeepSeek API (using OpenAI client)."""
        api_key = current_app.config.get('DEEPSEEK_API_KEY')
        if not api_key or api_key == 'your_deepseek_api_key_here':
            raise ValueError("DEEPSEEK_API_KEY not configured in .env file")
        
        try:
            # DeepSeek uses OpenAI-compatible API
            self.client = openai.OpenAI(
                api_key=api_key,
                base_url="https://api.deepseek.com/v1"
            )
        except Exception as e:
            current_app.logger.error(f"Failed to initialize DeepSeek client: {str(e)}")
            raise ValueError(f"DeepSeek API initialization failed: {str(e)}")
    
    def _init_moonshot(self):
        """Initialize Moonshot (Kimi) API (using OpenAI client)."""
        api_key = current_app.config.get('MOONSHOT_API_KEY')
        if not api_key or api_key == 'your_moonshot_api_key_here':
            raise ValueError("MOONSHOT_API_KEY not configured in .env file")
        
        try:
            # Moonshot uses OpenAI-compatible API
            self.client = openai.OpenAI(
                api_key=api_key,
                base_url="https://api.moonshot.ai/v1"
            )
        except Exception as e:
            current_app.logger.error(f"Failed to initialize Moonshot client: {str(e)}")
            raise ValueError(f"Moonshot API initialization failed: {str(e)}")
    
    def build_user_context(self, user_id: int, days_back: int = 7) -> str:
        """Build context string from user's recent activity."""
        context_parts = []
        
        # Get user
        user = User.query.get(user_id)
        if not user:
            return ""
        
        # Recent goals
        active_goals = Goal.query.filter_by(
            user_id=user_id,
            status='active'
        ).limit(5).all()
        
        if active_goals:
            goals_text = "User's active goals:\n"
            for goal in active_goals:
                progress = goal.calculate_progress()
                goals_text += f"- {goal.title} ({progress}% complete)\n"
            context_parts.append(goals_text)
        
        # Recent tasks
        recent_date = datetime.utcnow() - timedelta(days=days_back)
        recent_tasks = Task.query.filter(
            Task.user_id == user_id,
            Task.created_at >= recent_date
        ).order_by(Task.created_at.desc()).limit(10).all()
        
        if recent_tasks:
            completed = len([t for t in recent_tasks if t.completed])
            tasks_text = f"\nRecent tasks: {completed}/{len(recent_tasks)} completed\n"
            context_parts.append(tasks_text)
        
        # Active habits and streaks
        habits = Habit.query.filter_by(
            user_id=user_id,
            active=True
        ).all()
        
        if habits:
            habits_text = "Active habits:\n"
            for habit in habits:
                habits_text += f"- {habit.name} (streak: {habit.streak_count} days)\n"
            context_parts.append(habits_text)
        
        # Recent journal entries (mood trends)
        recent_journals = JournalEntry.query.filter(
            JournalEntry.user_id == user_id,
            JournalEntry.created_at >= recent_date
        ).order_by(JournalEntry.created_at.desc()).limit(5).all()
        
        if recent_journals:
            moods = [j.mood_score for j in recent_journals if j.mood_score]
            if moods:
                avg_mood = sum(moods) / len(moods)
                mood_trend = "improving" if moods[0] > moods[-1] else "declining" if moods[0] < moods[-1] else "stable"
                context_parts.append(f"\nRecent mood: {avg_mood:.1f}/10 ({mood_trend})")
        
        return "\n".join(context_parts)
    
    def get_personality_prompt(self, user_id: int) -> str:
        """Get the personality-specific system prompt for the user."""
        user = User.query.get(user_id)
        personality = user.avatar_personality if user else 'friend'
        
        base_prompt = self.PERSONALITY_PROMPTS.get(personality, self.PERSONALITY_PROMPTS['friend'])
        
        return f"""{base_prompt}
        
        You are helping a user with their personal development journey. Be supportive and constructive.
        Keep responses concise but meaningful. Focus on actionable advice when appropriate.
        Remember you're part of the Elara life coaching app."""
    
    def generate_response(
        self,
        user_id: int,
        message: str,
        include_context: bool = True
    ) -> Tuple[str, int]:
        """
        Generate AI response to user message.
        Returns: (response_text, tokens_used)
        """
        # Check rate limit
        if not self.rate_limiter.is_allowed(user_id):
            return "I need a moment to rest. Please try again in a minute! 🌟", 0
        
        # Build full prompt
        system_prompt = self.get_personality_prompt(user_id)
        
        if include_context:
            user_context = self.build_user_context(user_id)
            if user_context:
                system_prompt += f"\n\nContext about the user:\n{user_context}"
        
        try:
            if self.provider == 'gemini':
                return self._generate_gemini_response(system_prompt, message)
            elif self.provider == 'deepseek':
                return self._generate_deepseek_response(system_prompt, message)
            elif self.provider == 'moonshot':
                return self._generate_moonshot_response(system_prompt, message)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
        except Exception as e:
            current_app.logger.error(f"LLM generation error: {str(e)}")
            return "I'm having trouble connecting right now. Please try again in a moment.", 0
    
    def _generate_gemini_response(self, system_prompt: str, message: str) -> Tuple[str, int]:
        """Generate response using Gemini API."""
        # Combine system prompt and user message
        full_prompt = f"{system_prompt}\n\nUser: {message}\n\nAssistant:"
        
        # Generate response
        response = self.model.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=self.max_tokens,
                temperature=self.temperature,
            )
        )
        
        # Estimate tokens (Gemini doesn't provide exact count in response)
        tokens_estimate = len(full_prompt.split()) + len(response.text.split())
        
        return response.text, tokens_estimate
    
    def _generate_deepseek_response(self, system_prompt: str, message: str) -> Tuple[str, int]:
        """Generate response using DeepSeek API."""
        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            max_tokens=self.max_tokens,
            temperature=self.temperature
        )
        
        response_text = response.choices[0].message.content
        tokens_used = response.usage.total_tokens if response.usage else 0
        
        return response_text, tokens_used
    
    def _generate_moonshot_response(self, system_prompt: str, message: str) -> Tuple[str, int]:
        """Generate response using Moonshot (Kimi) API."""
        response = self.client.chat.completions.create(
            model="kimi-k2-0905-preview",  # Use the latest Kimi model
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            max_tokens=self.max_tokens,
            temperature=self.temperature
        )
        
        response_text = response.choices[0].message.content
        tokens_used = response.usage.total_tokens if response.usage else 0
        
        return response_text, tokens_used
    
    def save_conversation(
        self,
        user_id: int,
        user_message: str,
        ai_response: str,
        tokens_used: int = 0
    ):
        """Save conversation to database."""
        user = User.query.get(user_id)
        personality = user.avatar_personality if user else 'friend'
        
        # Save user message
        user_msg = ChatHistory(
            user_id=user_id,
            role='user',
            content=user_message,
            personality_used=personality
        )
        db.session.add(user_msg)
        
        # Save AI response
        ai_msg = ChatHistory(
            user_id=user_id,
            role='assistant',
            content=ai_response,
            personality_used=personality,
            tokens_used=tokens_used
        )
        db.session.add(ai_msg)
        
        db.session.commit()
    
    def get_conversation_history(
        self,
        user_id: int,
        limit: int = 20
    ) -> List[Dict]:
        """Get recent conversation history."""
        messages = ChatHistory.query.filter_by(
            user_id=user_id
        ).order_by(ChatHistory.timestamp.desc()).limit(limit).all()
        
        # Reverse to get chronological order
        messages.reverse()
        
        return [msg.to_dict() for msg in messages]
    
    def generate_weekly_review_summary(
        self,
        user_id: int,
        review_data: Dict
    ) -> str:
        """Generate AI summary for weekly review."""
        prompt = f"""Based on this weekly review data, provide a thoughtful summary and 
        recommendations for the user:
        
        Goals worked on: {review_data.get('goals_reflection', 'Not specified')}
        Wins celebrated: {review_data.get('wins_celebration', 'Not specified')}
        Challenges faced: {review_data.get('challenges_faced', 'Not specified')}
        Lessons learned: {review_data.get('lessons_learned', 'Not specified')}
        Next week focus: {review_data.get('next_week_focus', 'Not specified')}
        
        Task completion rate: {review_data.get('task_completion_rate', 0)}%
        Average mood: {review_data.get('mood_average', 0)}/10
        
        Provide:
        1. A brief celebration of their achievements
        2. Acknowledgment of challenges with empathy
        3. 2-3 specific, actionable recommendations for next week
        4. An encouraging closing thought
        """
        
        response, _ = self.generate_response(user_id, prompt, include_context=True)
        return response
    
    def guide_values_discovery(self, user_id: int, context: dict) -> str:
        """Provide AI guidance for values discovery process."""
        selected_values = context.get('selected_values', [])
        current_phase = context.get('phase', 'selection')
        
        if current_phase == 'selection':
            prompt = f"""I'm helping a user discover their core values. They've selected these values so far: {', '.join(selected_values) if selected_values else 'none yet'}.

            Provide encouraging, insightful guidance to help them:
            1. Reflect on whether these values truly resonate with their authentic self
            2. Consider any important values they might be missing
            3. Think about what these values mean to them personally
            
            Keep it supportive and thought-provoking. Ask 1-2 gentle questions to help them go deeper."""
            
        elif current_phase == 'ranking':
            prompt = f"""The user is now ranking their top values: {', '.join(selected_values)}. 

            Help them think about:
            1. Which values are truly non-negotiable vs. nice-to-have
            2. How these values have shown up in their peak moments
            3. Which values, if honored, would make them feel most authentic
            
            Provide guidance for making these tough ranking decisions."""
            
        else:  # reflection phase
            top_values = context.get('top_values', selected_values[:5])
            prompt = f"""The user has identified their top core values: {', '.join(top_values)}.

            Help them reflect on:
            1. What makes each value personally meaningful to them
            2. How these values connect to their life experiences
            3. How they can honor these values more in daily life
            
            Be encouraging about their self-discovery journey."""
        
        response, _ = self.generate_response(user_id, prompt, include_context=False)
        return response
    
    def guide_vision_creation(self, user_id: int, context: dict) -> str:
        """Provide AI guidance for vision statement creation."""
        current_vision = context.get('current_vision', '')
        current_mission = context.get('current_mission', '')
        values_assessment = self._get_user_values(user_id)
        
        values_context = ""
        if values_assessment:
            top_values = values_assessment.get_top_value_names()[:5]
            values_context = f"Their core values are: {', '.join(top_values)}."
        
        prompt = f"""I'm helping a user create their life vision statement. {values_context}

        Current vision draft: "{current_vision}"
        Current mission draft: "{current_mission}"
        
        Provide personalized guidance to help them:
        1. Make their vision more vivid and emotionally compelling
        2. Ensure it aligns with their core values
        3. Make it feel inspiring and authentic to who they are
        4. Add specific details that make it feel real and achievable
        
        Offer 2-3 specific suggestions and ask a thought-provoking question to help them go deeper."""
        
        response, _ = self.generate_response(user_id, prompt, include_context=True)
        return response
    
    def provide_discovery_reflection(self, user_id: int, context: dict) -> str:
        """Provide reflection on completed discovery process."""
        values_assessment = self._get_user_values(user_id)
        vision_statement = self._get_user_vision(user_id)
        
        if not values_assessment or not vision_statement:
            return "Please complete both your values assessment and vision statement first."
        
        top_values = values_assessment.get_top_value_names()[:5]
        vision_text = vision_statement.vision_statement[:200] + "..." if len(vision_statement.vision_statement) > 200 else vision_statement.vision_statement
        
        prompt = f"""The user has completed their discovery process:
        
        Core Values: {', '.join(top_values)}
        Vision: "{vision_text}"
        
        Provide a thoughtful reflection that:
        1. Celebrates their self-discovery journey
        2. Highlights connections between their values and vision
        3. Offers insights about what this reveals about them
        4. Suggests next steps for living more aligned with their discovery
        
        Be warm, encouraging, and insightful. Help them see the power of what they've discovered."""
        
        response, _ = self.generate_response(user_id, prompt, include_context=True)
        return response
    
    def suggest_task_goal_connections(self, user_id: int) -> str:
        """Suggest how orphaned tasks could connect to goals or values."""
        orphaned_tasks = self._get_orphaned_tasks(user_id)
        values_assessment = self._get_user_values(user_id)
        active_goals = self._get_active_goals(user_id)
        
        if not orphaned_tasks:
            return "Great job! All your tasks are connected to your goals."
        
        task_titles = [task.title for task in orphaned_tasks[:10]]  # Limit to 10 tasks
        values_context = ""
        goals_context = ""
        
        if values_assessment:
            top_values = values_assessment.get_top_value_names()[:5]
            values_context = f"Their core values: {', '.join(top_values)}."
        
        if active_goals:
            goal_titles = [goal.title for goal in active_goals[:5]]
            goals_context = f"Their active goals: {', '.join(goal_titles)}."
        
        prompt = f"""The user has these unconnected tasks: {', '.join(task_titles)}
        
        {values_context}
        {goals_context}
        
        Analyze these tasks and provide specific suggestions for:
        1. Which tasks naturally group together and could become a new goal
        2. Which tasks support existing goals and should be connected
        3. Which tasks align with their values and why that matters
        4. Any tasks that might not serve their bigger picture
        
        Be specific and actionable in your recommendations."""
        
        response, _ = self.generate_response(user_id, prompt, include_context=False)
        return response
    
    def _get_user_values(self, user_id: int):
        """Helper to get user's current values assessment."""
        from models import CoreValueAssessment
        return CoreValueAssessment.query.filter_by(user_id=user_id, is_current=True).first()
    
    def _get_user_vision(self, user_id: int):
        """Helper to get user's current vision statement."""
        from models import VisionStatement
        return VisionStatement.query.filter_by(user_id=user_id, is_current=True).first()
    
    def _get_orphaned_tasks(self, user_id: int):
        """Helper to get tasks not connected to goals."""
        from models import Task
        return Task.query.filter_by(user_id=user_id, goal_id=None, completed=False).limit(10).all()
    
    def _get_active_goals(self, user_id: int):
        """Helper to get user's active goals."""
        from models import Goal
        return Goal.query.filter_by(user_id=user_id, status='active').limit(10).all()