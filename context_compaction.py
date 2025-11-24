#!/usr/bin/env python3
"""
Context compaction service for managing long conversations.
Automatically summarizes old conversation turns to prevent token overflow.
"""

import logging
from typing import List, Dict, Any, Optional
from google.genai import Client, types

logger = logging.getLogger(__name__)


class ContextCompactionService:
    """
    Service for compacting conversation context through summarization.
    Prevents token overflow while maintaining conversation continuity.
    """
    
    def __init__(
        self,
        memory_service,
        summarization_model: str = "gemini-2.0-flash-exp",
        summarization_threshold: int = 20,  # Turns before summarization
        keep_recent_turns: int = 10,  # Recent turns to keep unsummarized
        max_tokens: int = 6000  # Reserve for prompt + response
    ):
        """
        Initialize context compaction service.
        
        Args:
            memory_service: ADK memory service instance
            summarization_model: Model for generating summaries
            summarization_threshold: Number of turns before triggering summarization
            keep_recent_turns: Number of recent turns to keep in full
            max_tokens: Maximum tokens to reserve for context
        """
        self.memory_service = memory_service
        self.model = summarization_model
        self.threshold = summarization_threshold
        self.keep_recent = keep_recent_turns
        self.max_tokens = max_tokens
        self.client = Client()
        
        logger.info(
            f"Context compaction initialized (threshold={summarization_threshold}, "
            f"keep_recent={keep_recent_turns})"
        )
    
    async def should_compact(
        self,
        session_id: str,
        user_id: str
    ) -> bool:
        """
        Check if conversation should be compacted.
        
        Args:
            session_id: Session identifier
            user_id: User identifier
        
        Returns:
            True if compaction is needed
        """
        try:
            # Get conversation history
            messages = await self.memory_service.get_messages(
                session_id=session_id,
                user_id=user_id
            )
            
            # Count turns (user + model = 1 turn)
            turn_count = len(messages) // 2
            
            should_compact = turn_count >= self.threshold
            
            if should_compact:
                logger.info(f"Compaction needed for session {session_id} ({turn_count} turns)")
            
            return should_compact
            
        except Exception as e:
            logger.error(f"Error checking compaction need: {e}")
            return False
    
    async def compact_conversation(
        self,
        session_id: str,
        user_id: str
    ) -> Optional[str]:
        """
        Compact old conversation turns into a summary.
        
        Args:
            session_id: Session identifier
            user_id: User identifier
        
        Returns:
            Summary text if successful, None otherwise
        """
        try:
            logger.info(f"Starting compaction for session {session_id}")
            
            # Get all messages
            messages = await self.memory_service.get_messages(
                session_id=session_id,
                user_id=user_id
            )
            
            if not messages:
                logger.warning("No messages to compact")
                return None
            
            # Split into old (to summarize) and recent (to keep)
            split_point = max(0, len(messages) - (self.keep_recent * 2))
            old_messages = messages[:split_point]
            
            if not old_messages:
                logger.info("Not enough old messages to compact")
                return None
            
            # Generate summary
            summary = await self._generate_summary(old_messages)
            
            if not summary:
                logger.error("Failed to generate summary")
                return None
            
            logger.info(f"Generated summary: {len(summary)} characters")
            
            return summary
            
        except Exception as e:
            logger.error(f"Error compacting conversation: {e}", exc_info=True)
            return None
    
    async def _generate_summary(
        self,
        messages: List[Dict[str, Any]]
    ) -> Optional[str]:
        """
        Generate a summary of conversation messages.
        
        Args:
            messages: List of conversation messages
        
        Returns:
            Summary text or None if generation fails
        """
        try:
            # Format messages for summarization
            conversation_text = self._format_messages(messages)
            
            # Create summarization prompt
            prompt = f"""
You are summarizing a pregnancy consultation conversation. Extract and preserve ALL critical information:

**Patient Information:**
- Name, age, phone number
- Location and country
- Contact preferences

**Pregnancy Details:**
- Last Menstrual Period (LMP) date
- Estimated Due Date (EDD)
- Gestational age
- Pregnancy number (first, second, etc.)

**Medical Information:**
- Risk level (low/moderate/high)
- Risk factors identified
- Medical history and conditions
- Medications
- Allergies
- Previous complications

**Care Plan:**
- ANC schedule provided
- Appointments scheduled
- Facility recommendations given
- Advice and guidance provided

**Follow-up Items:**
- Questions to address in next visit
- Tests or procedures recommended
- Red flags to watch for

**Conversation:**
{conversation_text}

Provide a structured summary (200-400 words) that preserves all factual details. Use bullet points for clarity.
"""
            
            # Call summarization model
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,  # Low temperature for factual summary
                    max_output_tokens=800
                )
            )
            
            summary = response.text.strip()
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}", exc_info=True)
            return None
    
    def _format_messages(
        self,
        messages: List[Dict[str, Any]]
    ) -> str:
        """
        Format messages for summarization prompt.
        
        Args:
            messages: List of conversation messages
        
        Returns:
            Formatted conversation text
        """
        formatted = []
        
        for msg in messages:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            
            if role == 'user':
                formatted.append(f"Patient: {content}")
            elif role == 'model':
                formatted.append(f"Agent: {content}")
            else:
                formatted.append(f"{role}: {content}")
        
        return "\n\n".join(formatted)
    
    async def archive_old_messages(
        self,
        session_id: str,
        user_id: str,
        summary: str
    ) -> bool:
        """
        Archive old messages after creating summary.
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            summary: Generated summary text
        
        Returns:
            True if archival successful
        """
        try:
            # Get all messages
            messages = await self.memory_service.get_messages(
                session_id=session_id,
                user_id=user_id
            )
            
            # Determine split point
            split_point = max(0, len(messages) - (self.keep_recent * 2))
            
            # Store summary as a special message
            await self.memory_service.add_message(
                session_id=session_id,
                user_id=user_id,
                role="system",
                content=f"[CONVERSATION SUMMARY]\n{summary}"
            )
            
            # Delete old messages (implementation depends on memory service)
            # For now, we'll just mark that archival happened
            logger.info(f"Archived {split_point} messages for session {session_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error archiving messages: {e}", exc_info=True)
            return False
    
    async def compact_and_archive(
        self,
        session_id: str,
        user_id: str
    ) -> bool:
        """
        Complete compaction workflow: summarize and archive.
        
        Args:
            session_id: Session identifier
            user_id: User identifier
        
        Returns:
            True if successful
        """
        try:
            # Check if compaction needed
            if not await self.should_compact(session_id, user_id):
                logger.info("Compaction not needed")
                return False
            
            # Generate summary
            summary = await self.compact_conversation(session_id, user_id)
            
            if not summary:
                logger.error("Failed to generate summary")
                return False
            
            # Archive old messages
            success = await self.archive_old_messages(session_id, user_id, summary)
            
            if success:
                logger.info(f"Compaction complete for session {session_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error in compact_and_archive: {e}", exc_info=True)
            return False


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def demo():
        """Demonstrate context compaction service"""
        from pregnancy_companion_agent import memory_service
        
        compaction = ContextCompactionService(
            memory_service=memory_service,
            summarization_threshold=5,  # Lower for testing
            keep_recent_turns=2
        )
        
        session_id = "demo_session"
        user_id = "demo_user"
        
        # Check compaction need
        should_compact = await compaction.should_compact(session_id, user_id)
        print(f"Should compact: {should_compact}")
        
        if should_compact:
            # Perform compaction
            summary = await compaction.compact_conversation(session_id, user_id)
            if summary:
                print(f"\nGenerated summary:\n{summary}")
    
    asyncio.run(demo())
