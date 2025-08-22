# 多用户ArXiv分类匹配器 - JSON输出功能

## 📋 功能概述

本功能扩展了原有的ArXiv分类匹配器，支持多用户数据存储和JSON格式输出。系统能够处理多个用户的研究方向描述，通过LLM评估匹配度，并将结果保存为结构化的JSON文件。

## 🆕 新增功能

### 1. MultiUserDataManager 类

- **多用户数据管理**：支持存储多个用户的分类匹配结果
- **JSON格式输出**：将结果保存为结构化的JSON文件
- **数据持久化**：支持从现有JSON文件加载数据
- **时间戳记录**：每条记录包含创建时间

### 2. 增强的CategoryMatcher

- **Token统计**：记录每次LLM调用的token使用量
- **费用计算**：基于通义千问Plus定价计算API调用费用
- **批量处理**：支持处理多个用户的多个研究方向

## 📊 JSON输出格式

生成的JSON文件包含以下结构：

```json
{
  "metadata": {
    "total_records": 20,
    "generated_at": "2025-08-10T13:51:31.850464",
    "description": "多用户ArXiv分类匹配结果"
  },
  "users": [
    {
      "username": "用户名",
      "category_id": "分类ID",
      "user_input": "用户输入的研究方向描述",
      "score": 匹配评分(0-100),
      "timestamp": "记录创建时间"
    }
  ]
}
```

### 字段说明

- **metadata**: 元数据信息
  - `total_records`: 总记录数
  - `generated_at`: 文件生成时间
  - `description`: 文件描述

- **users**: 用户数据数组
  - `username`: 用户名（支持重复，表示同一用户的不同研究方向）
  - `category_id`: ArXiv分类ID
  - `user_input`: 用户输入的研究方向描述
  - `score`: LLM评估的匹配度评分（0-100）
  - `timestamp`: 记录创建的时间戳

## 🚀 使用方法

### 方法1：运行主程序

```bash
cd c:\Users\admin\Desktop\arxiv_recommender_v2\task1
python category_matcher.py
```

这将处理预设的示例用户数据并生成 `user_categories.json` 文件。

### 方法2：运行演示程序

```bash
python multi_user_demo.py
```

这将运行更详细的演示，包含更多用户和研究方向的示例。

### 方法3：编程方式使用

```python
from category_matcher import CategoryMatcher, MultiUserDataManager

# 初始化
matcher = CategoryMatcher(model, base_url, api_key)
data_manager = MultiUserDataManager("output.json")

# 处理用户数据
user_input = "研究方向描述"
top_matches = matcher.match_categories(user_input, top_n=5)

# 保存结果
for category_id, category_name, score in top_matches:
    data_manager.add_user_result(
        username="用户名",
        category_id=category_id,
        user_input=user_input,
        score=score
    )

# 保存到文件
data_manager.save_to_json()
```

## 📈 示例输出

运行程序后，会在控制台看到类似输出：

```
=== 开始处理多用户分类匹配 ===

处理用户: 张三
研究方向: 我的研究方向是地球物理学，主要是研究地球的运动和变化...
开始匹配分类...

=== 张三 的匹配结果 ===
1. astro-ph.HE - High Energy Astrophysical Phenomena (评分: 92)
2. math.MP - Mathematical Physics (评分: 76)
3. astro-ph.CO - Cosmology and Nongalactic Astrophysics (评分: 76)

=== Token使用统计 ===
输入Token: 270,273
输出Token: 908
总Token: 271,181

=== 费用计算 (通义千问Plus定价) ===
总费用: ¥2.1803
总费用: $0.2987 (按汇率7.3计算)

=== 数据保存完成 ===
文件路径: C:\Users\admin\Desktop\arxiv_recommender_v2\task1\user_categories.json
记录数量: 20
```

## 🔧 配置要求

确保 `.env` 文件包含以下配置：

```env
DASHSCOPE_API_KEY=your_api_key_here
QWEN_MODEL=qwen-plus
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

## 📝 数据特点

1. **多用户支持**：同一个用户可以有多个研究方向
2. **唯一用户名**：通过用户名区分不同用户
3. **重复用户名**：同一用户名可以对应多个研究方向
4. **完整记录**：每条记录包含用户名、分类ID、输入描述、评分和时间戳
5. **可扩展性**：支持增量添加新的用户数据

## 💡 使用场景

- **研究机构**：管理多个研究员的研究方向分类
- **学术平台**：为用户推荐相关的ArXiv分类
- **数据分析**：分析用户研究兴趣的分布情况
- **个人管理**：跟踪个人多个研究方向的分类匹配

## 🔍 文件说明

- `category_matcher.py`: 主程序文件，包含CategoryMatcher和MultiUserDataManager类
- `multi_user_demo.py`: 演示程序，展示多用户处理流程
- `user_categories.json`: 输出的JSON结果文件
- `MULTI_USER_README.md`: 本说明文件

## ⚠️ 注意事项

1. **API费用**：每次运行会消耗API token，请注意费用控制
2. **处理时间**：处理多个用户可能需要较长时间
3. **文件覆盖**：重复运行会覆盖现有的JSON文件
4. **数据备份**：建议定期备份重要的结果文件
