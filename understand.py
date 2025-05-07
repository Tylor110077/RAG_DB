import os
from openai import OpenAI

# 初始化客户端
client = OpenAI(
    base_url='https://qianfan.baidubce.com/v2',
    api_key='bce-v3/ALTAK-8OgNFKW9v7KIfdfFl50xC/81b776a2ea7378b00697cb0d25047d684d025e26',
    default_headers={"appid": "app-WFuOZMng"}
)


def get_prompt_by_filename(filename):
    """根据文件名返回对应的提示词"""
    if filename == "MySQL_USER.txt":
        return "观察当前文件内容，总结并描述下其中的核心内容，这是一个数据库的所有用户的相关信息，描述信息尽可能的抓住重点语言精炼"
    elif filename == "MySQL_DB.txt":
        return "观察当前文件内容，总结并描述下其中的核心内容，这个文件主要是描述了有哪些数据库，描述信息尽可能的抓住重点语言精炼"
    elif filename.startswith("Metadata"):
        return "这是一个数据库中的表的相关信息，总结并描述下其中的核心内容，描述信息尽可能的抓住重点语言精炼"
    else:
        return "总结并描述下当前文件的核心内容"


def process_file(filepath):
    """处理单个文件：读取内容、调用API总结、追加结果"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    filename = os.path.basename(filepath)
    prompt = get_prompt_by_filename(filename)

    # 调用API获取总结
    response = client.chat.completions.create(
        model="deepseek-v3",
        messages=[
            {"role": "system", "content": "你是一个专业的数据库管理员，擅长总结技术文档。"},
            {"role": "user", "content": f"{prompt}\n\n文件内容:\n{content}"}
        ]
    )

    summary = response.choices[0].message.content

    # 将总结追加到文件末尾
    with open(filepath, 'a', encoding='utf-8') as f:
        f.write("\n\n=== AI 总结 ===\n")
        f.write(summary)

    return summary


def process_folder(folder_path):
    """处理文件夹中的所有文件"""
    for filename in os.listdir(folder_path):
        filepath = os.path.join(folder_path, filename)
        if os.path.isfile(filepath):
            print(f"正在处理文件: {filename}")
            try:
                summary = process_file(filepath)
                print(f"文件 {filename} 处理完成，总结已追加。")
            except Exception as e:
                print(f"处理文件 {filename} 时出错: {str(e)}")


# 使用示例
folder_to_process = "./data"  # 替换为你的文件夹路径
process_folder(folder_to_process)