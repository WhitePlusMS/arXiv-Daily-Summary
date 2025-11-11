<h1 align="center">arXiv Daily Article Summary</h1>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?logo=python" alt="Python Version">
  <img src="https://img.shields.io/badge/FastAPI-0.100%2B-green?logo=fastapi" alt="FastAPI">
  <img src="https://img.shields.io/badge/Vue.js-3.5%2B-green?logo=vue.js" alt="Vue.js">
  <img src="https://img.shields.io/badge/License-Apache--2.0-blue" alt="License">
</p>

<p align="center">
  An intelligent arXiv paper summarization tool that automatically filters, summarizes, and recommends the latest papers matching your research interests daily.
</p>

<p align="center">
  <a href="./README.md">🇨🇳 中文</a> | <a href="./README_EN.md">🇺🇸 English</a>
</p>

---

## 📚 Table of Contents

- [🏗️ System Architecture](#️-system-architecture) - Understand the project's technical architecture
- [✨ Core Features](#-core-features) - Understand the core problems this project solves
- [⚡ Quick Start](#-quick-start) - One-click startup for quick experience
- [💻 Interface Preview](#-interface-preview) - View system interface screenshots
- [⚙️ Usage Guide](#️-usage-guide) - Detailed operation instructions
- [🔧 Troubleshooting](#-troubleshooting) - Common issues and solutions
- [🤝 Contributing & Support](#-contributing--support) - How to participate in the project

---

## 🏗️ System Architecture

### Tech Stack

- **Backend**: FastAPI + Python 3.10+
- **Frontend**: Vue 3 + TypeScript + Vite
- **AI Model**: Qwen (DashScope API)
- **Data Storage**: JSON files + local file system
- **Deployment**: Supports local development and production deployment

### Architecture Design

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Vue3 Frontend │    │  FastAPI Backend │    │  Core Services │
│                 │    │                 │    │                 │
│ • User Interface│◄──►│ • RESTful API   │◄──►│ • Paper Fetch   │
│ • State Mgmt    │    │ • Data Validation│    │ • Smart Match   │
│ • Route Mgmt    │    │ • Business Logic│    │ • AI Analysis   │
│ • Components    │    │ • Async Process │    │ • Report Gen    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Module Organization

- **`fastapi_services/`**: FastAPI backend services
  - `fastapi_app.py`: Main application entry and API routes
  - `models.py`: Data model definitions
  - `service_container.py`: Dependency injection container
  - Various business service modules

- **`web/`**: Vue3 frontend application
  - Built with Vite
  - TypeScript support
  - Component-based development

- **`core/`**: Core business logic
  - `arxiv_fetcher.py`: ArXiv paper fetcher
  - `recommendation_engine.py`: Recommendation engine (paper filtering, scoring, analysis)
  - `category_matcher.py`: Category matcher (matches research interests with ArXiv categories)
  - `llm_provider.py`: LLM model provider (supports Qwen, OpenAI-compatible interfaces)
  - `pdf_text_extractor.py`: PDF text extractor
  - `prompt_manager.py`: Prompt manager (unified management of AI prompt templates)
  - `output_manager.py`: Output manager (report generation, email sending)
  - `email_sender.py`: Email sender (supports SMTP/SSL/TLS)
  - `template_renderer.py`: Template renderer (Jinja2 template engine)

- **`config/`**: Configuration directory
  - `prompts.default.json`: Default prompt templates
  - `prompts.json`: User custom prompts (overrides default values)
  - `arxiv_categories.json`: ArXiv category definitions
  - `templates/`: Jinja2 report templates

## ✨ Core Features

### Intelligent Recommendation Engine

- **Personalized Matching**: Precise paper filtering based on your research interests and keywords
- **AI Deep Analysis**: Paper abstracts and key insights extraction powered by Qwen models
- **Multi-dimensional Evaluation**: Comprehensive scoring from relevance, innovation, and practicality perspectives

### Modern Web Interface

- **Responsive Design**: Modern user interface based on Vue3
- **Real-time Interaction**: High-performance API support provided by FastAPI
- **Component-based Development**: Reusable UI components and clear code structure

### Diverse Output

- **Real-time Recommendations**: View recommendation results in real-time through web interface
- **Historical Archive**: Automatically save daily recommendation records to `arxiv_history` directory
- **Rich Formats**: Support multiple output formats including Markdown, HTML, etc.

### Intelligent Prompt Management

- **Template-based Design**: All AI prompts use template-based design with variable substitution support
- **Flexible Customization**: Customize prompts in web interface or configuration files, overriding default values
- **Version Management**: Separate management of default prompts and user custom prompts, with one-click reset support

### Dual Model Strategy

- **Heavy Model**: Used for detailed analysis and deep understanding, such as `qwen-plus`
- **Light Model**: Used for quick filtering and preliminary evaluation, such as `qwen-turbo`
- **Smart Scheduling**: System automatically selects appropriate model based on task complexity, balancing speed and quality

### Progress Tracking & Real-time Feedback

- **Task Progress**: Support real-time progress tracking for long-running tasks
- **WebSocket Support**: Frontend can get real-time backend task execution status
- **Detailed Logging**: Complete runtime log records for easy troubleshooting

### Report Generation Results

<p align="left">
  <a href="./arxiv_history/2025-08-23_ARXIV_summary.md">
    <img src="https://img.shields.io/badge/Read%20Report-Markdown-blue?style=for-the-badge&logo=markdown" alt="Markdown Report">
  </a>
  <a href="./arxiv_history/2025-08-23_ARXIV_summary.html">
    <img src="https://img.shields.io/badge/Online%20Preview-HTML-orange?style=for-the-badge&logo=html5" alt="HTML Report">
  </a>
</p>

## ⚡ Quick Start

### Environment Requirements

- **Python**: 3.10 or higher
- **Node.js**: 20.19.0 or higher
- **Package Managers**: Recommended to use uv (Python) and npm (Node.js)

### One-click Startup (Recommended)

```bash
# 1. Clone the project locally
git clone https://github.com/WhitePlusMS/arXiv-Daily-Summary.git

# 2. Enter project directory
cd arXiv-Daily-Summary

# 3. Recommended to use uv for dependency installation (if not installed yet)
pip install uv

# 4. Create virtual environment using uv
uv venv

# 5. Activate virtual environment (Windows)
.venv\Scripts\activate

# 6. Install project dependencies using uv (with uv environment activated)
pip install -r requirements.txt

# 7. Copy environment variable configuration file
copy .env.example .env

# 8. Edit .env file and fill in your API key (Important!)
#    Please manually open .env file and fill in DASHSCOPE_API_KEY
#    You can get API key from Qwen: https://console.aliyun.com/dashscope

# 9. Start FastAPI + Vue3 application!
python start_fastapi.py

# 10. Access application
#     Frontend: http://localhost:5173
#     Backend API: http://localhost:8000
#     API Documentation: http://localhost:8000/docs

# enjoy it!
```

### Traditional Streamlit Interface

If you prefer using the Streamlit interface:

```bash
# Enter streamlit_ui directory
cd streamlit_ui

# Start Streamlit application
python start.py
```

The system will automatically handle environment configuration, dependency installation, and service startup.

## 💻 Interface Preview

**Main Interface - Paper Recommendation and Summary Generation**

<img src="assets/主界面.png" alt="Main Interface" width="800">

**Category Matcher Interface - Configure Research Interests**

<img src="assets/分类匹配界面.png" alt="Category Matcher Interface" width="800">

**Environment Configuration Interface - System Settings**

<img src="assets/环境配置界面.png" alt="Environment Configuration Interface" width="800">

**Appendix Interface - Category Browser**

<img src="assets/附录界面.png" alt="Appendix Interface" width="800">

### Workflow

1. **Paper Retrieval**: Fetch latest papers from arXiv API for specified categories
2. **Intelligent Filtering**: Relevance matching based on user interests
3. **AI Analysis**: Generate paper summaries and scores using Qwen models
4. **Result Display**: Show recommendation results in web interface
5. **Historical Archive**: Automatically save recommendation records to local files

### Model Parameter Configuration (Qwen/OpenAI Compatible)

- **Location**: Edit the Qwen parameter section in the `.env` file in the project root directory.
- **Supported Parameters**:
  - Basic Sampling: `QWEN_MODEL_TEMPERATURE`, `QWEN_MODEL_TOP_P`, `QWEN_MODEL_MAX_TOKENS`
  - Sampling Enhancement: `QWEN_MODEL_TOP_K`
  - Repetition Penalty: `QWEN_MODEL_REPETITION_PENALTY`
  - Random Seed: `QWEN_MODEL_SEED`
  - Stop Words: `QWEN_MODEL_STOPS` (JSON array or separated by `||`)
  - Tool Choice: `QWEN_MODEL_TOOL_CHOICE` (`auto`/`none`/`required`)
  - Response Format: `QWEN_MODEL_RESPONSE_FORMAT` (`text`/`json_object`)
  - Thinking Process: `QWEN_MODEL_ENABLE_THINKING` (Qwen3 exclusive)
  - Probability Output: `QWEN_MODEL_LOGPROBS`, `QWEN_MODEL_TOP_LOGPROBS`
  - Other Penalties: `QWEN_MODEL_PRESENCE_PENALTY`, `QWEN_MODEL_FREQUENCY_PENALTY`
  - DashScope Features: `QWEN_MODEL_ENABLE_SEARCH`, `QWEN_MODEL_THINKING_BUDGET`, `QWEN_MODEL_INCREMENTAL_OUTPUT`

Example (.env):

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

Notes:
- Unfilled parameters will use reasonable defaults from code or remain disabled (None).
- Light models (`QWEN_MODEL_LIGHT_*`) support the same parameter naming (listed in `.env.example`).
- All extended parameters are called through OpenAI-compatible interface; DashScope-specific parameters are passed through `extra_body` for compatibility.

## ⚙️ Usage Guide

### 1. User Creation

The core of "User Creation" is to establish a precise ArXiv category profile for each user through the **Category Matcher** interface. It allows users to describe their research interests in natural language, and the system automatically matches them with official ArXiv categories, saving the most relevant categories to the user's configuration.

**Operation Process:**

1. **Access Category Matcher**: Click "Category Matcher" in the left navigation bar.
2. **Input Information**:
    - **Username**: Enter your username for unique identification and saving your matching results.
    - **Research Content Description**: Describe your research directions, interest areas, keywords, etc. in detail in the text box. For example:

        ```
        I mainly focus on using Large Language Models (LLM) for Retrieval-Augmented Generation (RAG) technology, especially how to optimize their performance on multimodal data.
        ```

3. **Start Matching**: Click the "Start Matching" button.
4. **Automatic Matching & Saving**:
    - The system backend calls large language models to calculate semantic similarity between your natural language description and official ArXiv categories defined in `config/arxiv_categories.json`.
    - The system returns a category list sorted by matching scores from high to low.
    - These highest-scoring category results are automatically saved to the `data/users/user_categories.json` file, associated with your username, completing user profile creation.

**Data Management:**

The bottom of the page provides comprehensive management functions for created user data:

- **View & Search**: Browse all user matching records and search by username or research content.
- **Edit**: Modify user research content descriptions and re-match.
- **Delete**: Delete individual or batch user records.
- **Export**: Support exporting user data as JSON files.

### 2. Daily Paper Recommendation

After creating user profiles, the main interface **ArXiv Daily Paper Recommendation System** provides core paper recommendation functionality. It automatically pulls, filters, and analyzes the latest relevant papers from ArXiv based on selected user profiles.

**Operation Process:**

1. **Select User Configuration**: In the top dropdown menu, select a user you created in the "Category Matcher".
    - The system automatically loads the user's configuration, including their matched **category tags** and **research interests**.
2. **Adjust Recommendation Parameters** (Optional):
    - **Max Papers**: Maximum number of papers to fetch per category
    - **Detailed Analysis Count**: Number of papers requiring detailed analysis
    - **Brief Analysis Count**: Number of papers requiring brief analysis
    - **Relevance Threshold**: Minimum threshold for paper relevance score (0-100)
3. **Start Recommendation**: Click the "Start Paper Recommendation" button.
4. **Monitor & View Results**:
    - After system startup, **real-time running logs** are displayed below, clearly showing each step's execution status, such as "Fetching Papers", "Analyzing Papers", "Generating Reports", etc.
    - After successful execution, recommendation results are displayed in tab format, including **Summary Content**, **Detailed Analysis**, and **Brief Analysis**.
    - Meanwhile, the system generates complete `HTML` and `Markdown` format reports that you can preview directly on the webpage or download locally.
    - Reports are automatically saved to the `arxiv_history` directory with filename format: `YYYY-MM-DD_username_ARXIV_summary.{html|md}`

### 3. Environment Configuration Management

The **Environment Configuration Interface** provides centralized management of system parameters, including:

**Model & API Configuration:**
- Main model and light model selection
- API key and base URL configuration
- Model parameter tuning (temperature, top_p, max tokens, etc.)

**ArXiv Configuration:**
- ArXiv API base URL and retry strategy
- Paper fetching quantity limits
- Relevance filtering threshold

**Email Configuration:**
- Enable/disable email sending functionality
- SMTP server configuration (supports SSL/TLS)
- Sender and receiver settings

**Timezone & Logging Configuration:**
- Timezone settings (affects time display in reports)
- Log output level and file management

**Operation Instructions:**
1. Click "Environment Configuration" in the left navigation bar
2. Select the configuration group to modify
3. Modify configuration values and click "Save Changes"
4. Supports group reset and global reset functionality

### 4. Prompt Management

The system supports custom AI prompt templates, allowing you to adjust the style and depth of paper analysis as needed.

**Prompt Types:**
- **Category Matching Prompt**: Used to match user research interests to ArXiv categories
- **Relevance Evaluation Prompt**: Used to evaluate the relevance between papers and user interests
- **Detailed Analysis Prompt**: Used to generate detailed analysis reports for papers
- **Brief Analysis Prompt**: Used to generate brief analysis reports for papers

**Operation Instructions:**
1. Find the "Prompt Management" section in the "Environment Configuration" interface
2. Select the prompt template to modify
3. Edit prompt content (supports variable placeholders, such as `{description}`, `{paper_title}`, etc.)
4. Click "Save" to apply changes
5. Supports "Reset to Default" functionality to restore default prompts with one click

**Prompt Variable Description:**
- `{description}`: User research interest description
- `{paper_title}`: Paper title
- `{paper_abstract}`: Paper abstract
- `{paper_authors}`: Paper author list
- `{paper_categories}`: Paper category tags
- More variables please refer to comments in prompt templates

## 🔧 Troubleshooting

### Common Issues

**1. Startup Failure: Virtual Environment Not Activated**

```
Error: VIRTUAL_ENV environment variable not set!
Solution: Please activate virtual environment first
Windows: .venv\Scripts\activate
Linux/Mac: source .venv/bin/activate
```

**2. API Call Failure: 401 or 403 Error**

```
Error: API authentication failed
Solution:
1. Check if DASHSCOPE_API_KEY in .env file is correct
2. Confirm if API key is valid and not expired
3. Check if the account corresponding to API key has sufficient balance
```

**3. Frontend Cannot Connect to Backend**

```
Error: CORS error or connection failure
Solution:
1. Confirm backend service is started (http://localhost:8000)
2. Check if frontend port matches backend CORS configuration
3. Check browser console error messages
```

**4. Paper Fetching Failure: Network Timeout**

```
Error: ArXiv API request timeout
Solution:
1. Check network connection
2. Increase ARXIV_RETRIES (retry count) in environment configuration
3. Increase ARXIV_DELAY (request interval to avoid excessive frequency)
```

**5. Prompt Template Error**

```
Error: Template variable missing or format error
Solution:
1. Check if variable names in prompts are correct
2. Confirm variable placeholder format is {variable_name}
3. Check detailed error messages in logs
4. Try resetting to default prompts
```

### Log Viewing

System logs are saved in the `logs/` directory:

```bash
# View latest logs
tail -f logs/fastapi.log

# View error logs
grep ERROR logs/fastapi.log
```

## 🤝 Contributing & Support

**Contributing Code**

```bash
# 1. Fork this project
Click the "Fork" button on the GitHub page to copy the project to your account

# 2. Clone locally
git clone https://github.com/YOUR_USERNAME/arXiv-Daily-Summary.git
cd arXiv-Daily-Summary

# 3. Create feature branch
git checkout -b feature/your-feature

# 4. Develop and commit changes
git add .
git commit -m "feat: add new feature description"

# 5. Push to remote
git push origin feature/your-feature

# 6. Create Pull Request
Create PR on GitHub page with detailed description of your changes
```

**Issue Feedback**

- Found a Bug? Please submit an [Issue](https://github.com/your-repo/issues)
- Have new ideas? Welcome discussions and suggestions
- Find it useful? Please give the project a Star

## 📄 License

This project is licensed under the [Apache 2.0 License](LICENSE)

## 🙏 Acknowledgments

- Thanks to the authors of [arxiv Python package](https://pypi.org/project/arxiv/) for providing very convenient paper download functionality.
- This project is inspired by the following excellent open source projects, thanks to their authors:
  - [TideDra/zotero-arxiv-daily](https://github.com/TideDra/zotero-arxiv-daily)
  - [Vincentqyw/cv-arxiv-daily](https://github.com/Vincentqyw/cv-arxiv-daily)
  - [AutoLLM/ArxivDigest](https://github.com/AutoLLM/ArxivDigest)

---

<p align="center">
  <strong>Let AI help you discover truly valuable research from the ocean of information</strong>
</p>
