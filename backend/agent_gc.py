import os
import langchain
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.tools import tool
from langchain.messages import HumanMessage
from dotenv import load_dotenv

load_dotenv()

async def agentfactory():
    model = init_chat_model("dashscope:qwen-plus", api_key=os.getenv("ALIYUN_ACCESS_KEY_SECRET"))
    agent = create_agent(
        model=model,
        system_prompt="你是一个乐于助人的助手，会使用工具来回答问题。",
    )
    return agent

