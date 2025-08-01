import logging
from collections import deque

# Initialize logger for chat_history.py
logger = logging.getLogger("chat_history")
logger.setLevel(logging.INFO)

class ChatHistory:
    def __init__(self, max_size=15):
        # Using deque to store up to `max_size` items
        self.history = deque(maxlen=max_size)
        logger.info("Chat history initialized with a maximum size of %d.", max_size)

    def get_sql_for_question(self, question):
        """Check if the question already exists in the history and return the SQL if found."""
        logger.info("Checking chat history for question: %s", question)
        for q, sql in self.history:
            logger.debug("Comparing with stored question: %s", q)
            if q.strip().lower() == question.strip().lower():  # Normalize for comparison
                logger.info("Found cached SQL for question: %s", question)
                return sql
        logger.info("No cached SQL found for question: %s", question)
        return None

    def add_question_answer(self, question, sql):
        """Add a new question and its corresponding SQL query to the history."""
        self.history.append((question, sql))
        logger.info("Added question to history: %s", question)