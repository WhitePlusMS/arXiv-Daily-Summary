<h1 align="center">arXiv Daily Summary</h1>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?logo=python" alt="Python Version">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/Status-Active-brightgreen" alt="Status">
</p>

<p align="center">
  一个智能的 arXiv 论文总结工具，每日自动为您筛选、总结和推荐符合您研究兴趣的最新论文。
</p>

---

## 📚 目录 📚

- [📚 目录 📚](#-目录-)
- [✨ 核心功能](#-核心功能)
- [🚀 开始使用](#-开始使用)
  - [1. 先决条件](#1-先决条件)
  - [2. 安装](#2-安装)
  - [3. 环境设置](#3-环境设置)
  - [4. 配置](#4-配置)
- [🏃‍♂️ 使用方法](#️-使用方法)
- [🤝 贡献](#-贡献)
- [📄 许可证](#-许可证)
- [🌟 Star History](#-star-history)
- [🙏 致谢](#-致谢)

---

**Arxiv Curator** 是一个自动化工具，旨在解决科研人员信息过载的问题。它通过结合强大的 AI 模型和您定制化的研究兴趣，每天自动从 arXiv.org 获取最新论文，进行智能筛选和深度总结，最后将一份精心组织的摘要报告发送到您的邮箱。

## ✨ 核心功能

- **个性化推荐**: 完全根据您在 `personal_research_interests.md` 中定义的关键词和领域进行论文筛选。
- **AI 驱动的总结**: 利用大型语言模型（如 GPT）对论文摘要进行提炼，生成更精炼、易于理解的核心观点总结。
- **自动化工作流**: 设置一次后，即可每日自动运行，无需人工干预。
- **邮件直达**: 将每日的论文摘要报告直接发送到您的指定邮箱，方便随时查阅。
- **历史存档**: 所有生成的摘要报告都会保存在 `arxiv_history` 目录中，方便回顾。

## 🚀 开始使用

请按照以下步骤在您自己的机器上部署和运行 arXiv Daily Summary。

### 1. 先决条件

- Python 3.9 或更高版本
- Git

### 2. 安装

首先，克隆本仓库到您的本地机器：
```bash
git clone https://github.com/your-username/arxiv-curator.git
cd arxiv-curator
```

### 3. 环境设置

我们强烈建议使用虚拟环境来管理项目依赖。

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

安装所需的 Python 包：
```bash
pip install -r req.txt
```

### 4. 配置

项目的所有配置都通过环境变量和 `personal_research_interests.md` 文件管理。

**a. 设置环境变量**

复制 `.env.example` 文件并重命名为 `.env`：
```bash
# Windows
copy .env.example .env
# macOS / Linux
cp .env.example .env
```

然后，编辑 `.env` 文件，填入您的个人信息：
```plaintext
# .env
# 用于调用 AI 模型的 API Key (例如 OpenAI)
OPENAI_API_KEY="sk-..."
OPENAI_API_BASE="https://api.openai.com/v1" # 如果使用代理，请修改

# 邮件发送配置 (以 QQ 邮箱为例)
EMAIL_HOST="smtp.qq.com"
EMAIL_PORT=465
EMAIL_HOST_USER="your_email@qq.com"
EMAIL_HOST_PASSWORD="your_email_password" # 注意：通常是授权码，而不是登录密码
EMAIL_USE_SSL=true

# 邮件接收人
RECIPIENT_EMAIL="recipient_email@example.com"
```

**b. 定义您的研究兴趣**

打开 `personal_research_interests.md` 文件，按照其中的格式定义您感兴趣的领域和关键词。AI 将使用这些信息来为您筛选论文。

```markdown
- **Computer Science**:
  - "Large Language Models"
  - "Reinforcement Learning"
  - "Graph Neural Networks"
- **Physics**:
  - "Quantum Computing"
```

## 🏃‍♂️ 使用方法

完成所有配置后，您可以手动运行主脚本来测试：

```bash
python main.py
```

脚本成功运行后，您应该会在邮箱中收到一封摘要邮件，并在 `arxiv_history` 目录中看到一个新生成的 Markdown 文件。

## 🤝 贡献

欢迎任何形式的贡献！如果您有好的想法或发现了 Bug，请随时提出 Issue 或提交 Pull Request。

1. Fork 本仓库
2. 创建您的新分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开一个 Pull Request

## 📄 许可证

本项目采用 MIT 许可证。详情请见 `LICENSE` 文件。

---

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=YOUR_USERNAME/YOUR_REPONAME&type=Date)](https://star-history.com/#YOUR_USERNAME/YOUR_REPONAME&Date)

---

## 🙏 致谢

- 感谢 [arxiv Python包](https://pypi.org/project/arxiv/) 的作者，它提供了非常便捷的论文下载功能。
- 本项目的灵感来源于以下优秀的开源项目，感谢它们的作者：
  - [TideDra/zotero-arxiv-daily](https://github.com/TideDra/zotero-arxiv-daily)
  - [Vincentqyw/cv-arxiv-daily](https://github.com/Vincentqyw/cv-arxiv-daily)
  - [AutoLLM/ArxivDigest](https://github.com/AutoLLM/ArxivDigest)
