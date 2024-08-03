from typing import Optional
from textwrap import dedent
from warui_genai.models.llm import BaseChatLLM
from warui_genai.models.chat import (
    HumanMessage,
    AIMessage,
    AILog,
    PartialSummary,
)
from warui_genai.models.llm import (
    CLAUDE_3_SONNET_CHAT,
    CLAUDE_3_5_SONNET_CHAT,
)

CHAT_LOG_LLM = CLAUDE_3_5_SONNET_CHAT

def chat_log_to_string(chat_log, **kwargs):
    '''
    Returns chat history as strings, including action logs from the copilot
    '''
    human_alias = kwargs.get("human_alias", "human")
    ai_alias = kwargs.get("ai_alias", "ai")
    
    log_string = ""
    
    for log in chat_log:
        if isinstance(log, HumanMessage):
            log_string += f"{human_alias}: {log.content.strip()}\n"
        elif isinstance(log, AIMessage):
            log_string += f"{ai_alias}: {log.content.strip()}\n"
        elif isinstance(log, AILog):
            log_string += f"{log.log_text}\n"
        elif isinstance(log, PartialSummary):
            log_string += f"Running Summary: {log.text}\n"
            
    return log_string.strip()

def trim_chat_log(
    chat_log: list,
    threshold: int = 30,
    trim_to: int = 15,
    llm: Optional[BaseChatLLM] = CHAT_LOG_LLM,
):
    '''
    If the chat log contains atleast <threshold> objects,
    It will be trimmed to the latest <trim_to - 1> objects and a partial summary will be added at the start.
    '''
    
    if len(chat_log) < threshold:
        return chat_log
    
    retained_log = chat_log[-(trim_to - 1):]
    summarized_log = chat_log[:-(trim_to - 1)]

    summarized_log_str = chat_log_to_string(
        summarized_log,
        human_alias = "HUMAN",
        ai_alias = "AI",
    )

    system_prompt = dedent('''
        A CHAT LOG will be provided between a HUMAN and an AI.
                           
        Provide a SUMMARY of the CHAT LOG. 
        Keep the SUMMARY within 4 sentences while retaining relevant details.
        
        Respond only with the SUMMARY.
        Do not add any explanation or extra text in your response.
    ''').strip()

    user_prompt = dedent('''
        CHAT LOG:
        {summarized_log_str}
    ''').strip().format(
        summarized_log_str = summarized_log_str,
    )

    res = llm.invoke(
        user_prompt,
        system_prompt = system_prompt,
    )

    partial_summary = PartialSummary(text = res)

    return [partial_summary] + retained_log