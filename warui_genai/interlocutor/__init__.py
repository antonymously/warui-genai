from abc import ABC, abstractmethod
from typing import Optional
from textwrap import dedent
import json

from .llm import (
    CLAUDE_3_HAIKU_CHAT,
    BaseChatLLM,
)

class BaseInterlocutor(ABC):

    def __init__(
        self,
        chat_llm: Optional[BaseChatLLM] = CLAUDE_3_HAIKU_CHAT,
    ):
        self.chat_llm = chat_llm
        self.system_prompt = ""

        self.clear_chat_log()

    def clear_chat_log(self):
        # NOTE: chat log does not include system prompt
        self.chat_log = []

    @abstractmethod
    def invoke(
        self,
        message: str = "",
    ):
        pass

class AdaptiveInterlocutor(BaseInterlocutor):
    '''
    This interlocutor adapts to the level and proficiencies of the user
    based on his Renshuu profile.
    '''
    
    def __init__(
        self,
        chat_llm: Optional[BaseChatLLM] = CLAUDE_3_HAIKU_CHAT,
        level: Optional[str] = "n5",
        focus_terms: Optional[list] = [],
    ):
        super().__init__(chat_llm = chat_llm)

        self.level = level
        self.focus_terms = focus_terms

        self.system_prompt = dedent('''
            You are a conversation partner for a Japanese learner STUDENT.
            ALWAYS respond only in Japanese, regardless of what language the STUDENT uses.

            The student is currently at the {level} level.
            Use grammar, vocabulary and kanji appropriate to this level.

            Be engaging in conversation.
            Encourate the STUDENT to go into different topics.
            Ask questions to keep the conversation going when necessary.
        ''').format(
            level = self.level,
        )

        if len(focus_terms) > 0:
            self.system_prompt += dedent('''
                \n\nFurthermore, specific STUDY TERMS will be provided in a json-list format.
                These are either vocabulary, grammar or kanji STUDY TERMS.
                These have been identified as focus points for the STUDENT's learning.
                Attempt to use these study points as you converse with the STUDENT, to improve his recall of these.

                STUDY TERMS:
                {focus_terms}
            ''').format(
                focus_terms = json.dumps(self.focus_terms, indent = 4),
            )

    def invoke(
        self,
        message: str = "",
    ):
        # TODO
        pass


    