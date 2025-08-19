import streamlit as st
import os
from dotenv import load_dotenv, find_dotenv, set_key
import subprocess
import glob

# App title
st.set_page_config(page_title="ARXIV每日文章总结系统(MCP&Agent挑战赛)", layout="wide")
st.title("ARXIV每日文章总结系统(MCP&Agent挑战赛)")

# --- Helper Functions ---
def get_latest_summary_file():
    """Finds the most recently created summary markdown file."""
    list_of_files = glob.glob(os.path.join('arxiv_history', '*.md'))
    if not list_of_files:
        return None
    latest_file = max(list_of_files, key=os.path.getctime)
    return latest_file

def load_env_variables():
    """Loads environment variables from .env file."""
    load_dotenv()
    config = {
        "DASHSCOPE_API_KEY": os.getenv("DASHSCOPE_API_KEY", ""),
        "DASHSCOPE_BASE_URL": os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
        "QWEN_MODEL": os.getenv("QWEN_MODEL", "qwen-turbo"),
        "CATEGORIES": os.getenv("CATEGORIES", "cs.CV"),
        "MAX_ENTRIES": int(os.getenv("MAX_ENTRIES", 3)),
        "MAX_PAPER_NUM": int(os.getenv("MAX_PAPER_NUM", 3)),
        "TEMPERATURE": float(os.getenv("TEMPERATURE", 0.7)),
        "NUM_WORKERS": int(os.getenv("NUM_WORKERS", 4)),
        "SAVE_DIR": os.getenv("SAVE_DIR", "./arxiv_history"),
        "DESCRIPTION_PATH": os.getenv("DESCRIPTION_PATH", "personal_research_interests.md"),
        "SAVE_TO_MARKDOWN": os.getenv("SAVE_TO_MARKDOWN", "true").lower() == "true",
    }
    return config

def save_env_variables(config):
    """Saves the configuration to the .env file."""
    dotenv_path = find_dotenv()
    if not dotenv_path:
        dotenv_path = os.path.join(os.getcwd(), '.env')
        open(dotenv_path, 'a').close() # Create the file if it doesn't exist

    for key, value in config.items():
        set_key(dotenv_path, key, str(value))
    return True

# --- UI Layout ---

# Load current config
config = load_env_variables()

# Sidebar for configuration
st.sidebar.header("配置")

with st.sidebar.form(key='config_form'):
    st.subheader("API 设置")
    config["DASHSCOPE_API_KEY"] = st.text_input("DashScope API 密钥", value=config["DASHSCOPE_API_KEY"], type="password")
    config["DASHSCOPE_BASE_URL"] = st.text_input("DashScope Base URL", value=config["DASHSCOPE_BASE_URL"])
    config["QWEN_MODEL"] = st.text_input("Qwen 模型", value=config["QWEN_MODEL"])

    st.subheader("ArXiv 设置")
    config["CATEGORIES"] = st.text_input("分类 (逗号分隔)", value=config["CATEGORIES"])
    config["MAX_ENTRIES"] = st.number_input("获取的最大条目数", min_value=1, value=config["MAX_ENTRIES"])
    config["MAX_PAPER_NUM"] = st.number_input("要总结的最大论文数", min_value=1, value=config["MAX_PAPER_NUM"])

    st.subheader("推荐器设置")
    config["TEMPERATURE"] = st.slider("温度", min_value=0.0, max_value=2.0, value=config["TEMPERATURE"], step=0.1)
    config["NUM_WORKERS"] = st.number_input("工作线程数", min_value=1, max_value=16, value=config["NUM_WORKERS"])
    config["DESCRIPTION_PATH"] = st.text_input("研究兴趣文件路径", value=config["DESCRIPTION_PATH"])

    st.subheader("输出设置")
    config["SAVE_DIR"] = st.text_input("保存目录", value=config["SAVE_DIR"])
    config["SAVE_TO_MARKDOWN"] = st.checkbox("保存到 Markdown 文件", value=config["SAVE_TO_MARKDOWN"])

    update_button = st.form_submit_button(label='更新 .env 文件')

if update_button:
    if save_env_variables(config):
        st.sidebar.success(".env 文件更新成功！")
    else:
        st.sidebar.error("更新 .env 文件失败。")

# Main content area
st.header("控制")
if st.button('运行 `main.py` 生成摘要'):
    with st.spinner('正在运行分析... 这可能需要几分钟时间。'):
        try:
            # 确保历史记录目录存在
            os.makedirs(config["SAVE_DIR"], exist_ok=True)
            
            process = subprocess.run(['python', 'main.py'], capture_output=True, text=True, check=True, encoding='gbk')
            st.success('成功生成摘要！')
            st.code(process.stdout)
            if process.stderr:
                st.warning("脚本中的警告/错误：")
                st.code(process.stderr)
        except subprocess.CalledProcessError as e:
            st.error(f"运行脚本时发生错误：")
            st.code(e.stdout)
            st.code(e.stderr)
        except Exception as e:
            st.error(f"发生意外错误： {e}")

st.header("最新摘要")
latest_summary_file = get_latest_summary_file()
if latest_summary_file:
    st.info(f"正在显示： `{os.path.basename(latest_summary_file)}`")
    with open(latest_summary_file, 'r', encoding='utf-8') as f:
        summary_content = f.read()
    st.markdown(summary_content)
else:
    st.warning("在 `arxiv_history` 中未找到摘要文件。请运行脚本生成一个。")