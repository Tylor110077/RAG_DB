from typing import Optional, List, Dict, Any
from pydantic import Field
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain.schema import ChatResult, ChatGeneration
from openai import OpenAI
from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool


class QianfanChatModel(BaseChatModel):  # 修改1：改为继承BaseChatModel
    """自定义百度千帆大模型ChatModel包装器"""
    api_key: str = Field(..., description="百度千帆API Key")
    model: str = Field(default="ernie-x1-32k", description="模型名称")

    @property
    def _llm_type(self) -> str:
        return "qianfan-chat"

    def _generate(self, messages: List[BaseMessage], **kwargs) -> ChatResult:
        client = OpenAI(
            base_url='https://qianfan.baidubce.com/v2',
            api_key=self.api_key
        )
        # 将LangChain消息格式转换为OpenAI格式
        openai_messages = [
            {"role": "user" if isinstance(m, HumanMessage) else "assistant",
             "content": m.content}
            for m in messages
        ]
        response = client.chat.completions.create(
            model=self.model,
            messages=openai_messages,
            extra_body={
                "web_search": {
                    "enable": False,
                    "enable_citation": False,
                    "enable_trace": False
                }
            },
            **kwargs
        )
        # 返回LangChain格式的ChatResult
        return ChatResult(
            generations=[
                ChatGeneration(message=AIMessage(content=response.choices[0].message.content))
            ]
        )
    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {"model": self.model, "api_key": self.api_key}


# 初始化ChatModel
qianfan_chat = QianfanChatModel(
    api_key='bce-v3/ALTAK-8OgNFKW9v7KIfdfFl50xC/81b776a2ea7378b00697cb0d25047d684d025e26',
    model="ernie-x1-32k"
)


def rag_query_graph(question):
    return "这是一个测试工具响应"


# 定义工具
rag_graph_tool = Tool(
    name="RAG_Graph_Query",
    func=rag_query_graph,
    description="用于测试的工具"
)

# 初始化Agent - 修改2：使用ZERO_SHOT_REACT_DESCRIPTION
agent = initialize_agent(
    tools=[rag_graph_tool],
    llm=qianfan_chat,  # 使用修改后的ChatModel
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,  # 使用基础Agent类型
    verbose=True,
    handle_parsing_errors=True
)

# 测试调用
response = agent.invoke({"input": "你是谁？"})
print(response)