import nest_asyncio
import os
import subprocess as sp
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.node_parser import SentenceSplitter
from dotenv import load_dotenv
from langchain_community.chat_models.baidu_qianfan_endpoint import QianfanChatEndpoint  # 更新后的导入
import mysql.connector
from langchain.tools import Tool
from langchain.agents import initialize_agent, AgentType
from llama_index.core.chat_engine.types import ChatMode
import graph_RAG
import json
import re
import subprocess
from mysql.connector import Error
import Qianfanpack
# -------------------------------------------------
# 允许在已运行的事件循环中嵌套 async 任务
nest_asyncio.apply()

# 加载环境变量
load_dotenv()
access_key = os.getenv("QIANFAN_ACCESS_KEY")
secret_key = os.getenv("QIANFAN_SECRET_KEY")

# 启动千帆 OpenAI 代理
os.environ["OPENAI_API_KEY"] = "FAKE_KEY"
os.environ["OPENAI_API_BASE"] = "http://127.0.0.1:8001/v1"
server = sp.Popen("qianfan openai -p 8001", shell=True)

# ---------------------------------------------------------------------------------------------------------------
# 定义 RAG 文档查询工具
# 加载文档数据
documents = SimpleDirectoryReader("data").load_data()
transformations = [
    SentenceSplitter(chunk_size=200, chunk_overlap=50),
    OpenAIEmbedding(embed_batch_size=10),
]
index = VectorStoreIndex.from_documents(
    documents, transformations=transformations, show_progress=True
)
llm_RAG = QianfanChatEndpoint(
    model="ERNIE-4.0-8K-Latest",
    temperature=0.1,
    timeout=30,
    api_key="1CArYp3LEoUHNmZ5TL66M9h6",
    secret_key="E7KgZivsfKLOk5fKGYPbYMEMQMPX6HiA"
)
query_engine = index.as_chat_engine(
    llm=llm_RAG,
    similarity_top_k=5,
    chat_mode=ChatMode.CONTEXT,
    system_prompt="你是一个text to SQL的自然语言数据库辅助查询助手，你需要根据提供的文档内容和用户问题进行回答。并给出能够在数据库查询到用户所"
                  "需的数据所要用到的SQL，当前使用的数据库名为employees，当前用户为tylor，当前使用的是Mysql数据库"
)


def rag_query_normal(question):
    response = query_engine.chat(question)
    print("-----------------------------------------------\n")
    print("\n基于普通查询得到的相关信息")
    print(response)
    print("-----------------------------------------------\n\n")
    return response


rag_document_tool = Tool(
    name="RAG_Document_Query",
    func=rag_query_normal,
    description="用于从数据库相关文档中检索内容并进行信息或者SQL返回，能够从中获取到数据库中的表的相关信息，用户信息，数据库有哪些等信息，适用于"
                "简单的问答，对于简单的不涉及多个表的查询有所帮助"
)


# ----------------------------------------------------------------------------------------------------------------------
def rag_query_graph(question):
    retriever = graph_RAG.VectorRetriever()
    generator = graph_RAG.SQLGenerator()
    schema_context = retriever.get_semantic_context(question)
    answer = generator.generate_response(question, "\n".join(schema_context))
    return answer


rag_graph_tool = Tool(
    name="RAG_Graph_Query",
    func=rag_query_graph,
    description="用于获取问题相关的图结构能够有效的知道表之间的关系以及表的基本信息，对于复杂的SQL查询有帮助，特别是对于涉及多个表的问题，以及需要联合查询以及涉及到外键的问题等"
)

# 输出可用图像链接
# ----------------------------------------------------------------------------------------------------------------------

index_of_display = 0

