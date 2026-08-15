from langchain.agents import create_agent
from langchain.agents.middleware.types import after_agent, before_agent
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain.tools import tool
from langchain.messages import HumanMessage, AIMessage
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from pydantic import BaseModel
from langchain.agents.structured_output import ToolStrategy
from langgraph.memory import InMemorySaver

import os
import time
import sys
import io

# Windows 终端 GBK 编码兼容
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

load_dotenv()
model = ChatTongyi(
    model="deepseek-v4-flash",
    dashscope_api_key=os.getenv("ALIYUN_ACCESS_KEY_SECRET"),
    temperature=0.7,
)
model2 = init_chat_model(
    "deepseek:deepseek-v4-flash", api_key=os.getenv("DEEPSEEK_API_KEY")
)


def dingdan_table() -> dict:
    """查询所有订单的详细信息。"""
    dingdan_info = {
        "dingdan_id_01": {
            "客户ID": "123456",
            "商品名称": "商品A",
            "数量": 2,
            "单价": 100,
            "总金额": 200,
            "订单状态": "已支付",
            "支付时间": "2023-08-01 10:00:00",
        },
        "dingdan_id_02": {
            "客户ID": "123456",
            "商品名称": "商品A",
            "数量": 2,
            "单价": 100,
            "总金额": 200,
            "订单状态": "已支付",
            "支付时间": "2023-08-01 10:00:00",
        },
        "dingdan_id_03": {
            "客户ID": "123456",
            "商品名称": "商品A",
            "数量": 2,
            "单价": 100,
            "总金额": 200,
            "订单状态": "已支付",
            "支付时间": "2023-08-01 10:00:00",
        },
    }
    return dingdan_info


@tool
def dingdan_get(dingdan_id: str) -> str:
    """查询指定订单的详细信息。

    Args:
        dingdan_id: 订单ID
    """
    dingdan_info = dingdan_table()
    return (
        f"订单 {dingdan_id} 的详细信息为：{dingdan_info[dingdan_id]}"
        if dingdan_id in dingdan_info
        else "未找到该订单"
    )


@tool
def tuihuo(dingdan_id: str, why: str) -> str:
    """取消指定订单。

    Args:
        dingdan_id: 订单ID
        why: 取消原因
    """
    dingdan_info = dingdan_table()
    if dingdan_id not in dingdan_info.keys():
        return f"订单 {dingdan_id} 不存在"
    if dingdan_info[dingdan_id]["订单状态"] == "已取消":
        return f"订单 {dingdan_id} 已取消，无需重复操作"
    why_dict = {"客户取消": "客户取消", "商品问题": "商品问题", "其他": "其他"}
    if why not in why_dict:
        return f"取消原因 {why} 不存在"
    else:
        dingdan_info[dingdan_id]["订单状态"] = "已取消"

    return (
        f"订单 {dingdan_id}因{why}已取消"
        if dingdan_id in dingdan_info.keys()
        else "未找到该订单"
    )


@before_agent
def get(state, runtime):
    runtime.context["start_time"] = time.time()


@after_agent
def logger_print(state, runtime):
    messages = state.get("messages", [])
    # 统计数据
    times = time.time() - runtime.context["start_time"]
    model_calls = 0
    tool_calls = 0
    total_chars = 0

    for msg in messages:
        if msg.type == "ai":
            model_calls += 1
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                tool_calls += len(msg.tool_calls)
        if hasattr(msg, "content") and msg.content:
            total_chars += len(str(msg.content))

    last_ai = None
    for msg in reversed(messages):
        if msg.type == "ai" and msg.content:
            last_ai = msg
            break
    # 追加到最终回复
    return {
        "messages": [
            AIMessage(
                content=last_ai.content
                + f"\n模型调用次数：{model_calls}\n工具调用次数：{tool_calls}\n字符数：{total_chars}\n耗时：{times}"
            )
        ]
    }


class Dingdan(BaseModel):
    intent: str
    reply: str
    should_escalate: bool


system_prompt = """
你是专业的智能电商客服助手，专注处理用户订单咨询、退换货售后问题，全程严格遵守固定工作规则与输出格式，所有回复必须标准化、规范化，适配系统结构化解析与流式输出展示。
一、核心工作职责
1. 订单查询服务：仅接收用户提供的有效订单号，调用对应工具查询订单实时状态、物流进度、发货时间等信息；用户未提供订单号时，主动礼貌询问，不随意猜测、不无效作答。
2. 退换货售后服务：受理用户退换货申请，必须核验两个核心信息：有效订单号、退换货具体原因（质量问题、七天无理由、发错货等），信息缺失时逐一引导用户补充完整。
3. 问题分级处理：简单的订单查询、常规售后咨询自行解答；遇到复杂问题（订单异常、售后驳回、超时未处理、用户投诉、无对应订单数据等）自动标记升级人工客服。
二、输出强制规则（最高优先级，不可违反）
1. 所有对话输出必须严格输出JSON结构化数据，禁止输出JSON以外的多余文字、解释、语气词、markdown格式，确保系统可直接解析。
2. 固定输出字段（缺一不可，字段类型严格匹配）：
- intent：字符串类型，精准识别用户意图，仅填写固定值：【订单查询、退换货申请、信息补充询问、升级人工客服、无效咨询】
- reply：字符串类型，对用户的完整回复内容，语气亲切、专业简洁，贴合电商客服沟通场景
- should_escalate：布尔值类型，无需升级人工填false，需要升级人工填true
3. 适配流式输出：输出内容语句连贯、分段合理，无冗余重复内容，支持逐段流式展示，不影响前端渲染。
4. 工具调用规范：严格根据用户意图触发对应工具，不滥用工具、不重复调用工具，工具返回结果后整理成通俗易懂的客服话术反馈给用户。
三、场景化应答规范
1. 用户仅咨询订单、未提供订单号：intent填「信息补充询问」，reply礼貌引导用户提供专属订单号以便查询，should_escalate填false。
2. 用户申请退换货、缺失订单号/退换货原因：intent填「信息补充询问」，精准告知用户缺失的信息并引导补充。
3. 工具成功查询到订单信息/受理简单售后：intent匹配对应业务场景，reply清晰告知用户结果，无需升级人工。
4. 遇到无法解决的异常场景、用户情绪激烈、多次信息核对失败：intent填「升级人工客服」，reply告知用户将转接人工客服处理，should_escalate填true。
5. 用户提问与电商订单、售后无关（闲聊、无关咨询）：intent填「无效咨询」，reply礼貌告知仅处理订单及退换货相关问题。
四、语气与风格要求
全程使用标准中文客服话术，耐心礼貌、逻辑清晰、简洁高效，不口语化、不敷衍、不使用网络热词，解答问题精准到位，主动解决用户核心诉求。
"""

agent = create_agent(
    tools=[tuihuo, dingdan_get],
    model=model2,
    system_prompt=system_prompt,
    middleware=[logger_print, get],
    # response_format=ToolStrategy(schema=Dingdan),
    context_schema=dict,
)

for chunk in agent.stream(
    {"messages": [HumanMessage(content="我的订单号是dingdan_id_02，帮我查询订单信息")]},
    context={"start_time": 0},
):
    for name, data in chunk.items():
        if name == "model":
            msg = data.get("messages", [None])[-1]
            if msg and msg.content:
                print(f"[模型回复]\n{msg.content}\n")
        elif name == "tools":
            for m in data.get("messages", []):
                print(f"[工具返回]\n{m.content}\n")
        elif name == "logger_print.after_agent":
            for m in data.get("messages", []):
                print(m.content)
