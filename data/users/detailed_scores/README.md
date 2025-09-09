# 详细评分数据说明

本目录用于保存每次分类匹配的全部115个ArXiv分类的详细评分数据。

## 文件命名规则

文件名格式：`{用户名}_{时间戳}_detailed_scores.json`

例如：`张三_20241223_143052_detailed_scores.json`

## JSON文件结构

```json
{
  "metadata": {
    "username": "用户名",
    "timestamp": "2024-12-23T14:30:52.123456",
    "user_description": "用户输入的研究方向描述",
    "total_categories": 115,
    "token_usage": {
      "input_tokens": 12345,
      "output_tokens": 678,
      "total_tokens": 13023
    }
  },
  "detailed_scores": [
    {
      "rank": 1,
      "category_id": "cs.AI",
      "category_name": "Artificial Intelligence",
      "score": 95
    },
    {
      "rank": 2,
      "category_id": "cs.LG",
      "category_name": "Machine Learning",
      "score": 87
    }
    // ... 其余113个分类的评分数据
  ]
}
```

## 数据说明

- **metadata**: 包含匹配的元数据信息
  - `username`: 执行匹配的用户名
  - `timestamp`: 匹配执行的时间戳（ISO格式）
  - `user_description`: 用户输入的研究方向描述
  - `total_categories`: 评估的分类总数
  - `token_usage`: LLM调用的Token使用统计

- **detailed_scores**: 包含所有分类的详细评分
  - `rank`: 按评分排序后的排名（1-115）
  - `category_id`: ArXiv分类ID
  - `category_name`: 分类名称
  - `score`: LLM给出的匹配评分（0-100）

## 使用场景

1. **研究分析**: 分析用户研究方向与各个ArXiv分类的匹配程度
2. **模型优化**: 基于历史评分数据优化匹配算法
3. **用户画像**: 构建用户的研究兴趣画像
4. **数据挖掘**: 发现研究领域之间的关联性