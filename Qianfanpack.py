from typing import Optional, List, Dict, Any
from pydantic import Field
from langchain.llms.base import LLM
from openai import OpenAI
import graph_RAG
from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool


class QianfanLLM(LLM):
    """自定义百度千帆大模型LLM包装器"""
    api_key: str = Field(..., description="百度千帆API Key")
    model: str = Field(default="ernie-x1-32k", description="模型名称")

    @property
    def _llm_type(self) -> str:
        return "qianfan"

    def _call(self, prompt: str, stop: Optional[List[str]] = None, **kwargs) -> str:
        client = OpenAI(
            base_url='https://qianfan.baidubce.com/v2',
            api_key=self.api_key
        )
        response = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            extra_body={
                "web_search": {
                    "enable": False,
                    "enable_citation": False,
                    "enable_trace": False
                }
            },
            **kwargs
        )
        return response.choices[0].message.content

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {"model": self.model, "api_key": self.api_key}

if __name__ == '__main__':
    # 初始化（现在会正确验证字段）
    qianfan_llm = QianfanLLM(
        api_key='bce-v3/ALTAK-8OgNFKW9v7KIfdfFl50xC/81b776a2ea7378b00697cb0d25047d684d025e26',
        model="deepseek-v3"
    )


    # 初始化自定义LLM

    def rag_query_graph(question):
        return "这是一个测试工具"


    rag_graph_tool = Tool(
        name="RAG_Graph_Query",
        func=rag_query_graph,
        description="测试工具"
    )
    # 初始化Agent
    agent = initialize_agent(
        tools=[rag_graph_tool],
        llm=qianfan_llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        handle_parsing_errors=True
    )

    # 使用Agent
    response = agent.invoke({"input": "你和深度求索公司的关系？"})
    print(response)
