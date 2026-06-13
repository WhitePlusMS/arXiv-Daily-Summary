"""调试模式推荐数据生成。

集中存放调试模式的假论文、假报告和 HTML 生成逻辑，避免 CLI/服务入口承担示例数据职责。
"""

import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from core.common_utils import format_timezone_date, get_timezone_aware_now


def build_debug_papers(target_date: str) -> List[Dict[str, Any]]:
    """生成调试模式论文样例。"""
    return [
        {
            "title": "Advanced Machine Learning Techniques for Natural Language Processing",
            "authors": ["John Smith", "Jane Doe"],
            "abstract": "This paper presents novel approaches to natural language processing using advanced machine learning techniques...",
            "arxiv_id": "2024.0001",
            "categories": ["cs.CL", "cs.LG"],
            "published": target_date,
        },
        {
            "title": "Quantum Computing Applications in Cryptography",
            "authors": ["Alice Johnson", "Bob Wilson"],
            "abstract": "We explore the implications of quantum computing on modern cryptographic systems...",
            "arxiv_id": "2024.0002",
            "categories": ["quant-ph", "cs.CR"],
            "published": target_date,
        },
    ]


def build_debug_summary(target_date: str, papers: List[Dict[str, Any]]) -> str:
    """生成调试模式 Markdown 报告。"""
    return f"""# ArXiv 每日论文推荐报告

**日期**: {target_date}
**生成时间**: {get_timezone_aware_now().strftime('%Y-%m-%d %H:%M:%S')}
**模式**: 调试模式

## 今日概览

- **论文总数**: {len(papers)}
- **重点推荐**: 2篇
- **涉及领域**: 机器学习、量子计算、密码学

## 重点推荐论文

### 1. Advanced Machine Learning Techniques for Natural Language Processing

**作者**: John Smith, Jane Doe
**ArXiv ID**: 2024.0001
**分类**: cs.CL, cs.LG

**推荐理由**: 这篇论文提出了创新的自然语言处理方法，结合了最新的机器学习技术，对当前NLP领域具有重要意义。

**核心贡献**:
- 提出了新的注意力机制
- 在多个基准数据集上取得了SOTA结果
- 方法具有良好的可解释性

### 2. Quantum Computing Applications in Cryptography

**作者**: Alice Johnson, Bob Wilson
**ArXiv ID**: 2024.0002
**分类**: quant-ph, cs.CR

**推荐理由**: 探讨了量子计算对现代密码学的影响，为后量子密码学的发展提供了重要见解。

**核心贡献**:
- 分析了量子算法对RSA加密的威胁
- 提出了抗量子攻击的新方案
- 给出了实用的安全建议

## 技术趋势分析

本日论文反映出以下技术趋势：
1. **机器学习与NLP的深度融合**: 越来越多的研究关注如何将先进的ML技术应用到NLP任务中
2. **量子计算的实用化**: 量子计算正从理论研究向实际应用转变
3. **安全性考量**: 随着新技术的发展，安全性问题变得越来越重要

---
*本报告由ArXiv每日论文推荐系统自动生成*
"""


def build_debug_html(target_date: str) -> str:
    """生成调试模式 HTML 报告。"""
    generated_at = get_timezone_aware_now().strftime("%Y-%m-%d %H:%M:%S")
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>ArXiv 每日论文推荐 - {target_date} (调试模式)</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
        h1, h2, h3 {{ color: #333; }}
        .debug-badge {{ background: #ff6b6b; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="debug-badge">调试模式</div>
    <h1>ArXiv 每日论文推荐报告</h1>
    <p><strong>日期</strong>: {target_date}</p>
    <p><strong>生成时间</strong>: {generated_at}</p>
    <p>这是调试模式生成的示例报告。</p>
</body>
</html>"""


def run_debug_recommendation(
    project_root: Path,
    target_date: Optional[str] = None,
) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """运行调试推荐流程并保存示例报告。"""
    try:
        target_date = target_date or format_timezone_date()
        logger.info(f"调试模式启动 - 目标日期: {target_date}")

        logger.info("模拟获取ArXiv论文...")
        time.sleep(1)
        papers = build_debug_papers(target_date)
        logger.success(f"模拟获取到 {len(papers)} 篇论文")

        logger.info("模拟LLM分析处理...")
        time.sleep(2)
        summary = build_debug_summary(target_date, papers)
        detailed_analysis = "详细分析内容...(调试模式生成)"
        brief_analysis = "简要分析内容...(调试模式生成)"
        logger.success("模拟分析完成")

        logger.info("保存调试报告...")
        output_dir = project_root / "output" / "reports"
        output_dir.mkdir(parents=True, exist_ok=True)

        md_filename = f"arxiv_recommendation_{target_date}_debug.md"
        md_filepath = output_dir / md_filename
        md_filepath.write_text(summary, encoding="utf-8")

        html_filename = f"arxiv_recommendation_{target_date}_debug.html"
        html_filepath = output_dir / html_filename
        html_filepath.write_text(build_debug_html(target_date), encoding="utf-8")

        logger.success(f"调试报告已保存: {md_filename}")
        return True, {
            "summary": summary,
            "detailed_analysis": detailed_analysis,
            "brief_analysis": brief_analysis,
            "papers_count": len(papers),
            "md_file": str(md_filepath),
            "html_file": str(html_filepath),
            "target_date": target_date,
        }, None
    except Exception as e:
        error_msg = f"调试模式运行失败: {str(e)}"
        logger.error(error_msg)
        return False, None, error_msg
