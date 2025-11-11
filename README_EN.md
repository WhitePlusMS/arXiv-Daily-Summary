<h1 align="center">arXiv Daily Article Summary</h1>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?logo=python" alt="Python Version">
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

- [✨ Core Features](#-core-features) - Understand the core problems this project solves
- [⚡ Quick Start](#-quick-start) - One-click startup for quick experience
- [💻 Interface Preview](#-interface-preview) - View system interface screenshots
- [⚙️ Usage Guide](#️-usage-guide) - Detailed operation instructions
- [🤝 Contributing & Support](#-contributing--support) - How to participate in the project

---

## ✨ Core Features

### Intelligent Recommendation Engine

- **Personalized Matching**: Precise paper filtering based on your research interests and keywords
- **AI Deep Analysis**: Paper abstracts and key insights extraction powered by Qwen models
- **Multi-dimensional Evaluation**: Comprehensive scoring from relevance, innovation, and practicality perspectives

### Automated Workflow

- **One-click Startup**: Complete configuration and startup with `python start.py`
- **Smart Environment Management**: Automatic detection and configuration of Python environment and dependencies
- **Web Interface**: Intuitive operation interface powered by Streamlit

### Diverse Output

- **Real-time Recommendations**: View recommendation results in real-time through web interface
- **Historical Archive**: Automatically save daily recommendation records to `arxiv_history` directory
- **Rich Formats**: Support multiple output formats including Markdown, HTML, etc.

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

# 9. Start the application!
python start.py

# 10. Access Web Interface
#     Open browser and visit http://localhost:8501
#     You can configure research interests, adjust parameters, and view real-time recommendation results in the interface

# enjoy it!
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
    * The system automatically loads the user's configuration, including their matched **category tags** and **research interests**.
2. **Start Recommendation**: Click the "Start Paper Recommendation" button.
3. **Monitor & View Results**:
    * After system startup, **real-time running logs** are displayed below, clearly showing each step's execution status, such as "Fetching Papers", "Analyzing Papers", "Generating Reports", etc.
    * After successful execution, recommendation results are displayed in tab format, including **Summary Content**, **Detailed Analysis**, and **Brief Analysis**.
    * Meanwhile, the system generates complete `HTML` and `Markdown` format reports that you can preview directly on the webpage or download locally.

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