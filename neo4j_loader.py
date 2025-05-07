from py2neo import Graph, Node, Relationship
from schema_extractor import extract_schema
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import numpy as np
import os

# 加载环境变量
load_dotenv()

# 初始化文本向量化模型（中文推荐 paraphrase-multilingual-MiniLM-L12-v2）
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')


def get_text_embedding(text):
    """将文本转换为向量"""
    if not text or str(text).strip() == "":
        return None
    return model.encode(str(text)).tolist()  # 返回768维向量


# 连接Neo4j
neo4j_graph = Graph(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PWD"))
)


def load_schema_to_neo4j(schemas_to_load=None):
    # 清空现有数据
    neo4j_graph.delete_all()
    schema = extract_schema()

    for table_name, table_data in schema.items():
        if schemas_to_load is None or table_name in schemas_to_load:
            table_name = str(table_name)
            table_comment = str(table_data.get("comment", ""))

            # 生成表名和注释的向量
            table_text = f"{table_name} {table_comment}"
            table_vector = get_text_embedding(table_text)

            # 创建表节点（包含向量）
            table_node = Node("Table",
                              name=table_name,
                              type="table",
                              comment=table_comment,
                              vector=table_vector)
            neo4j_graph.create(table_node)

            for col in table_data["columns"]:
                col_name = str(col["name"])
                col_comment = str(col.get("comment", ""))
                col_type = str(col["type"])

                # 生成字段名和注释的向量
                col_text = f"{col_name} {col_comment} {col_type}"
                col_vector = get_text_embedding(col_text)

                # 创建字段节点（包含向量）
                col_node = Node("Column",
                                name=f"{table_name}.{col_name}",
                                dtype=col_type,
                                comment=col_comment,
                                vector=col_vector)
                neo4j_graph.create(col_node)
                neo4j_graph.create(Relationship(table_node, "CONTAINS", col_node))

            for fk in table_data["foreign_keys"]:
                # 创建外键关系
                neo4j_graph.run(f"""
                    MATCH (a:Column {{name: '{str(fk["source"])}'}})
                    MATCH (b:Column {{name: '{str(fk["target"])}'}})
                    MERGE (a)-[:FOREIGN_KEY]->(b)
                """)

    # 创建向量索引（提升搜索性能）
    neo4j_graph.run("""
    CREATE FULLTEXT INDEX entityVectorIndex IF NOT EXISTS
    FOR (n:Table|Column) ON EACH [n.vector]
    """)


if __name__ == "__main__":
    # 定义要加载的schema（None表示加载全部）
    schemas_to_load = ["salaries", "employees", "dept_manager",
                       "titles", "dept_emp", "departments"]

    load_schema_to_neo4j(schemas_to_load)
    print("MySQL Schema已导入Neo4j（含向量化信息）！")