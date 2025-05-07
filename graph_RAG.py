from neo4j import GraphDatabase
from openai import OpenAI
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import mysql.connector
import subprocess
import json
import os
import sys
import io
import re

# 加载环境变量
load_dotenv()

# 初始化文本向量化模型
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')


class VectorRetriever:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI"),
            auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PWD"))
        )

    def get_semantic_context(self, question):
        # 确保生成浮点数向量
        question_vector = [float(x) for x in model.encode(question)]

        query = """
        WITH $vector AS input_vector
        UNWIND input_vector AS value 
        WITH collect(toFloat(value)) AS q_vector
        MATCH (n)
        WHERE n.vector IS NOT NULL
        WITH n, 
             [x IN n.vector | toFloat(x)] AS n_vector,
             q_vector
        WITH n,
             n_vector,
             q_vector,
             sqrt(reduce(s=0.0, x IN n_vector | s + x*x)) AS norm_n,
             sqrt(reduce(s=0.0, x IN q_vector | s + x*x)) AS norm_q
        WITH n,
             n_vector,
             q_vector,
             norm_n,
             norm_q,
             reduce(s=0.0, i IN range(0, size(n_vector)-1) | 
                   s + n_vector[i] * q_vector[i]) AS dot_product
        WHERE norm_n > 0.0 AND norm_q > 0.0
        WITH n, 
             dot_product / (norm_n * norm_q) AS similarity
        ORDER BY similarity DESC LIMIT 4
        MATCH path=(n)-[:CONTAINS|FOREIGN_KEY*0..2]-(related)
        RETURN nodes(path) AS nodes, relationships(path) AS rels, similarity
        """

        with self.driver.session() as session:
            result = session.run(query, vector=question_vector)
            return [self._format_path(record) for record in result]

    def _format_path(self, record):
        """格式化子图信息为文本，包含comment信息（如果存在）"""
        nodes = [dict(node) for node in record["nodes"]]
        rels = record["rels"]  # 保持原始关系对象
        similarity = record["similarity"]

        desc = [f"\n匹配相似度: {similarity:.2f}"]

        for node in nodes:
            # 处理节点信息
            node_info = []
            if node.get("type") == "table":
                node_info.append(f"表【{node['name']}】")
            elif "dtype" in node:
                node_info.append(f"字段 {node['name']} (类型: {node['dtype']})")

            # 添加comment信息（如果存在）
            if "comment" in node and node["comment"]:
                node_info.append(f"备注: {node['comment']}")

            if node_info:
                desc.append(" ".join(node_info))

        # 处理关系信息
        for i, rel in enumerate(rels):
            if i + 1 < len(nodes):
                rel_type = getattr(rel, 'type', 'RELATED')
                rel_info = f"关系: {nodes[i]['name']} --{rel_type}--> {nodes[i + 1]['name']}"

                # 添加关系comment（如果存在）
                if hasattr(rel, 'comment') and rel.comment:
                    rel_info += f" (备注: {rel.comment})"

                desc.append(rel_info)

        return "\n".join(desc)


class SQLGenerator:
    def __init__(self):
        self.client = OpenAI(
            base_url='https://qianfan.baidubce.com/v2',
            api_key='bce-v3/ALTAK-8OgNFKW9v7KIfdfFl50xC/81b776a2ea7378b00697cb0d25047d684d025e26',
            default_headers={"appid": "app-WFuOZMng"}
        )

    def generate_response(self, question, context):
        """生成自然语言回答或SQL"""
        response = self.client.chat.completions.create(
            model="deepseek-v3",
            messages=[
                {
                    "role": "system",
                    "content": "你是一个数据库助手，根据提供的数据库结构回答问题。"
                               "如果问题需要查询数据，直接生成SQL；"
                               "如果是概念性问题，用自然语言回答。"
                               "当前使用的数据库名为employees，当前用户为tylor,使用Mysql数据库,用中文回答"
                },
                {
                    "role": "user",
                    "content": f"数据库上下文:\n{context}\n\n问题: {question}"
                }
            ],
            temperature=0
        )
        return response.choices[0].message.content


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


if __name__ == "__main__":
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

    retriever = VectorRetriever()
    generator = SQLGenerator()

    index_of_display = 0

    while True:
        question = input("\n请输入您的问题（输入exit退出）: ")
        if question.lower() == 'exit':
            break

        # 1. 语义检索
        schema_context = retriever.get_semantic_context(question)
        print("\n相关数据库结构:")
        print("\n".join(schema_context))

        # 2. 生成回答
        answer = generator.generate_response(question, "\n".join(schema_context))
        print("\n回答结果:")
        print(answer)

        matches = re.findall(r'```sql\s*(.*?)\s*```', str(answer), re.DOTALL)

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
