#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分类浏览器UI组件 - ArXiv分类浏览器专用的界面渲染组件
"""

import streamlit as st


def render_category_browser_header():
    """渲染分类浏览器页面头部"""
    # 设置页面配置
    st.set_page_config(
        page_title="ArXiv分类浏览器",
        page_icon="📖",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # 增强版标题和简介
    st.markdown("""
    <div style='text-align: center; padding: 1rem 0; width: 100%;'>
        <h1 style='color: #1e40af; margin-bottom: 0.5rem; font-size: 3rem; font-weight: 700;'>
            📚 ArXiv 学术分类
        </h1>
        <div style='color: #4b5563; font-size: 1.3rem; line-height: 1.6; margin-bottom: 1rem;'>
            探索完整的 ArXiv 学术分类体系，发现你的研究领域
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_statistics_card(categories):
    """渲染统计卡片
    
    Args:
        categories: 分类数据列表
    """
    total_main = len(categories)
    total_sub = sum(len(cat['subcategories']) for cat in categories)
    
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #f8fafc, #f1f5f9); padding: 1.5rem; border-radius: 20px; margin: 1rem 0 2rem 0; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);'>
        <div style='display: flex; justify-content: space-around; text-align: center; gap: 2rem; max-width: 800px; margin: 0 auto;'>
            <div style='flex: 1;'>
                <div style='font-size: 2.5rem; font-weight: 700; color: #2563eb; margin-bottom: 0.5rem;'>{total_main}</div>
                <div style='color: #4b5563; font-size: 1.2rem; font-weight: 500;'>主要学术领域</div>
            </div>
            <div style='width: 1px; background: #d1d5db;'></div>
            <div style='flex: 1;'>
                <div style='font-size: 2.5rem; font-weight: 700; color: #059669; margin-bottom: 0.5rem;'>{total_sub}</div>
                <div style='color: #4b5563; font-size: 1.2rem; font-weight: 500;'>具体研究方向</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_category_section(main_cat):
    """渲染单个主分类区域
    
    Args:
        main_cat: 主分类数据
    """
    with st.expander(f"📁 **{main_cat['main_category']}** ({len(main_cat['subcategories'])}个研究方向)", expanded=False):
        st.markdown(f"""
        <div style='background: #f8fafc; padding: 0.8rem; border-radius: 12px; margin-bottom: 0.8rem;'>
            <h3 style='color: #1e40af; margin-bottom: 0.3rem; font-size: 1.3rem;'>
                📚 {main_cat['main_category']} 
            </h3>
            <p style='color: #4b5563; font-size: 1.1rem; margin: 0;'>
                该领域包含 {len(main_cat['subcategories'])} 个具体研究方向，涵盖相关学科的主要研究领域。
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        for subcat in main_cat['subcategories']:
            render_subcategory_card(subcat)


def render_subcategory_card(subcat):
    """渲染子分类卡片
    
    Args:
        subcat: 子分类数据
    """
    st.markdown(f"""
    <div style='background: white; border: 1px solid #e5e7eb; border-radius: 12px; padding: 1rem; margin: 0.5rem 0; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);'>
        <div style='display: flex; align-items: flex-start; gap: 1rem; margin-bottom: 0.8rem;'>
            <div style='background: linear-gradient(135deg, #eff6ff, #dbeafe); color: #1e40af; padding: 0.4rem 0.8rem; border-radius: 8px; font-family: 'Monaco', 'Menlo', monospace; font-size: 1.1rem; font-weight: 700; min-width: 70px; text-align: center;'>
                {subcat['id']}
            </div>
            <div style='flex: 1;'>
                <h4 style='font-weight: 700; color: #111827; font-size: 1.3rem; margin: 0 0 0.3rem 0;'>
                    {subcat['name']} ({subcat.get('name_cn', '')})
                </h4>
            </div>
        </div>
        <div style='color: #374151; line-height: 1.6; font-size: 1.15rem; margin-left: 0;'>
            {subcat['description']}
        </div>
        <div style='color: #4b5563; line-height: 1.6; font-size: 1.05rem; margin-left: 0; margin-top: 0.5rem; border-top: 1px solid #e5e7eb; padding-top: 0.5rem;'>
            {subcat.get('description_cn', '')}
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_usage_guide():
    """渲染使用指南"""
    st.markdown("""
    <div style='text-align: center; padding: 1.5rem; margin-top: 2rem;'>
        <div style='background: linear-gradient(135deg, #eff6ff, #dbeafe); padding: 1.2rem; border-radius: 16px; max-width: 800px; margin: 0 auto;'>
            <h3 style='color: #1e40af; font-size: 1.2rem; margin-bottom: 0.8rem;'>💡 使用指南</h3>
            <p style='color: #374151; font-size: 1.1rem; line-height: 1.6; margin: 0;'>
                点击上方的 📁 展开按钮查看每个学术领域的详细分类信息。支持使用浏览器的 <kbd>Ctrl+F</kbd> 或 <kbd>Cmd+F</kbd> 
                进行页面内搜索，快速定位你感兴趣的研究方向。<br><br>
                原文详见 <a href='https://arxiv.org/category_taxonomy' target='_blank' style='color: #2563eb; text-decoration: none; font-weight: 500;'>https://arxiv.org/category_taxonomy</a>
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)