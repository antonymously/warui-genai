'''
Models for interacting with LLMs
'''

import os
import json
from abc import ABC, abstractmethod
from dotenv import load_dotenv
import anthropic

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_CLIENT = anthropic.Anthropic(api_key = ANTHROPIC_API_KEY)

class BaseChatLLM(ABC):

    @abstractmethod
    def invoke(
        self, 
        message, 
        system_prompt = "", 
        history = None, 
        role = None
    ):
        pass

class ClaudeChat(BaseChatLLM):

    def __init__(
        self, 
        model = "claude-3-5-sonnet-20240620",
        max_tokens = 4096,
        temperature = 0.0,
    ):
        super().__init__()

        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

    def invoke(
        self, 
        message, 
        system_prompt = "You are a helpful assistant.", 
        history = [], 
        role = "user",
    ):

        response = ANTHROPIC_CLIENT.messages.create(
            model = self.model,
            max_tokens = self.max_tokens,
            system = system_prompt,
            temperature = self.temperature,
            messages = history + [
                {"role": role, "content": message},
            ],
        )

        return response.content[0].text

CLAUDE_3_5_SONNET_CHAT = ClaudeChat(model = "claude-3-5-sonnet-20240620")
CLAUDE_3_SONNET_CHAT = ClaudeChat(model = "claude-3-sonnet-20240229")
CLAUDE_3_HAIKU_CHAT = ClaudeChat(model = "claude-3-haiku-20240307")