import psutil
from flask import Flask, render_template_string, redirect
import sys
import json
import os
from datetime import datetime


def stop_flask_processes(port=5000):
    current_pid = os.getpid()  # 获取当前进程的 PID
    current_script_name = os.path.basename(__file__)  # 获取当前脚本的文件名

    # 遍历所有正在运行的进程
    for process in psutil.process_iter(attrs=['pid', 'name', 'cmdline']):
        try:
            # 获取进程的 cmdline
            cmdline = process.info.get('cmdline', [])
            # 排除当前进程，避免误杀自己
            if process.info['pid'] == current_pid:
                continue

            # 检查该进程是否在监听指定的端口
            for conn in process.connections(kind='inet'):  # 获取所有互联网连接
                if conn.laddr.port == port:
                    # 如果进程正在监听指定端口，则终止它
                    print(f"Terminating process {process.info['pid']} on port {port}...")
                    process.terminate()
                    break  # 一旦找到，跳出检查

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

def start_flask_app(results, columns, route, save_path):
    app = Flask(__name__)

    @app.route("/")
    def home():
        return redirect(route)

    @app.route(route)
    def index():
        # 渲染模板
        html_content = render_template_string("""
            <html>
                <head>
                    <title>Query Results</title>
                    <style>
                        table {
                            border-collapse: collapse;
                            width: 80%;
                            margin: 20px auto;
                            font-family: Arial, sans-serif;
                        }
                        th, td {
                            border: 1px solid #ccc;
                            padding: 8px 12px;
                            text-align: left;
                        }
                        th {
                            background-color: #f2f2f2;
                        }
                        tr:nth-child(even) {
                            background-color: #fafafa;
                        }
                    </style>
                </head>
                <body>
                    <h1 style="text-align:center;">Query Results</h1>
                    <table>
                        <thead>
                            <tr>
                                {% for col in columns %}
                                    <th>{{ col }}</th>
                                {% endfor %}
                            </tr>
                        </thead>
                        <tbody>
                            {% for row in results %}
                                <tr>
                                    {% for cell in row %}
                                        <td>{{ cell }}</td>
                                    {% endfor %}
                                </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </body>
            </html>
            """, results=results, columns=columns)

        # 保存 HTML 到指定路径
        os.makedirs(save_path, exist_ok=True)  # 确保文件夹存在
        time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        name = "query_results_" + str(time) + ".html"
        file_path = os.path.join(save_path, name)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"HTML saved to {file_path}")

        return html_content


    app.run(use_reloader=False, debug=True)  # 禁用自动重载功能


# 从命令行获取数据并解析
data = json.loads(sys.argv[1])

results = data['results']
columns = data['columns']
route = data['route']
save_path = "./results"  # 这里指定你希望保存的文件夹路径

# 关闭所有正在运行的 Flask 进程
stop_flask_processes()

# 启动新的 Flask 应用
start_flask_app(results, columns, route, save_path)
