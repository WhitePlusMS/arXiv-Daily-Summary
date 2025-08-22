"""模板渲染器模块

提供Jinja2模板渲染功能，用于生成Markdown报告和HTML邮件内容。
"""

import os
from typing import Dict, Any, List, Optional
from jinja2 import Environment, FileSystemLoader, Template
from pathlib import Path
from loguru import logger
import markdown


class TemplateRenderer:
    """模板渲染器，负责使用Jinja2渲染各种模板。"""
    
    def __init__(self, template_dir: Optional[str] = None):
        """初始化模板渲染器。
        
        Args:
            template_dir: 模板目录路径，如果为None则使用默认路径
        """
        logger.info("TemplateRenderer初始化开始")
        
        if template_dir is None:
            # 获取当前文件的目录，然后找到templates目录
            # 当前文件在 core/utils/ 下，templates在项目根目录下
            current_dir = Path(__file__).parent
            template_dir = current_dir.parent.parent / "templates"
        
        self.template_dir = Path(template_dir)
        logger.debug(f"模板目录: {self.template_dir}")
        
        # 确保模板目录存在
        if not self.template_dir.exists():
            logger.error(f"模板目录不存在: {self.template_dir}")
            raise FileNotFoundError(f"模板目录不存在: {self.template_dir}")
        
        # 初始化Jinja2环境
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # 添加自定义过滤器
        self._add_custom_filters()
        
        logger.success("TemplateRenderer初始化完成")
    
    def _add_custom_filters(self):
        """添加自定义Jinja2过滤器。"""
        
        def format_score_stars(score: float) -> str:
            """将评分转换为星级显示。"""
            if score <= 2:
                return ""
            elif score >= 8:
                return "⭐" * 5
            else:
                star_count = int((score - 2) / 1.2)
                return "⭐" * min(star_count, 5)
        
        def truncate_text(text: str, length: int = 100) -> str:
            """截断文本到指定长度。"""
            if len(text) <= length:
                return text
            return text[:length].rstrip() + "..."
        
        def format_authors(authors: List[str], max_authors: int = 3) -> str:
            """格式化作者列表。"""
            if len(authors) <= max_authors:
                return ", ".join(authors)
            return ", ".join(authors[:max_authors]) + f" et al. (+{len(authors) - max_authors})"
        
        def markdown_to_html(text: str) -> str:
            """将Markdown文本转换为HTML。"""
            if not text:
                return ""
            
            # 配置markdown扩展
            md = markdown.Markdown(
                extensions=[
                    'markdown.extensions.extra',
                    'markdown.extensions.codehilite',
                    'markdown.extensions.toc'
                ],
                extension_configs={
                    'markdown.extensions.codehilite': {
                        'css_class': 'highlight'
                    }
                }
            )
            
            return md.convert(text)
        
        # 注册过滤器
        self.env.filters['format_score_stars'] = format_score_stars
        self.env.filters['truncate_text'] = truncate_text
        self.env.filters['format_authors'] = format_authors
        self.env.filters['markdown_to_html'] = markdown_to_html
    
    
    def render_template(self, template_name: str, **context) -> str:
        """渲染指定的模板。
        
        Args:
            template_name: 模板文件名
            **context: 模板变量
            
        Returns:
            渲染后的内容
        """
        logger.debug(f"模板渲染开始 - {template_name}")
        try:
            template = self.env.get_template(template_name)
            result = template.render(**context)
            logger.debug(f"模板渲染完成 - {template_name} (长度: {len(result)} 字符)")
            return result
        except Exception as e:
            logger.error(f"模板渲染失败 - {template_name}: {e}")
            raise
    
    def _extract_themes(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """从论文中提取主题分类。
        
        Args:
            papers: 论文列表
            
        Returns:
            主题列表
        """
        if not papers:
            return []
        
        # 简单的主题提取逻辑，可以根据需要扩展
        themes = []
        
        # 按相关性评分分组
        high_score_papers = [p for p in papers if p.get('relevance_score', 0) >= 7]
        medium_score_papers = [p for p in papers if 5 <= p.get('relevance_score', 0) < 7]
        
        if high_score_papers:
            themes.append({
                'name': '高相关性研究',
                'papers': high_score_papers,
                'trend': '这些论文与研究兴趣高度匹配，代表了当前最相关的研究方向',
                'highlights': '方法创新性强，实验验证充分，具有重要的理论和实践价值'
            })
        
        if medium_score_papers:
            themes.append({
                'name': '相关研究领域',
                'papers': medium_score_papers,
                'trend': '这些论文在相关领域有一定价值，可作为研究参考',
                'highlights': '提供了有价值的研究思路和方法参考'
            })
        
        return themes
    
    def _generate_research_insights(self, papers: List[Dict[str, Any]]) -> str:
        """生成研究趋势洞察。
        
        Args:
            papers: 论文列表
            
        Returns:
            研究趋势洞察文本
        """
        if not papers:
            return "暂无足够数据进行趋势分析。"
        
        avg_score = sum(p.get('relevance_score', 0) for p in papers) / len(papers)
        high_score_count = len([p for p in papers if p.get('relevance_score', 0) >= 7])
        
        insights = f"""基于今日推荐的{len(papers)}篇论文分析，当前研究领域呈现以下趋势：

1. **研究质量**: 平均相关性评分达到{avg_score:.1f}/10，其中{high_score_count}篇论文获得高分评价
2. **研究热点**: 推荐论文涵盖了多个前沿研究方向，显示出该领域的活跃度较高
3. **方法创新**: 论文在方法论上展现出多样化的创新思路，为后续研究提供了丰富的参考
4. **应用前景**: 多数论文具有良好的实际应用潜力，体现了理论与实践的结合"""
        
        return insights
    
    def _generate_recommendation_rationale(self, papers: List[Dict[str, Any]]) -> str:
        """生成推荐理由。
        
        Args:
            papers: 论文列表
            
        Returns:
            推荐理由文本
        """
        if not papers:
            return "今日暂无符合条件的推荐论文。"
        
        rationale = f"""推荐这{len(papers)}篇论文的主要原因包括：

1. **高度相关性**: 所有推荐论文都经过了严格的相关性评估，确保与研究兴趣的匹配度
2. **研究价值**: 论文在研究背景、方法创新、实验结果等方面都具有较高的学术价值
3. **时效性**: 这些都是近期发表的最新研究成果，代表了领域的最新进展
4. **实用性**: 论文提供的方法和结论对当前研究工作具有直接的参考和指导意义

建议优先关注评分较高的论文，它们在创新性和实用性方面表现更为突出。"""
        
        return rationale


def main():
    """独立测试函数。"""
    logger.info("TemplateRenderer测试开始")
    
    # 创建测试数据
    test_papers = [
        {
            'title': 'Test Paper 1',
            'arXiv_id': '2024.0001',
            'authors': ['Author A', 'Author B', 'Author C'],
            'published': '2024-01-01',
            'relevance_score': 8.5,
            'research_background': '这是一个测试论文的研究背景',
            'methodology_innovation': '测试方法创新点',
            'experimental_results': '测试实验结果',
            'conclusion_significance': '测试结论意义',
            'tldr': '这是一个测试论文的核心贡献',
            'pdf_url': 'https://arxiv.org/pdf/2024.0001.pdf',
            'abstract_url': 'https://arxiv.org/abs/2024.0001'
        },
        {
            'title': 'Test Paper 2',
            'arXiv_id': '2024.0002',
            'authors': ['Author X', 'Author Y'],
            'published': '2024-01-02',
            'relevance_score': 6.0,
            'research_background': '第二个测试论文的研究背景',
            'methodology_innovation': '第二个测试方法创新点',
            'experimental_results': '第二个测试实验结果',
            'conclusion_significance': '第二个测试结论意义',
            'tldr': '第二个测试论文的核心贡献',
            'pdf_url': 'https://arxiv.org/pdf/2024.0002.pdf',
            'abstract_url': 'https://arxiv.org/abs/2024.0002'
        }
    ]
    
    try:
        # 初始化模板渲染器
        renderer = TemplateRenderer()
        
        # 测试模板渲染功能
        logger.info("开始基础模板渲染测试")
        test_content = renderer.render_template(
            'markdown_report_email.j2',
            markdown_content="# 测试内容\n\n这是一个测试。",
            current_time='2024-01-01 12:00:00'
        )
        logger.debug(f"测试内容预览: {test_content[:200]}...")
        
        logger.success("TemplateRenderer测试完成")
        
    except Exception as e:
        logger.error(f"TemplateRenderer测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()