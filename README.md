<h1 align="center">arXiv Daily Article Summary</h1>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?logo=python" alt="Python Version">
  <img src="https://img.shields.io/badge/FastAPI-0.100%2B-green?logo=fastapi" alt="FastAPI">
  <img src="https://img.shields.io/badge/Vue.js-3.5%2B-green?logo=vue.js" alt="Vue.js">
  <img src="https://img.shields.io/badge/License-Apache--2.0-blue" alt="License">
  <a href="https://deepwiki.com/WhitePlusMS/arXiv-Daily-Summary"><img src="https://deepwiki.com/badge.svg" alt="Ask DeepWiki"></a>
</p>

<p align="center">
  一个智能的 arXiv 论文总结工具，每日自动为您筛选、总结和推荐符合您研究兴趣的最新论文。
</p>

<p align="center">
  <a href="./README.md">中文</a> | <a href="./README_EN.md">English</a>
</p>

---

## 📚 目录导航

- [🏗️ 系统架构](#️-系统架构) - 了解项目技术架构
- [✨ 核心功能](#-核心功能) - 了解项目解决的核心问题
- [⚡ 快速开始](#-快速开始) - 一键启动，快速体验
- [💻 界面预览](#-界面预览) - 查看系统界面截图
- [⚙️ 使用方法](#️-使用方法) - 详细操作指南
- [🔧 故障排查](#-故障排查) - 常见问题与解决方案
- [🤝 贡献与支持](#-贡献与支持) - 如何参与项目

---

## 🏗️ 系统架构

### 技术栈

- **后端**: FastAPI + Python 3.10+
- **前端**: Vue 3 + TypeScript + Vite
- **AI 模型**: 通义千问 (DashScope API)
- **数据存储**: JSON 文件 + 本地文件系统
- **部署**: 支持本地开发和生产部署

### 架构设计

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Vue3 前端     │    │  FastAPI 后端   │    │   核心服务层    │
│                 │    │                 │    │                 │
│ • 用户界面      │◄──►│ • RESTful API   │◄──►│ • 论文获取      │
│ • 状态管理      │    │ • 数据验证      │    │ • 智能匹配      │
│ • 路由管理      │    │ • 业务逻辑      │    │ • AI 分析       │
│ • 组件化开发    │    │ • 异步处理      │    │ • 报告生成      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 模块组织

- **`fastapi_services/`**: FastAPI 后端服务
  - `fastapi_app.py`: 主应用入口和 API 路由
  - `models.py`: 数据模型定义
  - `service_container.py`: 依赖注入容器
  - 各种业务服务模块

- **`web/`**: Vue3 前端应用
  - 基于 Vite 构建工具
  - TypeScript 支持
  - 组件化开发

- **`core/`**: 核心业务逻辑
  - `arxiv_fetcher.py`: ArXiv 论文获取器
  - `recommendation_engine.py`: 推荐引擎（论文筛选、评分、分析）
  - `category_matcher.py`: 分类匹配器（研究兴趣与 ArXiv 分类匹配）
  - `llm_provider.py`: LLM 模型提供者（支持通义千问、OpenAI 兼容接口）
  - `pdf_text_extractor.py`: PDF 文本提取器
  - `prompt_manager.py`: 提示词管理器（统一管理 AI 提示词模板）
  - `output_manager.py`: 输出管理器（报告生成、邮件发送）
  - `email_sender.py`: 邮件发送器（支持 SMTP/SSL/TLS）
  - `template_renderer.py`: 模板渲染器（Jinja2 模板引擎）

- **`config/`**: 配置文件目录
  - `prompts.default.json`: 默认提示词模板
  - `prompts.json`: 用户自定义提示词（覆盖默认值）
  - `arxiv_categories.json`: ArXiv 分类定义
  - `templates/`: Jinja2 报告模板

## ✨ 核心功能

### 智能推荐引擎

- **个性化匹配**：基于您的研究兴趣和关键词进行精准论文筛选
- **AI 深度分析**：通义千问模型驱动的论文摘要和核心观点提取
- **多维度评估**：从相关性、创新性、实用性等角度综合评分

### 现代化 Web 界面

- **响应式设计**：基于 Vue3 的现代化用户界面
- **实时交互**：FastAPI 提供的高性能 API 支持
- **组件化开发**：可复用的 UI 组件和清晰的代码结构

### 多样化输出

- **实时推荐**：Web 界面实时查看推荐结果
- **历史存档**：自动保存每日推荐记录到 `arxiv_history` 目录
- **格式丰富**：支持 Markdown、HTML 等多种输出格式

### 智能提示词管理

- **模板化设计**：所有 AI 提示词采用模板化设计，支持变量替换
- **灵活定制**：可在 Web 界面或配置文件中自定义提示词，覆盖默认值
- **版本管理**：默认提示词与用户自定义提示词分离管理，支持一键重置

### 双模型策略

- **主模型（Heavy Model）**：用于详细分析和深度理解，如 `qwen-plus`
- **轻量模型（Light Model）**：用于快速筛选和初步评估，如 `qwen-turbo`
- **智能调度**：系统根据任务复杂度自动选择合适的模型，平衡速度与质量

### 进度追踪与实时反馈

- **任务进度**：支持长时间运行任务的实时进度追踪
- **WebSocket 支持**：前端可实时获取后端任务执行状态
- **详细日志**：完整的运行日志记录，便于问题排查

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

### 环境要求

- **Python**: 3.10 或更高版本
- **Node.js**: 20.19.0 或更高版本
- **包管理器**: 推荐使用 uv (Python) 和 npm (Node.js)

### 一键启动 (推荐)

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

# 9. 启动 FastAPI + Vue3 应用程序！
python start_fastapi.py

# 10. 访问应用
#    前端界面: http://localhost:5173
#    后端 API: http://localhost:8000
#    API 文档: http://localhost:8000/docs

# enjoy it!
```

### 传统 Streamlit 界面

如果您更喜欢使用 Streamlit 界面：

```bash
# 进入 streamlit_ui 目录
cd streamlit_ui

# 启动 Streamlit 应用
python start.py
```

系统会自动处理环境配置、依赖安装和服务启动。

### Docker 一键部署（推荐生产环境）

使用 Docker Compose 可以快速部署整个系统，无需手动配置环境：

```bash
# 1. 克隆项目到本地
git clone https://github.com/WhitePlusMS/arXiv-Daily-Summary.git
cd arXiv-Daily-Summary

# 2. 进入 docker 目录
cd docker

# 3. 启动服务（首次启动会从 Docker Hub 拉取镜像）
docker compose up -d

# 4. 查看服务状态
docker compose ps

# 5. 访问应用
#    前端界面: http://localhost:5173
#    后端 API: http://localhost:8000
#    API 文档: http://localhost:8000/docs
```

**配置 API 密钥：**

1. 首次启动后，系统会自动从 `.env.example` 创建 `.env` 文件
2. 访问前端界面：http://localhost:5173
3. 在左侧导航栏点击"环境配置"
4. 在"🤖 模型与API配置"分组中，填入您的 `DASHSCOPE_API_KEY`
5. 点击"💾 保存配置"按钮

**停止服务：**

```bash
# 停止服务
docker compose down

# 停止服务并删除数据卷（谨慎使用）
docker compose down -v
```

**数据持久化：**

所有数据（包括 `.env` 配置、历史记录、用户数据、日志）都保存在 Docker Volume 中，即使删除容器也不会丢失数据。

**注意事项：**

- 首次启动会从 Docker Hub 拉取镜像，可能需要几分钟时间（取决于网络速度）
- 默认端口：前端 5173，后端 8000
- 确保配置的端口未被占用
- 修改端口后，访问地址会相应变化（例如：http://localhost:8080）

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

### 模型参数配置（Qwen/OpenAI 兼容）

- 位置：编辑项目根目录下的 `.env` 文件中的 Qwen 参数段。
- 支持参数：
  - 基本采样：`QWEN_MODEL_TEMPERATURE`, `QWEN_MODEL_TOP_P`, `QWEN_MODEL_MAX_TOKENS`
  - 采样增强：`QWEN_MODEL_TOP_K`
  - 重复惩罚：`QWEN_MODEL_REPETITION_PENALTY`
  - 随机种子：`QWEN_MODEL_SEED`
  - 停止词：`QWEN_MODEL_STOPS`（JSON 数组或用 `||` 分隔）
  - 工具调用：`QWEN_MODEL_TOOL_CHOICE`（`auto`/`none`/`required`）
  - 响应格式：`QWEN_MODEL_RESPONSE_FORMAT`（`text`/`json_object`）
  - 思考过程：`QWEN_MODEL_ENABLE_THINKING`（Qwen3 专属）
  - 概率输出：`QWEN_MODEL_LOGPROBS`, `QWEN_MODEL_TOP_LOGPROBS`
  - 其他罚则：`QWEN_MODEL_PRESENCE_PENALTY`, `QWEN_MODEL_FREQUENCY_PENALTY`
  - DashScope 特性：`QWEN_MODEL_ENABLE_SEARCH`, `QWEN_MODEL_THINKING_BUDGET`, `QWEN_MODEL_INCREMENTAL_OUTPUT`

示例（.env）：

```
QWEN_MODEL=qwen-plus
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
DASHSCOPE_API_KEY=YOUR_KEY
QWEN_MODEL_TEMPERATURE=0.7
QWEN_MODEL_TOP_P=0.9
QWEN_MODEL_MAX_TOKENS=4000
QWEN_MODEL_TOP_K=50
QWEN_MODEL_REPETITION_PENALTY=1.05
QWEN_MODEL_SEED=42
QWEN_MODEL_STOPS=["END"]
QWEN_MODEL_TOOL_CHOICE=auto
QWEN_MODEL_RESPONSE_FORMAT=json_object
QWEN_MODEL_ENABLE_THINKING=false
QWEN_MODEL_LOGPROBS=false
QWEN_MODEL_TOP_LOGPROBS=0
```

说明：
- 未填写的参数会使用代码中的合理默认或不启用（None）。
- 轻量模型（`QWEN_MODEL_LIGHT_*`）支持同样的参数命名（在 `.env.example` 中已列出）。
- 所有扩展参数通过 OpenAI 兼容接口调用；DashScope 专属参数通过 `extra_body` 传递，保持兼容。

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
    - 系统后台会调用大语言模型，将您输入的自然语言描述与 `config/arxiv_categories.json` 中定义的官方 ArXiv 分类进行语义相似度计算。
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

1. **选择用户配置**：在顶部的下拉菜单中，选择一个您在"分类匹配器"中创建的用户。
    - 系统会自动加载该用户的配置，包括其匹配的 **分类标签** 和 **研究兴趣**。
2. **调整推荐参数**（可选）：
    - **最大论文数**：每个分类获取的最大论文数量
    - **详细分析数**：需要进行详细分析的论文数量
    - **简要分析数**：需要进行简要分析的论文数量
    - **相关性阈值**：论文相关性评分的最低阈值（0-100）
3. **开始推荐**：点击"开始推荐论文"按钮。
4. **监控与查看结果**：
    - 系统启动后，下方会显示 **实时运行日志**，您可以清晰地看到每一步的执行状态，例如"获取论文"、"分析论文"、"生成报告"等。
    - 运行成功后，推荐结果会以标签页的形式展示，包括 **摘要内容**、**详细分析** 和 **简要分析**。
    - 同时，系统会生成完整的 `HTML` 和 `Markdown` 格式报告，您可以直接在网页上预览或下载到本地。
    - 报告会自动保存到 `arxiv_history` 目录，文件名格式为 `YYYY-MM-DD_用户名_ARXIV_summary.{html|md}`

### 3. 环境配置管理

**环境配置界面**提供了系统参数的集中管理功能，包括：

**模型与 API 配置：**
- 主模型和轻量模型选择
- API 密钥和基础 URL 配置
- 模型参数调优（温度、top_p、最大 token 数等）

**ArXiv 配置：**
- ArXiv API 基础 URL 和重试策略
- 论文获取数量限制
- 相关性筛选阈值

**邮件配置：**
- 启用/禁用邮件发送功能
- SMTP 服务器配置（支持 SSL/TLS）
- 发件人和收件人设置

**时区与日志配置：**
- 时区设置（影响报告中的时间显示）
- 日志输出级别和文件管理

**操作说明：**
1. 在左侧导航栏点击"环境配置"
2. 选择要修改的配置分组
3. 修改配置值后点击"保存更改"
4. 支持分组重置和全局重置功能

### 4. 提示词管理

系统支持自定义 AI 提示词模板，您可以根据需要调整论文分析的风格和深度。

**提示词类型：**
- **分类匹配提示词**：用于将用户研究兴趣匹配到 ArXiv 分类
- **相关性评估提示词**：用于评估论文与用户兴趣的相关性
- **详细分析提示词**：用于生成论文的详细分析报告
- **简要分析提示词**：用于生成论文的简要分析报告

**操作说明：**
1. 在"环境配置"界面找到"提示词管理"部分
2. 选择要修改的提示词模板
3. 编辑提示词内容（支持变量占位符，如 `{description}`、`{paper_title}` 等）
4. 点击"保存"应用更改
5. 支持"重置为默认"功能，一键恢复默认提示词

**提示词变量说明：**
- `{description}`: 用户研究兴趣描述
- `{paper_title}`: 论文标题
- `{paper_abstract}`: 论文摘要
- `{paper_authors}`: 论文作者列表
- `{paper_categories}`: 论文分类标签
- 更多变量请参考提示词模板中的注释

## 🔧 故障排查

### 常见问题

**1. 启动失败：虚拟环境未激活**

```
错误：VIRTUAL_ENV环境变量未设置！
解决：请先激活虚拟环境
Windows: .venv\Scripts\activate
Linux/Mac: source .venv/bin/activate
```

**2. API 调用失败：401 或 403 错误**

```
错误：API 认证失败
解决：
1. 检查 .env 文件中的 DASHSCOPE_API_KEY 是否正确
2. 确认 API 密钥是否有效且未过期
3. 检查 API 密钥对应的账户是否有足够的余额
```

**3. 前端无法连接后端**

```
错误：CORS 错误或连接失败
解决：
1. 确认后端服务已启动（http://localhost:8000）
2. 检查前端端口是否与后端 CORS 配置匹配
3. 查看浏览器控制台的错误信息
```

**4. 论文获取失败：网络超时**

```
错误：ArXiv API 请求超时
解决：
1. 检查网络连接
2. 在环境配置中增加 ARXIV_RETRIES（重试次数）
3. 增加 ARXIV_DELAY（请求间隔，避免频率过高）
```

**5. 提示词模板错误**

```
错误：模板变量缺失或格式错误
解决：
1. 检查提示词中的变量名是否正确
2. 确认变量占位符格式为 {variable_name}
3. 查看日志中的详细错误信息
4. 尝试重置为默认提示词
```

### 日志查看

系统日志保存在 `logs/` 目录下：

```bash
# 查看最新日志
tail -f logs/fastapi.log

# 查看错误日志
grep ERROR logs/fastapi.log
```

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
