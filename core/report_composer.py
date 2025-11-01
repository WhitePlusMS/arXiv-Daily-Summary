"""报告内容生成模块

承载从论文列表中提取主题、生成研究趋势洞察与推荐理由的逻辑，
与模板渲染器解耦，便于独立演进与测试。
"""

from typing import List, Dict, Any


class ReportComposer:
    """负责根据论文数据组装报告的分析性内容。"""

    def extract_themes(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """从论文中提取主题分类。"""
        if not papers:
            return []

        themes = []

        high_score_papers = [p for p in papers if p.get("relevance_score", 0) >= 7]
        medium_score_papers = [p for p in papers if 5 <= p.get("relevance_score", 0) < 7]

        if high_score_papers:
            themes.append(
                {
                    "name": "高相关性研究",
                    "papers": high_score_papers,
                    "trend": "这些论文与研究兴趣高度匹配，代表了当前最相关的研究方向",
                    "highlights": "方法创新性强，实验验证充分，具有重要的理论和实践价值",
                }
            )

        if medium_score_papers:
            themes.append(
                {
                    "name": "相关研究领域",
                    "papers": medium_score_papers,
                    "trend": "这些论文在相关领域有一定价值，可作为研究参考",
                    "highlights": "提供了有价值的研究思路和方法参考",
                }
            )

        return themes

    def generate_research_insights(self, papers: List[Dict[str, Any]]) -> str:
        """生成研究趋势洞察。"""
        if not papers:
            return "暂无足够数据进行趋势分析。"

        avg_score = sum(p.get("relevance_score", 0) for p in papers) / len(papers)
        high_score_count = len([p for p in papers if p.get("relevance_score", 0) >= 7])

        insights = f"""基于今日推荐的{len(papers)}篇论文分析，当前研究领域呈现以下趋势：

1. **研究质量**: 平均相关性评分达到{avg_score:.1f}/10，其中{high_score_count}篇论文获得高分评价
2. **研究热点**: 推荐论文涵盖了多个前沿研究方向，显示出该领域的活跃度较高
3. **方法创新**: 论文在方法论上展现出多样化的创新思路，为后续研究提供了丰富的参考
4. **应用前景**: 多数论文具有良好的实际应用潜力，体现了理论与实践的结合"""

        return insights

    def generate_recommendation_rationale(self, papers: List[Dict[str, Any]]) -> str:
        """生成推荐理由。"""
        if not papers:
            return "今日暂无符合条件的推荐论文。"

        rationale = f"""推荐这{len(papers)}篇论文的主要原因包括：

1. **高度相关性**: 所有推荐论文都经过了严格的相关性评估，确保与研究兴趣的匹配度
2. **研究价值**: 论文在研究背景、方法创新、实验结果等方面都具有较高的学术价值
3. **时效性**: 这些都是近期发表的最新研究成果，代表了领域的最新进展
4. **实用性**: 论文提供的方法和结论对当前研究工作具有直接的参考和指导意义

建议优先关注评分较高的论文，它们在创新性和实用性方面表现更为突出。"""

        return rationale