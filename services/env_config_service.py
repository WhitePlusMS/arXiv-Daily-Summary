#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境配置服务 - 业务逻辑层
"""

import os
import sys
import re
import streamlit as st
from typing import Dict, Any
from pathlib import Path


class EnvConfigManager:
    """环境配置管理器"""
    
    def __init__(self):
        # 获取项目根目录的绝对路径
        # 动态计算项目根目录
        project_root = Path(__file__).parent.parent
        # 将项目根目录添加到sys.path
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        self.env_file = project_root / ".env"
        self.env_example_file = project_root / ".env.example"
        self.config = {}
        self.load_config()
    
    def load_config(self):
        """加载当前配置"""
        if self.env_file.exists():
            with open(self.env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        self.config[key.strip()] = value.strip()
    
    def save_config(self, new_config: Dict[str, Any]) -> bool:
        """保存配置到.env文件"""
        try:
            # 确保父目录存在
            self.env_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 读取原文件保留注释和格式
            lines = []
            if self.env_file.exists():
                with open(self.env_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
            
            # 更新配置值
            updated_lines = []
            updated_keys = set()
            
            for line in lines:
                stripped = line.strip()
                if stripped and not stripped.startswith('#') and '=' in stripped:
                    key = stripped.split('=', 1)[0].strip()
                    if key in new_config:
                        updated_lines.append(f"{key}={new_config[key]}\n")
                        updated_keys.add(key)
                    else:
                        updated_lines.append(line)
                else:
                    updated_lines.append(line)
            
            # 添加新的配置项
            for key, value in new_config.items():
                if key not in updated_keys:
                    updated_lines.append(f"{key}={value}\n")
            
            # 写入文件
            with open(self.env_file, 'w', encoding='utf-8') as f:
                f.writelines(updated_lines)
            
            # 验证写入是否成功
            if not self.env_file.exists():
                raise FileNotFoundError(f"配置文件写入失败: {self.env_file}")
            
            # 重新加载配置以验证
            self.load_config()
            
            # 强制重新加载环境变量到当前进程
            from dotenv import load_dotenv
            load_dotenv(self.env_file, override=True)
            
            # 清除Streamlit缓存以确保其他页面重新加载
            if hasattr(st, 'cache_data'):
                st.cache_data.clear()
            if hasattr(st, 'cache_resource'):
                st.cache_resource.clear()
            
            return True
        except Exception as e:
            st.error(f"保存配置失败: {str(e)}")
            st.error(f"错误类型: {type(e).__name__}")
            st.error(f"文件路径: {self.env_file}")
            return False
    
    def load_example_config(self) -> Dict[str, str]:
        """加载示例配置"""
        example_config = {}
        if self.env_example_file.exists():
            with open(self.env_example_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        example_config[key.strip()] = value.strip()
        return example_config


def validate_email(email: str) -> bool:
    """验证邮箱格式"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_url(url: str) -> bool:
    """验证URL格式"""
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return re.match(pattern, url) is not None


def track_config_change(key: str, value: str) -> None:
    """跟踪配置更改并触发实时更新"""
    # 立即更新配置状态
    st.session_state.config_changes[key] = value
    
    # 创建跟踪键名
    track_key = f'last_{key.lower()}'
    
    # 强制触发状态更新检查
    if track_key not in st.session_state:
        st.session_state[track_key] = value
    elif st.session_state[track_key] != value:
        st.session_state[track_key] = value
        # 触发页面重新渲染以立即显示更改状态
        st.rerun()


def initialize_config_state(config_manager):
    """初始化配置状态"""
    # 每次都重新加载.env文件以确保获取最新配置
    config_manager.load_config()
    
    # 如果是第一次访问或强制重新加载，完全初始化session_state
    if 'config_changes' not in st.session_state or st.session_state.get('force_reload', False):
        st.session_state.config_changes = config_manager.config.copy()
        st.session_state.force_reload = False
        
        # 初始化所有配置项的上次值跟踪
        for key in config_manager.config:
            st.session_state[f'last_{key.lower()}'] = config_manager.config[key]
    else:
        # 如果session_state已存在，只更新文件中存在的配置项
        # 保持用户在界面上的未保存更改，但确保文件配置是最新的
        for key, value in config_manager.config.items():
            # 如果session_state中没有这个配置项，添加它
            if key not in st.session_state.config_changes:
                st.session_state.config_changes[key] = value
                st.session_state[f'last_{key.lower()}'] = value


