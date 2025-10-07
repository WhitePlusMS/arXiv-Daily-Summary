# Tools 工具目录

本目录包含了 ArXiv 每日论文推荐系统的各种辅助工具和脚本，用于数据处理、分类管理和系统维护。

## 目录结构

```
tools/
├── arxiv_category_extractor/     # ArXiv 分类信息提取工具
├── category_profiling_generator/ # 分类画像生成工具
├── cleanup_translated_file.py    # 翻译文件清理工具
└── translate_categories.py       # 分类翻译工具
```

## 工具详细说明

### 1. arxiv_category_extractor/ - ArXiv 分类信息提取工具

这个目录包含从 ArXiv 官方网站提取分类信息的工具集。

#### 文件说明：

- **`extract_categories.py`** - 主要提取脚本
  - 功能：从 HTML 文件中提取 ArXiv 分类信息
  - 输入：`source.html`（ArXiv 官方分类页面的 HTML 源码）
  - 输出：结构化的分类信息到 Markdown 文件
  - 支持解析主分类和子分类的层级结构

- **`convert_to_json.py`** - 格式转换工具
  - 功能：将 Markdown 格式的分类信息转换为 JSON 格式
  - 输入：`extracted_categories.md`
  - 输出：标准化的 JSON 分类文件
  - 便于程序化处理和数据交换

- **`source.html`** - 数据源文件
  - ArXiv 官方分类页面的 HTML 源码
  - 作为分类信息提取的原始数据源

- **`extracted_categories.md`** - 中间输出文件
  - 从 HTML 提取后的 Markdown 格式分类信息
  - 人类可读的分类结构展示

### 2. category_profiling_generator/ - 分类画像生成工具

这个目录包含为 ArXiv 分类生成详细画像的工具，用于增强分类匹配的准确性。

#### 文件说明：

- **`category_profile_generator.py`** - 分类画像生成器
  - 功能：为每个 ArXiv 分类创建详细的"画像"
  - 工作流程：
    1. 读取现有的 ArXiv 分类信息
    2. 从 ArXiv API 获取代表性论文
    3. 使用 LLM 分析论文内容
    4. 生成包含核心主题、常用方法、交叉领域和关键词的分类画像
  - 输出：增强后的分类信息 JSON 文件

- **`arxiv_yearly_tester.py`** - 年度相关性测试工具
  - 功能：测试获取指定分类在过去几年中每年最相关的论文
  - 用途：验证 ArXiv API 查询功能和数据质量
  - 支持按年份范围查询和相关性排序

- **`generated_user_descriptions.json`** - 生成的用户描述文件
  - 存储 LLM 生成的分类画像数据
  - 包含详细的分类特征描述

- **`token_usage.json`** - Token 使用统计
  - 记录 LLM API 调用的 Token 消耗情况
  - 用于成本控制和性能监控

### 3. cleanup_translated_file.py - 翻译文件清理工具

- **功能**：清理翻译后的分类文件，删除冗余字段
- **主要操作**：
  - 删除子分类中的 'name' 和 'description' 字段
  - 保持数据结构的一致性
  - 减少文件大小和处理复杂度
- **使用场景**：在分类文件翻译完成后进行数据清理

### 4. translate_categories.py - 分类翻译工具

- **功能**：使用 LLM 将 ArXiv 分类信息翻译为中文
- **特性**：
  - 支持批量翻译分类名称和描述
  - 集成通义千问 LLM 服务
  - 自动处理翻译错误和重试机制
  - 保持原有的 JSON 数据结构
- **配置**：需要在 `.env` 文件中配置 LLM 相关参数

## 使用指南

### 环境准备

1. 确保已安装项目依赖：
   ```bash
   pip install -r requirements.txt
   ```

2. 配置环境变量（`.env` 文件）：
   ```
   QWEN_MODEL=your_model_name
   DASHSCOPE_BASE_URL=your_api_base_url
   DASHSCOPE_API_KEY=your_api_key
   ```

### 典型工作流程

1. **提取分类信息**：
   ```bash
   cd tools/arxiv_category_extractor
   python extract_categories.py
   python convert_to_json.py
   ```

2. **翻译分类信息**：
   ```bash
   cd tools
   python translate_categories.py
   ```

3. **清理翻译文件**：
   ```bash
   python cleanup_translated_file.py
   ```

4. **生成分类画像**：
   ```bash
   cd tools/category_profiling_generator
   python category_profile_generator.py
   ```

## 注意事项

- 所有工具都需要在项目根目录的 Python 环境中运行
- 使用 LLM 相关工具前请确保 API 配置正确
- 部分工具可能需要较长的运行时间，特别是涉及大量 API 调用的操作
- 建议在使用前备份重要的数据文件

## 维护说明

这些工具主要用于系统的初始化设置和数据维护，不是日常运行的核心组件。在 ArXiv 分类体系发生变化或需要更新分类数据时使用。