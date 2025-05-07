# 使用官方 Python 镜像作为基础镜像
FROM python:3.9

# 设置工作目录
WORKDIR /app

# 将当前目录下的文件复制到容器的 /app 目录
COPY . /app

# 安装依赖
RUN pip install --upgrade pip
RUN pip install -U "qianfan[openai]" -i https://pypi.tuna.tsinghua.edu.cn/simple
RUN pip install -r requirements.txt


#EXPOSE 5000

# 运行应用程序
CMD ["python", "test.py"]