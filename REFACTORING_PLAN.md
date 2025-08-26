#trecommendation_engine.py
│   │
│   ├── data_models/
│   │   ├── __init__.py
│   │   ├── paper.py
│   │   └── user.py
│   │
│   ├── pages/
│   │   ├── 1_Matcher.py
│   │   ├── 2_Settings.py
│   │   └── 3_Appendix_Browser.py
│   │
│   ├── templates/
│   │   └── markdown_report.j2
│   │
│   └── utils/
│       ├── __init__.py
│       ├── logging_config.py
│       ├── template_renderer.py
│       └── time_service.py
│
└── docker/
    ├── .dockerignore
    ├── .env
    ├── docker-compose.yml
    ├── docker-entrypoint.sh
    └── Dockerfile
```

---
### 文件改造前后对应关系 (完整版)

| 新文件/目录 (New Path) | 改造前的来源 (Old Path / Origin) |
| :--- | :--- |
| `src/app.py` | `ArXiv 每日论文推荐系统.py` & `start.py` |
| `src/cli.py` | `core/task3_recommendation_cli/cli_main.py` |
| `src/config.py` | *(新创建)* |
| `src/core/arxiv_fetcher.py` | `core/arxiv_fetcher.py` |
| `src/core/llm_provider.py` | `core/llm_provider.py` |
| `src/core/output_manager.py` | `core/output_manager.py` |
| `src/core/recommendation_engine.py`| `core/recommendation_engine.py` |
| `src/data_models/*` | *(新创建)* |
| `src/pages/1_Matcher.py` | `pages/1_分类匹配器.py` |
| `src/pages/2_Settings.py` | `pages/2_环境配置.py` |
| `src/pages/3_Appendix_Browser.py` | `pages/3_附录_分类浏览器.py` |
| `src/templates/markdown_report.j2`| `templates/markdown_report_email.j2` |
| `src/utils/logging_config.py` | *(新创建)* |
| `src/utils/template_renderer.py`| `core/utils/template_renderer.py` |
| `src/utils/time_service.py` | `core/utils/mcp_time_service.py` |
| `scripts/extract_categories.py` | `core/task1_category_extraction/task1_extract_arxiv_categories.py` |
| `scripts/convert_md_to_json.py` | `core/task1_category_extraction/task1_convert_md_to_json.py` |
| `scripts/category_matcher.py` | `core/task2_category_matching/task2_category_matcher.py` |
| `scripts/cleanup_translated_file.py`| `utils/cleanup_translated_file.py` |
| `scripts/traies.py`| `utils/translate_caaask1_egotaskegoz