#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ArXiv分类评分可视化工具

该脚本读取详细评分JSON文件并生成可视化图表
横轴：分类ID
纵轴：评分
"""

import json
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
from pathlib import Path

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def load_scores_data(json_file_path):
    """
    从JSON文件加载评分数据
    
    Args:
        json_file_path (str): JSON文件路径
        
    Returns:
        tuple: (categories, scores, metadata)
    """
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        detailed_scores = data['detailed_scores']
        metadata = data['metadata']
        
        # 提取分类ID和评分
        categories = [item['category_id'] for item in detailed_scores]
        scores = [item['score'] for item in detailed_scores]
        category_names = [item['category_name'] for item in detailed_scores]
        
        return categories, scores, category_names, metadata
    
    except FileNotFoundError:
        print(f"错误：找不到文件 {json_file_path}")
        return None, None, None, None
    except json.JSONDecodeError:
        print(f"错误：JSON文件格式不正确 {json_file_path}")
        return None, None, None, None
    except KeyError as e:
        print(f"错误：JSON文件缺少必要字段 {e}")
        return None, None, None, None

def create_score_visualization(categories, scores, category_names, metadata, output_path=None):
    """
    创建评分可视化图表
    
    Args:
        categories (list): 分类ID列表
        scores (list): 评分列表
        category_names (list): 分类名称列表
        metadata (dict): 元数据
        output_path (str, optional): 输出图片路径
    """
    # 创建图表
    fig, ax = plt.subplots(figsize=(20, 10))
    
    # 创建颜色映射
    colors = plt.cm.viridis(np.linspace(0, 1, len(scores)))
    
    # 绘制柱状图
    bars = ax.bar(range(len(categories)), scores, color=colors, alpha=0.8, edgecolor='black', linewidth=0.5)
    
    # 设置标题和标签
    username = metadata.get('username', 'Unknown')
    timestamp = metadata.get('timestamp', 'Unknown')
    total_categories = metadata.get('total_categories', len(categories))
    
    ax.set_title(f'ArXiv分类评分分析\n用户: {username} | 时间: {timestamp} | 总分类数: {total_categories}', 
                fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('分类ID', fontsize=12, fontweight='bold')
    ax.set_ylabel('评分', fontsize=12, fontweight='bold')
    
    # 设置x轴标签
    ax.set_xticks(range(len(categories)))
    ax.set_xticklabels(categories, rotation=45, ha='right', fontsize=8)
    
    # 设置y轴范围
    ax.set_ylim(0, max(scores) * 1.1)
    
    # 添加网格
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # 添加数值标签（仅对高分项显示）
    for i, (bar, score) in enumerate(zip(bars, scores)):
        if score > 50:  # 只对评分大于50的显示数值
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                   f'{score}', ha='center', va='bottom', fontsize=8, fontweight='bold')
    
    # 添加统计信息
    stats_text = f"最高分: {max(scores)} | 最低分: {min(scores)} | 平均分: {np.mean(scores):.1f} | 中位数: {np.median(scores):.1f}"
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=10, 
           verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    # 调整布局
    plt.tight_layout()
    
    # 保存图片
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"图表已保存到: {output_path}")
    
    # 不显示图表，只保存
    # plt.show()

def create_top_categories_chart(categories, scores, category_names, metadata, json_file_path, top_n=20):
    """
    创建Top N分类的详细图表
    
    Args:
        categories (list): 分类ID列表
        scores (list): 评分列表
        category_names (list): 分类名称列表
        metadata (dict): 元数据
        json_file_path (str): JSON文件路径（用于确定输出路径）
        top_n (int): 显示前N个分类
    """
    # 获取前N个分类
    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_n]
    top_categories = [categories[i] for i in top_indices]
    top_scores = [scores[i] for i in top_indices]
    top_names = [category_names[i] for i in top_indices]
    
    # 创建图表
    fig, ax = plt.subplots(figsize=(15, 10))
    
    # 创建颜色映射
    colors = plt.cm.RdYlGn(np.linspace(0.3, 1, len(top_scores)))
    
    # 绘制水平柱状图
    bars = ax.barh(range(len(top_categories)), top_scores, color=colors, alpha=0.8, edgecolor='black', linewidth=0.5)
    
    # 设置标题和标签
    username = metadata.get('username', 'Unknown')
    ax.set_title(f'Top {top_n} ArXiv分类评分\n用户: {username}', 
                fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('评分', fontsize=12, fontweight='bold')
    ax.set_ylabel('分类', fontsize=12, fontweight='bold')
    
    # 设置y轴标签（显示分类ID和名称）
    y_labels = [f"{cat_id}\n{name[:30]}{'...' if len(name) > 30 else ''}" 
               for cat_id, name in zip(top_categories, top_names)]
    ax.set_yticks(range(len(top_categories)))
    ax.set_yticklabels(y_labels, fontsize=9)
    
    # 反转y轴（最高分在顶部）
    ax.invert_yaxis()
    
    # 添加数值标签
    for i, (bar, score) in enumerate(zip(bars, top_scores)):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2, 
               f'{score}', ha='left', va='center', fontsize=10, fontweight='bold')
    
    # 添加网格
    ax.grid(True, alpha=0.3, linestyle='--', axis='x')
    
    # 调整布局
    plt.tight_layout()
    
    # 保存Top分类图表
    top_output_path = Path(json_file_path).parent / "arxiv_top_categories_visualization.png"
    plt.savefig(str(top_output_path), dpi=300, bbox_inches='tight')
    print(f"Top分类图表已保存到: {top_output_path}")
    # 不显示图表，只保存
    # plt.show()

def main():
    """
    主函数
    """
    # JSON文件路径
    json_file_path = r"c:\Users\admin\Desktop\ARXIV_daily_article_summary\data\users\detailed_scores\T2_20250909_083739_detailed_scores.json"
    
    print("正在加载评分数据...")
    categories, scores, category_names, metadata = load_scores_data(json_file_path)
    
    if categories is None:
        print("加载数据失败，程序退出。")
        return
    
    print(f"成功加载 {len(categories)} 个分类的评分数据")
    
    # 创建完整的评分可视化
    print("\n正在生成完整评分图表...")
    output_path = Path(json_file_path).parent / "arxiv_scores_visualization.png"
    create_score_visualization(categories, scores, category_names, metadata, str(output_path))
    
    # 创建Top 20分类图表
    print("\n正在生成Top 20分类图表...")
    create_top_categories_chart(categories, scores, category_names, metadata, json_file_path, top_n=20)
    
    print("\n可视化完成！")
    print(f"数据统计:")
    print(f"  - 总分类数: {len(categories)}")
    print(f"  - 最高评分: {max(scores)}")
    print(f"  - 最低评分: {min(scores)}")
    print(f"  - 平均评分: {np.mean(scores):.2f}")
    print(f"  - 评分大于0的分类数: {sum(1 for s in scores if s > 0)}")

if __name__ == "__main__":
    main()