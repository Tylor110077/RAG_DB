import nest_asyncio
import subprocess as sp
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.node_parser import SentenceSplitter
from dotenv import load_dotenv
from langchain.chat_models.baidu_qianfan_endpoint import QianfanChatEndpoint
from llama_index.core.chat_engine.types import ChatMode
import mysql.connector
import os
import sys
import io
import re
import subprocess
import json

# 连接 MySQL
conn = mysql.connector.connect(
    host="localhost",  # MySQL 服务器地址
    user="Tylor",  # 用户名
    password="Zjw201314",  # 密码
)

# 创建游标
cursor = conn.cursor()
cursor.execute("USE employees;")

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')

# 允许在已运行的事件循环中嵌套 async 任务
nest_asyncio.apply()

# 设置 OpenAI API 兼容接口（转发到千帆服务）
os.environ["OPENAI_API_KEY"] = "FAKE_KEY"
os.environ["OPENAI_API_BASE"] = "http://127.0.0.1:8001/v1"

# 加载千帆 API 认证信息
load_dotenv()
access_key = os.getenv("QIANFAN_ACCESS_KEY")
secret_key = os.getenv("QIANFAN_SECRET_KEY")

os.environ["QIANFAN_ACCESS_KEY"] = access_key
os.environ["QIANFAN_SECRET_KEY"] = secret_key
os.environ["QIANFAN_QPS_LIMIT"] = "5"  # 限制 QPS 避免被封

# 启动本地千帆 OpenAI 代理
server = sp.Popen("qianfan openai -p 8001", shell=True)

# 加载本地文档
documents = SimpleDirectoryReader("data").load_data()

# 文档预处理：切分文本 + 向量化
transformations = [
    SentenceSplitter(chunk_size=200, chunk_overlap=50),  # 保留一定重叠
    OpenAIEmbedding(embed_batch_size=10),  # 向量化
]

# 创建向量索引
index = VectorStoreIndex.from_documents(
    documents, transformations=transformations, show_progress=True
)

# 使用 SQLCoder 结合文档进行智能问答
llm_Agent = QianfanChatEndpoint(
    model="ERNIE-4.0-8K-Latest",
    temperature=0.1,
    timeout=30,
    api_key="1CArYp3LEoUHNmZ5TL66M9h6",
    secret_key="E7KgZivsfKLOk5fKGYPbYMEMQMPX6HiA"
)


query_engine = index.as_chat_engine(
    llm = llm_Agent,
    similarity_top_k=5,  # 检索最相似的 5 条内容
    chat_mode=ChatMode.CONTEXT, # 让模型结合上下文回答=
    system_prompt="你是一个text to SQL的自然语言数据库辅助查询助手，你需要根据提供的文档内容和用户问题进行回答。并给出能够在数据库查询到用户所"
                  "需的数据所要用到的SQL，当前使用的数据库名为employees，当前用户为tylor"
)

index_of_display = 0


def display(index_of_display, matches, matches_no):
    sql = matches[matches_no]
    sql_statements = sql.strip().split(';')
    for stmt in sql_statements:
        stmt = stmt.strip()
        if stmt:
            cursor.execute(stmt)
    results = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    route = "/" + str(index_of_display)
    print(index_of_display)
    index_of_display += 1
    results = [item.decode('utf-8') if isinstance(item, bytes) else item for item in results]
    route = route.decode('utf-8') if isinstance(route, bytes) else route
    data = json.dumps({'results': results, 'columns': columns, 'route': route})
    subprocess.run(['cmd', '/c', 'start', 'cmd', '/k', 'python', 'runapp.py', data], shell=True)


# 进行问答
while True:
    question = input("\n请输入你的问题（输入 'exit' 退出）： ")
    if question.lower() == "exit":
        break

    response = query_engine.chat(question)
    print("--------------------------------------------------")
    print(f"\n大模型回答：\n{response}\n")

    matches = re.findall(r'```sql\s*(.*?)\s*```', str(response), re.DOTALL)

    print(matches)

    if not matches:
        pass
    else:

        for i, sql in enumerate(matches, 1):
            print("--------------------------------------------------")
            print(f"SQL {i}:\n{sql}\n")
            print("--------------------------------------------------")
        while True:
            no_sql = input("输入你想要展示的SQL结果数字编号，或者按下c或者C以跳过\n")
            numbers = re.findall(r'\d+', no_sql)
            if numbers:
                first_number = int(numbers[0]) if numbers else None
                matches_no = first_number - 1
                try:
                    display(index_of_display, matches, matches_no)
                except:
                    print("当前命令逻辑链不完整,不正确,或者参数错误")
            elif 'c' in no_sql.lower():
                break

# 终止千帆服务


cursor.close()
conn.close()
server.terminate()
