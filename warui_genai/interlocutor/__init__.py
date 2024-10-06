from abc import ABC, abstractmethod
from typing import Optional
from textwrap import dedent
import json

from ..models.llm import (
    CLAUDE_3_HAIKU_CHAT,
    BaseChatLLM,
)
from ..utils.chat_log import (
    trim_chat_log,
    chat_log_to_history,
)
from ..models.chat import (
    HumanMessage,
    AIMessage,
    PartialSummary,
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
        chat_log_threshold: Optional[int] = 20,
        chat_log_trim_to: Optional[int] = 10,
    ):
        super().__init__(chat_llm = chat_llm)

        self.level = level
        self.focus_terms = focus_terms
        self.chat_log_threshold = chat_log_threshold
        self.chat_log_trim_to = chat_log_trim_to

        self.system_prompt = dedent('''
            You are a conversation partner for a Japanese learner STUDENT.
            ALWAYS respond only in Japanese, regardless of what language the STUDENT uses.
            If the STUDENT responds in a different language, encourage him to respond in Japanese.

            The student is currently at the {level} level.
            Use grammar, vocabulary and kanji appropriate to this level.

            Be engaging in conversation.
            Encourate the STUDENT to go into different topics.
            Ask questions to keep the conversation going when necessary.
        ''').format(
            level = self.level.upper(),
        )

        if len(focus_terms) > 0:
            self.system_prompt += dedent('''
                Furthermore, specific STUDY TERMS will be provided in a json-list format.
                These are either vocabulary, grammar or kanji STUDY TERMS.
                These have been identified as focus points for the STUDENT's learning.
                Attempt to use these study points as you converse with the STUDENT, to improve his recall of these.

                STUDY TERMS:
                {focus_terms}
            ''').format(
                focus_terms = json.dumps(self.focus_terms, indent = 4, ensure_ascii=False),
            )

    def invoke(
        self,
        message: str = "",
    ):

        # NOTE: trim chat_log if necessary
        self.chat_log = trim_chat_log(
            self.chat_log,
            threshold = self.chat_log_threshold,
            trim_to = self.chat_log_trim_to,
        )

        # NOTE: if self.chat_log includes a running_summary
            # include it as part of the system prompt
        if len(self.chat_log) == 0:
            system_prompt_ = self.system_prompt
            chat_log_ = self.chat_log
        elif isinstance(self.chat_log[0], PartialSummary):
            partial_summary = self.chat_log[0].text

            system_prompt_ = self.system_prompt + dedent('''
            Additionally, the following is a summary of the conversation so far:
            "{partial_summary}"
            ''').format(
                partial_summary = partial_summary,
            )

            chat_log_ = self.chat_log[1:]
        else:
            system_prompt_ = self.system_prompt
            chat_log_ = self.chat_log

        # NOTE: the first message must be user
            # if it is not, just insert a placeholder message
        if len(chat_log_) > 0:
            if not isinstance(chat_log_[0], HumanMessage):
                chat_log_ = [HumanMessage(content = "...")] + chat_log_

        # NOTE: transform the chat log into the appropriate chat_history
        chat_history = chat_log_to_history(chat_log_)

        response = self.chat_llm.invoke(
            message,
            system_prompt = system_prompt_,
            history = chat_history,
        )

        # NOTE: add to chat_log
        self.chat_log.append(
            HumanMessage(content = message)
        )
        self.chat_log.append(
            AIMessage(content = response)
        )

        return response