def check_config_changes(config_manager):
    """检查配置更改状态"""
    # 实时状态监控 - 优化配置更改检测逻辑
    if 'config_changes' in st.session_state and config_manager.config:
        # 检查是否有未保存的更改 - 更严格的比较逻辑
        has_changes = False
        changed_keys = []
        
        # 遍历所有可能的配置项，包括session_state中的新增项
        all_keys = set(st.session_state.config_changes.keys()) | set(config_manager.config.keys())
        
        for key in all_keys:
            file_value = str(config_manager.config.get(key, '')).strip()
            session_value = str(st.session_state.config_changes.get(key, '')).strip()
            
            # 更严格的比较：确保类型一致性和值的准确比较
            if file_value != session_value:
                has_changes = True
                changed_keys.append(key)
        
        # 实时显示状态 - 立即响应任何更改
        if changed_keys:
            st.warning(f"⚠️ 有 {len(changed_keys)} 项配置未保存到文件")
            with st.expander(f"📋 查看所有 {len(changed_keys)} 项更改详情", expanded=False):
                for key in changed_keys:
                    file_val = config_manager.config.get(key, '')
                    session_val = st.session_state.config_changes.get(key, '')
                    
                    # 显示完整值，但限制显示长度以保持界面整洁
                    file_display = file_val[:30] + "..." if len(str(file_val)) > 30 else str(file_val)
                    session_display = session_val[:30] + "..." if len(str(session_val)) > 30 else str(session_val)
                    
                    st.write(f"  - **{key}**: 文件=`{file_display}` → 界面=`{session_display}`")
        else:
            st.success("✅ 所有配置已同步，无未保存更改")
            # 添加占位符区域，保持界面布局一致性
            with st.expander("📋 配置状态详情", expanded=False):
                st.info("🎉 当前所有配置项都已保存到 .env 文件中，界面与文件完全同步。")
                st.write("💡 **提示**: 修改任何配置项后，此区域将显示具体的更改详情。")


def handle_save_config(config_manager):
    """处理保存配置"""
    # 显示保存进度
    with st.spinner("正在保存配置到.env文件..."):
        # 立即保存配置到.env文件
        if config_manager.save_config(st.session_state.config_changes):
            # 重新加载环境变量确保生效
            config_manager.load_config()
            st.session_state.config_changes = config_manager.config.copy()
            
            st.rerun()
        else:
            st.error("❌ 配置保存失败！请检查文件权限或路径是否正确。")


def handle_reload_config(config_manager):
    """处理重新加载配置"""
    # 显示确认对话框
    if st.session_state.get('confirm_reload', False):
        st.warning("⚠️ 确认要重新加载配置吗？这将丢失所有未保存的更改。")
        col_confirm, col_cancel = st.columns(2)
        with col_confirm:
            if st.button("✅ 确认重新加载", type="primary", key="confirm_reload_btn"):
                # 显示重新加载进度
                with st.spinner("正在从.env文件重新加载配置..."):
                    # 完全丢弃用户修改，从.env文件重新加载
                    config_manager.load_config()
                    st.session_state.config_changes = config_manager.config.copy()
                    
                    # 显示详细的重新加载结果
                    st.success("✅ 配置重新加载成功！")
                    st.info(f"📂 已从 .env 文件重新加载 {len(config_manager.config)} 项配置")
                    st.info("🔄 所有未保存的界面更改已丢弃，恢复到文件中的配置")
                    
                    # 清除所有相关的session状态
                    st.session_state.force_reload = True
                    st.session_state.confirm_reload = False
                    st.rerun()
        with col_cancel:
            if st.button("❌ 取消", key="cancel_reload_btn"):
                st.session_state.confirm_reload = False
                st.rerun()
    else:
        st.session_state.confirm_reload = True
        st.rerun()


def handle_restore_default(config_manager):
    """处理恢复默认配置"""
    # 显示确认对话框
    if st.session_state.get('confirm_restore', False):
        st.warning("⚠️ 确认要恢复默认配置吗？这将丢失所有当前更改并使用.env.example中的默认值。")
        col_confirm, col_cancel = st.columns(2)
        with col_confirm:
            if st.button("✅ 确认恢复默认", type="primary", key="confirm_restore_btn"):
                # 显示恢复默认配置进度
                with st.spinner("正在恢复默认配置..."):
                    example_config = config_manager.load_example_config()
                    if example_config:
                        # 直接将默认配置写入.env文件
                        if config_manager.save_config(example_config):
                            # 重新加载配置确保生效
                            config_manager.load_config()
                            st.session_state.config_changes = config_manager.config.copy()
                            
                            # 显示详细的恢复结果
                            st.success("✅ 默认配置恢复成功！")
                            st.info(f"📋 已从 .env.example 加载 {len(example_config)} 项默认配置")
                            st.info(f"💾 默认配置已写入 .env 文件并重新加载")
                            st.info("🔄 所有配置已重置为默认值")
                            
                            st.session_state.confirm_restore = False
                            st.rerun()
                        else:
                            st.error("❌ 恢复默认配置失败！请检查文件权限。")
                            st.session_state.confirm_restore = False
                    else:
                        st.error("❌ 无法加载默认配置！请确保该文件存在于项目根目录。")
                        st.session_state.confirm_restore = False
        with col_cancel:
            if st.button("❌ 取消", key="cancel_restore_btn"):
                st.session_state.confirm_restore = False
                st.rerun()
    else:
        st.session_state.confirm_restore = True
        st.rerun()