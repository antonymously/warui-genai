'''
Models for chat messages and log
'''

class Message:
    content: str
    role: str

    def __init__(self, content: str, role: str):
        self.content = content
        self.role = role

    def __repr__(self):
        return "{role}: {content}".format(
            role = self.role,
            content = self.content
        )

class HumanMessage(Message):

    def __init__(
        self,
        content: str,
        role: str = "human"
    ):
        super().__init__(content, role)

class AIMessage(Message):

    def __init__(
        self,
        content: str,
        role: str = "ai"
    ):
        super().__init__(content, role)

class AILog:
    log_text: str

    def __init__(self, log_text: str):
        self.log_text = log_text

    def __repr__(self):
        return "AI Log: {}".format(self.log_text)

class PartialSummary:
    '''
    A summary of the conversation so far.
    Added to the start of the chat log.
    '''
    text: str

    def __init__(self, text: str):
        self.text = text

    def __repr__(self):
        return "Running Summary: {}".format(self.text)