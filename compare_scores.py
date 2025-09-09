#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ArXiv分类评分对比可视化工具

该脚本用于对比原始版本和Enhanced版本的评分差异
支持批量处理多个用户的对照数据
"""

import json
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
from pathlib import Path
import re

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def load_scores_data(json_file_path):
    """
    从JSON文件加载评分数据
    
    Args:
        json_file_path (str): JSON文件路径
        
    Returns:
        tuple: (categories, scores, metadata) 或 (None, None, None)
    """
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        detailed_scores = data['detailed_scores']
        metadata = data['metadata']
        
        # 提取分类ID和评分，按分类ID排序以确保对比时顺序一致
        score_dict = {item['category_id']: item['score'] for item in detailed_scores}
        categories = sorted(score_dict.keys())
        scores = [score_dict[cat] for cat in categories]
        
        return categories, scores, metadata
    
    except Exception as e:
        print(f"加载文件 {json_file_path} 失败: {e}")
        return None, None, None

def find_paired_files(detailed_scores_dir):
    """
    查找配对的原始和enhanced文件
    
    Args:
        detailed_scores_dir (Path): detailed_scores文件夹路径
        
    Returns:
        list: 配对文件列表，每个元素为(original_file, enhanced_file, user_base)
    """
    json_files = list(detailed_scores_dir.glob("*.json"))
    
    # 按用户分组
    user_groups = {}
    for file in json_files:
        # 提取用户基础名称（去掉_en_enhanced后缀和时间戳）
        filename = file.stem
        if '_en_enhanced_' in filename:
            # enhanced文件
            user_base = filename.split('_en_enhanced_')[0]
            if user_base not in user_groups:
                user_groups[user_base] = {}
            user_groups[user_base]['enhanced'] = file
        else:
            # 原始文件
            # 提取用户名（去掉时间戳）
            parts = filename.split('_')
            if len(parts) >= 3:  # user_X_timestamp_detailed_scores
                user_base = '_'.join(parts[:2])  # user_X
                if user_base not in user_groups:
                    user_groups[user_base] = {}
                user_groups[user_base]['original'] = file
    
    # 找到配对的文件
    paired_files = []
    for user_base, files in user_groups.items():
        if 'original' in files and 'enhanced' in files:
            paired_files.append((files['original'], files['enhanced'], user_base))
        else:
            print(f"警告：用户 {user_base} 缺少配对文件")
            if 'original' in files:
                print(f"  - 找到原始文件: {files['original'].name}")
            if 'enhanced' in files:
                print(f"  - 找到enhanced文件: {files['enhanced'].name}")
    
    return paired_files

def create_comparison_chart(original_file, enhanced_file, user_base, output_dir):
    """
    创建单个用户的对比图表
    
    Args:
        original_file (Path): 原始文件路径
        enhanced_file (Path): enhanced文件路径
        user_base (str): 用户基础名称
        output_dir (Path): 输出目录
    """
    # 加载数据
    orig_categories, orig_scores, orig_metadata = load_scores_data(str(original_file))
    enh_categories, enh_scores, enh_metadata = load_scores_data(str(enhanced_file))
    
    if orig_categories is None or enh_categories is None:
        print(f"跳过用户 {user_base}：数据加载失败")
        return False
    
    # 确保分类顺序一致
    if orig_categories != enh_categories:
        print(f"警告：用户 {user_base} 的分类顺序不一致，正在重新排序...")
        # 取交集并排序
        common_categories = sorted(set(orig_categories) & set(enh_categories))
        orig_score_dict = dict(zip(orig_categories, orig_scores))
        enh_score_dict = dict(zip(enh_categories, enh_scores))
        
        orig_scores = [orig_score_dict[cat] for cat in common_categories]
        enh_scores = [enh_score_dict[cat] for cat in common_categories]
        categories = common_categories
    else:
        categories = orig_categories
    
    # 计算改进情况
    improvements = [enh - orig for orig, enh in zip(orig_scores, enh_scores)]
    improved_count = sum(1 for imp in improvements if imp > 0)
    total_improvement = sum(imp for imp in improvements if imp > 0)
    
    # 创建图表
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(20, 12))
    
    # 上图：并排柱状图对比
    x = np.arange(len(categories))
    width = 0.35
    
    bars1 = ax1.bar(x - width/2, orig_scores, width, label='原始版本', alpha=0.8, color='lightcoral')
    bars2 = ax1.bar(x + width/2, enh_scores, width, label='Enhanced版本', alpha=0.8, color='lightgreen')
    
    ax1.set_title(f'{user_base} - ArXiv分类评分对比\n改进分类数: {improved_count}/{len(categories)} | 总改进分数: +{total_improvement}', 
                 fontsize=14, fontweight='bold')
    ax1.set_xlabel('分类ID', fontsize=10)
    ax1.set_ylabel('评分', fontsize=10)
    ax1.set_xticks(x)
    ax1.set_xticklabels(categories, rotation=45, ha='right', fontsize=6)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 下图：改进幅度
    colors = ['red' if imp < 0 else 'green' if imp > 0 else 'gray' for imp in improvements]
    bars3 = ax2.bar(x, improvements, color=colors, alpha=0.7)
    
    ax2.set_title('评分改进幅度 (Enhanced - 原始)', fontsize=12, fontweight='bold')
    ax2.set_xlabel('分类ID', fontsize=10)
    ax2.set_ylabel('改进分数', fontsize=10)
    ax2.set_xticks(x)
    ax2.set_xticklabels(categories, rotation=45, ha='right', fontsize=6)
    ax2.axhline(y=0, color='black', linestyle='-', alpha=0.5)
    ax2.grid(True, alpha=0.3)
    
    # 添加统计信息
    stats_text = f"原始平均分: {np.mean(orig_scores):.1f} | Enhanced平均分: {np.mean(enh_scores):.1f} | 平均改进: {np.mean(improvements):.1f}"
    fig.suptitle(stats_text, fontsize=10, y=0.02)
    
    plt.tight_layout()
    
    # 保存图片
    output_path = output_dir / f"{user_base}_comparison.png"
    plt.savefig(str(output_path), dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"已生成对比图表: {output_path}")
    return True

def create_summary_chart(paired_files, output_dir):
    """
    创建所有用户的汇总对比图表
    
    Args:
        paired_files (list): 配对文件列表
        output_dir (Path): 输出目录
    """
    user_stats = []
    
    for original_file, enhanced_file, user_base in paired_files:
        # 加载数据
        orig_categories, orig_scores, orig_metadata = load_scores_data(str(original_file))
        enh_categories, enh_scores, enh_metadata = load_scores_data(str(enhanced_file))
        
        if orig_categories is None or enh_categories is None:
            continue
        
        # 确保分类顺序一致
        if orig_categories != enh_categories:
            common_categories = sorted(set(orig_categories) & set(enh_categories))
            orig_score_dict = dict(zip(orig_categories, orig_scores))
            enh_score_dict = dict(zip(enh_categories, enh_scores))
            
            orig_scores = [orig_score_dict[cat] for cat in common_categories]
            enh_scores = [enh_score_dict[cat] for cat in common_categories]
        
        # 计算统计数据
        improvements = [enh - orig for orig, enh in zip(orig_scores, enh_scores)]
        improved_count = sum(1 for imp in improvements if imp > 0)
        total_improvement = sum(imp for imp in improvements if imp > 0)
        avg_improvement = np.mean(improvements)
        
        user_stats.append({
            'user': user_base,
            'orig_avg': np.mean(orig_scores),
            'enh_avg': np.mean(enh_scores),
            'avg_improvement': avg_improvement,
            'improved_count': improved_count,
            'total_categories': len(orig_scores),
            'total_improvement': total_improvement
        })
    
    if not user_stats:
        print("没有可用的对比数据")
        return
    
    # 创建汇总图表
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    
    users = [stat['user'] for stat in user_stats]
    
    # 图1：平均分对比
    orig_avgs = [stat['orig_avg'] for stat in user_stats]
    enh_avgs = [stat['enh_avg'] for stat in user_stats]
    
    x = np.arange(len(users))
    width = 0.35
    
    ax1.bar(x - width/2, orig_avgs, width, label='原始版本', alpha=0.8, color='lightcoral')
    ax1.bar(x + width/2, enh_avgs, width, label='Enhanced版本', alpha=0.8, color='lightgreen')
    ax1.set_title('各用户平均评分对比', fontweight='bold')
    ax1.set_ylabel('平均评分')
    ax1.set_xticks(x)
    ax1.set_xticklabels(users, rotation=45)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 图2：改进幅度
    improvements = [stat['avg_improvement'] for stat in user_stats]
    colors = ['green' if imp > 0 else 'red' for imp in improvements]
    ax2.bar(users, improvements, color=colors, alpha=0.7)
    ax2.set_title('平均改进幅度', fontweight='bold')
    ax2.set_ylabel('平均改进分数')
    ax2.set_xticklabels(users, rotation=45)
    ax2.axhline(y=0, color='black', linestyle='-', alpha=0.5)
    ax2.grid(True, alpha=0.3)
    
    # 图3：改进分类数量
    improved_counts = [stat['improved_count'] for stat in user_stats]
    total_counts = [stat['total_categories'] for stat in user_stats]
    improvement_ratios = [ic/tc*100 for ic, tc in zip(improved_counts, total_counts)]
    
    ax3.bar(users, improvement_ratios, color='skyblue', alpha=0.7)
    ax3.set_title('改进分类比例 (%)', fontweight='bold')
    ax3.set_ylabel('改进比例 (%)')
    ax3.set_xticklabels(users, rotation=45)
    ax3.grid(True, alpha=0.3)
    
    # 图4：总改进分数
    total_improvements = [stat['total_improvement'] for stat in user_stats]
    ax4.bar(users, total_improvements, color='gold', alpha=0.7)
    ax4.set_title('总改进分数', fontweight='bold')
    ax4.set_ylabel('总改进分数')
    ax4.set_xticklabels(users, rotation=45)
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # 保存汇总图表
    summary_path = output_dir / "all_users_comparison_summary.png"
    plt.savefig(str(summary_path), dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"已生成汇总对比图表: {summary_path}")
    
    # 打印统计摘要
    print("\n=== Enhanced版本改进效果摘要 ===")
    for stat in user_stats:
        print(f"{stat['user']}: 平均分 {stat['orig_avg']:.1f} → {stat['enh_avg']:.1f} "
              f"(+{stat['avg_improvement']:.1f}) | "
              f"改进分类 {stat['improved_count']}/{stat['total_categories']} "
              f"({stat['improved_count']/stat['total_categories']*100:.1f}%)")
    
    overall_avg_improvement = np.mean([stat['avg_improvement'] for stat in user_stats])
    overall_improvement_ratio = np.mean([stat['improved_count']/stat['total_categories'] for stat in user_stats]) * 100
    print(f"\n整体效果: 平均改进 {overall_avg_improvement:.2f}分 | 平均改进比例 {overall_improvement_ratio:.1f}%")

def main():
    """
    主函数
    """
    # detailed_scores文件夹路径
    detailed_scores_dir = Path(r"c:\Users\admin\Desktop\ARXIV_daily_article_summary\data\users\detailed_scores")
    
    if not detailed_scores_dir.exists():
        print(f"错误：文件夹不存在 {detailed_scores_dir}")
        return
    
    # 创建输出目录
    output_dir = detailed_scores_dir / "comparisons"
    output_dir.mkdir(exist_ok=True)
    
    # 查找配对文件
    print("正在查找配对文件...")
    paired_files = find_paired_files(detailed_scores_dir)
    
    if not paired_files:
        print("未找到任何配对的文件")
        return
    
    print(f"找到 {len(paired_files)} 组配对文件")
    
    # 生成单个用户对比图表
    print("\n正在生成单个用户对比图表...")
    successful_count = 0
    for original_file, enhanced_file, user_base in paired_files:
        print(f"处理用户: {user_base}")
        if create_comparison_chart(original_file, enhanced_file, user_base, output_dir):
            successful_count += 1
    
    print(f"成功生成 {successful_count} 个用户对比图表")
    
    # 生成汇总对比图表
    print("\n正在生成汇总对比图表...")
    create_summary_chart(paired_files, output_dir)
    
    print(f"\n所有图表已保存到: {output_dir}")

if __name__ == "__main__":
    main()