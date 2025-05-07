import mysql.connector
import os

# 连接 MySQL
conn = mysql.connector.connect(
    host="localhost",  # MySQL 服务器地址
    user="Tylor",  # 用户名
    password="Zjw201314",  # 密码
)

# 创建游标
cursor = conn.cursor()

# -------------------------------------------------------------
# 获取用户信息
cursor.execute("""
    SELECT 
        user, 
        host 
    FROM mysql.user;
""")
users = cursor.fetchall()  # 获取所有用户信息

# 将获取的用户信息存储到文件中
with open('./data/MySQL_USER.txt', 'w') as f:
    for user in users:
        f.write(f"User: {user[0]}, Host: {user[1]}\n")

# -------------------------------------------------------------
# 获取所有数据库信息及其配置
cursor.execute("SELECT schema_name, default_character_set_name, default_collation_name FROM "
               "information_schema.schemata;")
databases = cursor.fetchall()  # 获取所有数据库信息

# 将获取的数据库信息存储到文件中
with open('./data/MySQL_DB.txt', 'w') as f:
    for db in databases:
        f.write(f"Database Name: {db[0]}\n")
        f.write(f"  Default Character Set: {db[1]}\n")
        f.write(f"  Default Collation: {db[2]}\n")

# -------------------------------------------------------------
# 指定要处理的数据库和表
target_db = 'employees'  # 指定的数据库名
target_tables = ['employees', 'departments', 'salaries']  # 指定要处理的表名列表

# 获取指定数据库中的所有表信息
cursor.execute(
    f"SELECT table_name, table_type, create_time FROM information_schema.tables WHERE table_schema = '{target_db}';")
tables = cursor.fetchall()

for table in tables:
    table_name = table[0]

    # 只处理指定的表
    if table_name not in target_tables:
        continue

    file_name = f'./data/Metadata_++{target_db}++_++{table_name}++.txt'
    with open(file_name, 'w') as f:
        f.write(f"Database Name: {target_db}\n")
        f.write(f"Table Name: {table_name}\n")
        f.write(f"  Table Type: {table[1]}\n")
        f.write(f"  Created At: {table[2]}\n")

        # 获取列信息
        cursor.execute(f"""
            SELECT column_name, data_type, is_nullable, column_default, 
                   character_maximum_length, numeric_precision, numeric_scale, collation_name 
            FROM information_schema.columns 
            WHERE table_schema = '{target_db}' AND table_name = '{table_name}';
        """)
        columns = cursor.fetchall()

        for column in columns:
            f.write(f"  Column Name: {column[0]}\n")
            f.write(f"    Data Type: {column[1]}\n")
            f.write(f"    Is Nullable: {column[2]}\n")
            f.write(f"    Default Value: {column[3]}\n")
            f.write(f"    Max Length: {column[4]}\n")
            f.write(f"    Numeric Precision: {column[5]}\n")
            f.write(f"    Numeric Scale: {column[6]}\n")
            f.write(f"    Collation: {column[7]}\n\n")

        f.write("\n")

# -------------------------------------------------------------
# 清理不存在的数据库或表的元数据文件

# 获取所有数据库名称
cursor.execute("SHOW DATABASES;")
databases = [db[0] for db in cursor.fetchall()]

# 获取文件夹中的所有文件
folder_path = './data/'  # 请根据实际情况修改文件夹路径
files = os.listdir(folder_path)

# 遍历文件夹中的所有文件
for file in files:
    # 判断文件是否符合命名规则：Metadata_++{db_name}++_++{table_name}++.txt
    if file.startswith("Metadata_") and file.endswith(".txt"):
        # 从文件名中提取数据库名和表名
        parts = file.split("++")
        if len(parts) >= 4:
            db_name = parts[1]  # 获取数据库名
            table_name = parts[3]  # 获取表名

            # 检查数据库是否存在
            if db_name not in databases:
                print(f"Database {db_name} does not exist. Deleting file: {file}")
                os.remove(os.path.join(folder_path, file))  # 删除文件
            else:
                # 如果数据库存在，检查表是否存在
                cursor.execute(f"""
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_schema = '{db_name}' 
                    AND table_name = '{table_name}';
                """)
                table_exists = cursor.fetchone()[0] > 0

                if not table_exists:
                    print(f"Table {table_name} in database {db_name} does not exist. Deleting file: {file}")
                    os.remove(os.path.join(folder_path, file))  # 删除文件

# 关闭连接
cursor.close()
conn.close()