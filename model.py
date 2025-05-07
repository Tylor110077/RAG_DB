import shutil
from sentence_transformers import SentenceTransformer
import os

# 清除旧缓存（谨慎操作）
cache_path = r"C:\Users\Tylor\.cache\huggingface\hub\models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2"
if os.path.exists(cache_path):
    shutil.rmtree(cache_path)

# 重新下载（添加resume_download和force_download参数）
model = SentenceTransformer(
    'paraphrase-multilingual-MiniLM-L12-v2',
    cache_folder=r"C:\MyFile\Graduation_design\PJnew\models",  # 指定新缓存路径 # 强制重新下载
)