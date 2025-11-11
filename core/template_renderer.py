"""模板渲染器模块

提供Jinja2模板渲染功能，用于生成Markdown报告和HTML邮件内容。
"""

import os
from typing import Dict, Any, List, Optional
from jinja2 import Environment, FileSystemLoader, Template
from pathlib import Path
from loguru import logger
import markdown
from core.common_utils import STAR_LOW_THRESHOLD, STAR_HIGH_THRESHOLD


class TemplateRenderer:
    """模板渲染器，负责使用Jinja2渲染各种模板。"""
    
    def __init__(self, template_dir: Optional[str] = None):
        """初始化模板渲染器。
        
        Args:
            template_dir: 模板目录路径，如果为None则使用默认路径
        """
        logger.info("TemplateRenderer初始化开始")
        
        if template_dir is None:
            # 获取当前文件的目录，然后找到config/templates目录
            # 当前文件在 core/ 下，config/templates在项目根目录下
            current_dir = Path(__file__).parent
            template_dir = current_dir.parent / "config" / "templates"
        
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
            """将评分直接映射为星级显示（0–10）。
            规则：多少分就显示多少星（取整），下限0，上限10。"""
            try:
                # 保护性转换并裁剪范围到 [0, 10]
                star_count = int(float(score))
            except Exception:
                star_count = 0
            star_count = max(0, min(star_count, 10))
            return "⭐" * star_count
        
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