def display(question):
    global index_of_display
    try:
        # 提取 SQL 语句
        matches = re.findall(r'```sql\s*(.*?)\s*```', str(question), re.DOTALL)
        if not matches:
            return "错误：未找到有效的 SQL 语句，请确保 SQL 包含在 ```sql ``` 代码块中"

        conn = None
        cursor = None
        try:
            # 连接数据库
            conn = mysql.connector.connect(
                host="localhost",
                user="Tylor",
                password="Zjw201314",
                database="employees"  # 直接指定数据库，避免额外的 USE 语句
            )
            cursor = conn.cursor()

            # 执行 SQL
            sql = matches[0]
            sql_statements = [stmt.strip() for stmt in sql.split(';') if stmt.strip()]

            for stmt in sql_statements:
                try:
                    cursor.execute(stmt)
                except Error as e:
                    return f"SQL 执行错误:\n- 错误语句: {stmt}\n- 错误详情: {str(e)}"

            # 获取结果
            results = cursor.fetchall()
            if cursor.description:  # 只有查询语句才有 description
                columns = [desc[0] for desc in cursor.description]
            else:
                columns = []

            # 准备数据
            route = f"/{index_of_display}"
            index_of_display += 1

            # 处理字节类型数据
            processed_results = []
            for row in results:
                processed_row = [item.decode('utf-8') if isinstance(item, bytes) else item for item in row]
                processed_results.append(processed_row)

            data = json.dumps({
                'results': processed_results,
                'columns': columns,
                'route': route
            })

            # 启动子进程
            try:
                subprocess.run(
                    ['cmd', '/c', 'start', 'cmd', '/k', 'python', 'runapp.py', data],
                    shell=True,
                    check=True,
                    timeout=10  # 设置超时时间
                )
                return "访问网页 http://127.0.0.1:5000 以查看查询结果"
            except subprocess.TimeoutExpired:
                return "错误：启动展示程序超时"
            except subprocess.CalledProcessError as e:
                return f"错误：启动展示程序失败，返回码 {e.returncode}"
            except Exception as e:
                return f"未知子进程错误: {str(e)}"

        except Error as e:
            return f"数据库连接/操作错误: {str(e)}"
        finally:
            # 确保关闭连接
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    except Exception as e:
        return f"系统发生未预期的错误: {str(e)}"


display_tool = Tool(name="Display",
                    func=display,
                    description="作为一个查询工具输入带有SQL的文字输出查询结果网页链接，其结果会被展示在网页上,输入的SQL应该被```sql SQL内容 ``` ")

# ----------------------------------------------------------------------------------------------------------------------
# 初始化 Agent
llm_Agent = QianfanChatEndpoint(
    model="ERNIE-4.0-8K-Latest",
    temperature=0.1,
    timeout=30,
    api_key="1CArYp3LEoUHNmZ5TL66M9h6",
    secret_key="E7KgZivsfKLOk5fKGYPbYMEMQMPX6HiA"
)

qianfan_llm = Qianfanpack.QianfanLLM(
    api_key='bce-v3/ALTAK-8OgNFKW9v7KIfdfFl50xC/81b776a2ea7378b00697cb0d25047d684d025e26',
    model="deepseek-v3"
)

agent = initialize_agent(
    tools=[rag_document_tool, rag_graph_tool, display_tool],  # 提供 SQL 查询和 RAG 文档查询工具
    llm=llm_Agent,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,  # 让 Agent 自主决策
    verbose=True,
    handle_parsing_errors=True
)

# ----------------------------------------------------------------------------------------------------------------------
# 进行问答
while True:
    question = input("\n请输入你的数据库查询相关问题（输入 'exit' 退出）： ")
    if question.lower() == "exit":
        break

    prompt = (
        "你是一个专门用于数据库查询的 Text-to-SQL Agent。\n"
        "你的任务是将用户的查询需求转换为 SQL 语句，并调用正确的工具来执行。\n\n"
        "可用工具：\n"
        "1. RAG_Document_Query - 用于从文档中检索数据库信息和复杂SQL\n"
        "2. RAG_Graph_Query - 用于查询表结构和关系以及简单SQL\n\n"
        "3. Display - 用于展示SQL查询后的结果，输入带有SQL的语句返回查询结果展示，输入SQL需要按照这个格式```sql SQL内容 ```"
        "请根据问题复杂度和实际应用选择合适的工具。不要采用任何的假设来回答问题，要么有数据参考，要么就回答不知道不确定。如果最终回答有SQL那么必定"
        "要调用Display工具按照格式输入并获得查询结果"
    )
    response = agent.invoke({"input":prompt + question})
    print("--------------------------------------------------")
    print(response["output"])

# 终止千帆服务
server.terminate()