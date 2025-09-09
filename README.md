<h1 align="center">arXiv Daily Article Summary</h1>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?logo=python" alt="Python Version">
  <img src="https://img.shields.io/badge/License-Apache--2.0-blue" alt="License">
</p>

<p align="center">
  一个智能的 arXiv 论文总结工具，每日自动为您筛选、总结和推荐符合您研究兴趣的最新论文。
</p>

<p align="center">
  <a href="./README.md">中文</a> | <a href="./README_EN.md">English</a>
</p>

---

## 📚 目录导航

- [✨ 核心功能](#-核心功能) - 了解项目解决的核心问题
- [⚡ 快速开始](#-快速开始) - 一键启动，快速体验
- [💻 界面预览](#-界面预览) - 查看系统界面截图
- [⚙️ 使用方法](#️-使用方法) - 详细操作指南
- [🤝 贡献与支持](#-贡献与支持) - 如何参与项目

---

## ✨ 核心功能

### 智能推荐引擎

- **个性化匹配**：基于您的研究兴趣和关键词进行精准论文筛选
- **AI 深度分析**：通义千问模型驱动的论文摘要和核心观点提取
- **多维度评估**：从相关性、创新性、实用性等角度综合评分

### 自动化工作流

- **一键启动**：`python start.py` 即可完成所有配置和启动
- **智能环境管理**：自动检测和配置 Python 环境、依赖包
- **Web 界面**：Streamlit 驱动的直观操作界面

### 多样化输出

- **实时推荐**：Web 界面实时查看推荐结果
- **历史存档**：自动保存每日推荐记录到 `arxiv_history` 目录
- **格式丰富**：支持 Markdown、HTML 等多种输出格式

### 报告生成效果

<p align="left">
  <a href="./arxiv_history/2025-08-23_ARXIV_summary.md">
    <img src="https://img.shields.io/badge/阅读报告-Markdown-blue?style=for-the-badge&logo=markdown" alt="Markdown Report">
  </a>
  <a href="./arxiv_history/2025-08-23_ARXIV_summary.html">
    <img src="https://img.shields.io/badge/在线预览-HTML-orange?style=for-the-badge&logo=html5" alt="HTML Report">
  </a>
</p>

## ⚡ 快速开始

```bash
# 1. 克隆项目到本地
git clone https://github.com/WhitePlusMS/arXiv-Daily-Summary.git

# 2. 进入项目目录
cd arXiv-Daily-Summary

# 3. 推荐使用 uv 安装依赖 (如果尚未安装)
pip install uv

# 4. 使用 uv 创建虚拟环境
uv venv

# 5. 激活虚拟环境 (Windows)
.venv\Scripts\activate

# 6. 使用 uv 安装项目依赖（在uv环境启动状态下）
pip install -r requirements.txt

# 7. 复制环境变量配置文件
copy .env.example .env

# 8. 编辑 .env 文件，填入您的 API 密钥 (重要！)
#    请手动打开 .env 文件并填入 DASHSCOPE_API_KEY
#    您可以从通义千问获取 API 密钥：https://console.aliyun.com/dashscope

# 9. 启动应用程序！
python start.py

# 10. 访问 Web 界面
#    打开浏览器，访问 http://localhost:8501
#    您可以在界面中配置研究兴趣、调整参数，查看实时推荐结果

# enjoy it!
```

系统会自动处理环境配置、依赖安装和服务启动。

## 💻 界面预览

**主界面 - 论文推荐和摘要生成**

<img src="assets/主界面.png" alt="主界面" width="800">

**分类匹配界面 - 配置研究兴趣**

<img src="assets/分类匹配界面.png" alt="分类匹配界面" width="800">

**环境配置界面 - 系统设置**

<img src="assets/环境配置界面.png" alt="环境配置界面" width="800">

**附录界面 - 分类浏览器**

<img src="assets/附录界面.png" alt="附录界面" width="800">

### 工作流程

1. **论文获取**：从 arXiv API 获取指定分类的最新论文
2. **智能筛选**：基于用户兴趣进行相关性匹配
3. **AI 分析**：使用通义千问模型生成论文摘要和评分
4. **结果展示**：在 Web 界面展示推荐结果
5. **历史存档**：自动保存推荐记录到本地文件

## ⚙️ 使用方法

### 1. 用户创建

“用户创建”的核心是为每个用户建立一个精准的 ArXiv 分类画像，通过 **分类匹配器** 界面完成，它允许用户通过自然语言描述自己的研究兴趣，系统会自动将其与 ArXiv 的官方分类进行匹配，并将最相关的分类保存到该用户的配置中。

**操作流程：**

1. **访问分类匹配器**：在左侧导航栏点击“分类匹配器”。
2. **输入信息**：
    - **用户名**：输入您的用户名，用于唯一标识和保存您的匹配结果。
    - **研究内容描述**：在文本框中详细描述您的研究方向、兴趣领域、关键词等。例如：

        ```
        我主要关注使用大型语言模型（LLM）进行检索增强生成（RAG）的技术，特别是如何优化其在多模态数据上的表现。
        ```

3. **开始匹配**：点击“开始匹配”按钮。
4. **自动匹配与保存**：
    - 系统后台会调用大语言模型，将您输入的自然语言描述与 `data/users/arxiv_categories.json` 中定义的官方 ArXiv 分类进行语义相似度计算。
    - 系统会返回一个按匹配评分从高到低排序的分类列表。
    - 这些评分最高的分类结果将自动保存到 `data/users/user_categories.json` 文件中，与您的用户名关联，完成用户画像的创建。

**数据管理：**

页面下方提供了对已创建用户数据的全面管理功能：

- **查看与搜索**：可以浏览所有用户的匹配记录，并按用户名或研究内容进行搜索。
- **编辑**：可以修改用户的研究内容描述，并重新进行匹配。
- **删除**：可以删除单个或批量的用户记录。
- **导出**：支持将用户数据导出为 JSON 文件。

### 2. 每日论文推荐

在创建完用户画像后，主界面 **ArXiv 每日论文推荐系统** 提供了核心的论文推荐功能。它会根据选定用户的画像，自动从 ArXiv 拉取、筛选并分析最新的相关论文。

**操作流程：**

1.  **选择用户配置**：在顶部的下拉菜单中，选择一个您在“分类匹配器”中创建的用户。
    *   系统会自动加载该用户的配置，包括其匹配的 **分类标签** 和 **研究兴趣**。
2.  **开始推荐**：点击“开始推荐论文”按钮。
3.  **监控与查看结果**：
    *   系统启动后，下方会显示 **实时运行日志**，您可以清晰地看到每一步的执行状态，例如“获取论文”、“分析论文”、“生成报告”等。
    *   运行成功后，推荐结果会以标签页的形式展示，包括 **摘要内容**、**详细分析** 和 **简要分析**。
    *   同时，系统会生成完整的 `HTML` 和 `Markdown` 格式报告，您可以直接在网页上预览或下载到本地。

## 🤝 贡献与支持

**贡献代码**

```bash
# 1. Fork 本项目
在 GitHub 页面点击 "Fork" 按钮复制项目到您的账号

# 2. 克隆到本地
git clone https://github.com/YOUR_USERNAME/arXiv-Daily-Summary.git
cd arXiv-Daily-Summary

# 3. 创建功能分支
git checkout -b feature/your-feature

# 4. 开发并提交更改
git add .
git commit -m "feat: 添加新功能描述"

# 5. 推送到远程
git push origin feature/your-feature

# 6. 创建 Pull Request
在 GitHub 页面创建 PR，详细描述您的改动
```

**问题反馈**

- 发现 Bug？请提交 [Issue](https://github.com/your-repo/issues)
- 有新想法？欢迎讨论和建议
- 觉得有用？请给项目点个 Star

## 📄 许可证

本项目采用 [Apache 2.0 许可证](LICENSE)

## 🙏 致谢

- 感谢 [arxiv Python包](https://pypi.org/project/arxiv/) 的作者，它提供了非常便捷的论文下载功能。
- 本项目的灵感来源于以下优秀的开源项目，感谢它们的作者：
  - [TideDra/zotero-arxiv-daily](https://github.com/TideDra/zotero-arxiv-daily)
  - [Vincentqyw/cv-arxiv-daily](https://github.com/Vincentqyw/cv-arxiv-daily)
  - [AutoLLM/ArxivDigest](https://github.com/AutoLLM/ArxivDigest)

---

<p align="center">
  <strong>让 AI 帮您从信息海洋中发现真正有价值的研究</strong>
</p>
