from sqlalchemy import create_engine, MetaData, text
from dotenv import load_dotenv
import os

load_dotenv()

# 构造 MySQL 连接 URL
MYSQL_URL = f"mysql+pymysql://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PWD')}@{os.getenv('MYSQL_HOST')}/{os.getenv('MYSQL_DB')}"
engine = create_engine(MYSQL_URL)
metadata = MetaData()


def extract_schema():
    metadata.reflect(bind=engine)
    schema = {}

    # 获取表注释
    with engine.connect() as conn:
        result = conn.execute(text(f"""
            SELECT table_name AS tname, table_comment AS tcomment
            FROM information_schema.tables
            WHERE table_schema = '{os.getenv("MYSQL_DB")}'
        """))
        table_comments = {row["tname"]: row["tcomment"] for row in result.mappings()}

    for table in metadata.tables.values():
        schema[table.name] = {
            "columns": [{"name": col.name, "type": str(col.type), "comment": col.comment or ""}
                        for col in table.columns],
            "foreign_keys": [
                {
                    "source": f"{table.name}.{fk.parent.name}",
                    "target": f"{fk.column.table.name}.{fk.column.name}"
                }
                for fk in table.foreign_keys
            ],
            "comment": table_comments.get(table.name, "")
        }

    return schema


# 测试用：输出 JSON 格式结构
if __name__ == "__main__":
    import json
    print(json.dumps(extract_schema(), indent=2, ensure_ascii=False))
