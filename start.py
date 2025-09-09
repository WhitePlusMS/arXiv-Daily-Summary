#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ArXiv 每日论文推荐系统启动脚本 (PyEnv + NV 专用版本)
"""

import os
import sys
import subprocess
import platform
import argparse
from pathlib import Path
from typing import Optional


class Logger:
    """简单的日志输出类"""
    
    @staticmethod
    def info(message: str):
        print(f"ℹ️  {message}")
    
    @staticmethod
    def success(message: str):
        print(f"✅ {message}")
    
    @staticmethod
    def warning(message: str):
        print(f"⚠️  {message}")
    
    @staticmethod
    def error(message: str):
        print(f"❌ {message}")
    
    @staticmethod
    def header(message: str):
        print(f"\n{'='*60}")
        print(f"🚀 {message}")
        print(f"{'='*60}\n")


class PyEnvNVLauncher:
    """PyEnv + NV 专用启动器 - 第一性原理重构版"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.python_version_file = self.project_root / ".python-version"
        self.requirements_file = self.project_root / "requirements.txt"
        self.main_file = self.project_root / "ArXiv 每日论文推荐系统.py"
        self.env_file = self.project_root / ".env"
        self.venv_path = self.project_root / ".venv"
        
        # 严格定义虚拟环境中的可执行文件路径
        if platform.system() == "Windows":
            self.venv_python = self.venv_path / "Scripts" / "python.exe"
            self.venv_pip = self.venv_path / "Scripts" / "pip.exe"
        else:
            self.venv_python = self.venv_path / "bin" / "python"
            self.venv_pip = self.venv_path / "bin" / "pip"
    
    def is_docker_environment(self) -> bool:
        """检测是否在Docker环境中运行"""
        return os.environ.get('IS_DOCKER_ENV', '').lower() == 'true'
    
    def check_pyenv_installation(self) -> bool:
        """检查PyEnv是否正确安装"""
        Logger.info("检查PyEnv安装状态...")
        
        try:
            result = subprocess.run(["pyenv", "--version"], 
                                  capture_output=True, text=True, check=True, shell=True)
            version = result.stdout.strip()
            Logger.success(f"PyEnv已安装: {version}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            Logger.error("PyEnv未安装或未正确配置！")
            Logger.error("请先安装PyEnv: https://github.com/pyenv/pyenv")
            Logger.error("Windows用户请使用: https://github.com/pyenv-win/pyenv-win")
            return False
    
    def check_python_version_file(self) -> Optional[str]:
        """检查.python-version文件"""
        Logger.info("检查Python版本配置...")
        
        if not self.python_version_file.exists():
            Logger.error(".python-version文件不存在！")
            Logger.error("请在项目根目录创建.python-version文件并指定Python版本")
            Logger.error("例如: echo '3.12.10' > .python-version")
            return None
        
        try:
            python_version = self.python_version_file.read_text().strip()
            Logger.success(f"项目Python版本: {python_version}")
            return python_version
        except Exception as e:
            Logger.error(f"读取.python-version文件失败: {e}")
            return None
    
    def check_pyenv_python_version(self, required_version: str) -> bool:
        """检查PyEnv中是否安装了所需的Python版本"""
        Logger.info(f"检查PyEnv中的Python {required_version}...")
        
        try:
            result = subprocess.run(["pyenv", "versions"], 
                                  capture_output=True, text=True, check=True, shell=True)
            installed_versions = result.stdout
            
            if required_version in installed_versions:
                Logger.success(f"Python {required_version} 已安装")
                return True
            else:
                Logger.error(f"Python {required_version} 未安装！")
                Logger.error(f"请使用以下命令安装: pyenv install {required_version}")
                return False
        except subprocess.CalledProcessError as e:
            Logger.error(f"检查PyEnv版本失败: {e}")
            return False
    
    def check_current_python_version(self, required_version: str) -> bool:
        """检查当前激活的Python版本"""
        Logger.info("检查当前Python版本...")
        
        try:
            result = subprocess.run(["pyenv", "version"], 
                                  capture_output=True, text=True, check=True, shell=True)
            current_info = result.stdout.strip()
            
            if required_version in current_info:
                Logger.success(f"当前Python版本正确: {current_info}")
                return True
            else:
                Logger.warning(f"当前Python版本不匹配: {current_info}")
                Logger.info(f"正在切换到Python {required_version}...")
                
                subprocess.run(["pyenv", "local", required_version], check=True, shell=True)
                Logger.success(f"已切换到Python {required_version}")
                return True
        except subprocess.CalledProcessError as e:
            Logger.error(f"检查或设置Python版本失败: {e}")
            return False
    
    def check_nv_virtual_environment(self, auto_init: bool = False) -> bool:
        """严格检查NV虚拟环境状态，支持自动初始化"""
        Logger.info("检查NV虚拟环境状态...")
        
        # 第一性原理：必须同时满足以下条件
        # 1. VIRTUAL_ENV环境变量指向项目.venv目录
        # 2. .venv目录存在且包含必要的Python可执行文件
        # 3. 当前运行的Python来自.venv环境
        
        virtual_env = os.environ.get('VIRTUAL_ENV')
        expected_venv_path = str(self.venv_path.resolve())
        
        # 检查.venv目录是否存在
        if not self.venv_path.exists():
            Logger.warning("项目.venv目录不存在！")
            
            if auto_init:
                Logger.info("自动初始化模式：尝试创建虚拟环境...")
                if self.auto_create_venv():
                    Logger.success("虚拟环境创建成功！")
                    Logger.warning("⚠️  重要提示：虚拟环境已创建，但尚未激活")
                    Logger.warning("请按以下步骤激活虚拟环境后重新运行脚本：")
                    self._show_nv_activation_guide()
                    return False
                else:
                    Logger.error("自动创建虚拟环境失败")
                    self._show_nv_creation_guide()
                    return False
            else:
                Logger.error("请使用NV创建虚拟环境")
                self._show_nv_creation_guide()
                return False
        
        # 检查虚拟环境中的Python可执行文件
        if not self.venv_python.exists():
            Logger.error(f"虚拟环境Python可执行文件不存在: {self.venv_python}")
            Logger.error("虚拟环境可能已损坏，请重新创建")
            self._show_nv_creation_guide()
            return False
        
        # 检查环境变量
        if not virtual_env:
            Logger.warning("VIRTUAL_ENV环境变量未设置！")
            Logger.warning("NV虚拟环境未激活")
            
            if auto_init:
                Logger.info("💡 检测到虚拟环境存在但未激活")
                Logger.info("请按以下步骤激活虚拟环境后重新运行脚本：")
                self._show_nv_activation_guide()
                return False
            else:
                self._show_nv_activation_guide()
                return False
        
        # 检查环境变量是否指向正确的.venv目录
        if Path(virtual_env).resolve() != self.venv_path.resolve():
            Logger.error(f"VIRTUAL_ENV指向错误的目录: {virtual_env}")
            Logger.error(f"期望的目录: {expected_venv_path}")
            Logger.error("请确保激活的是项目目录下的.venv环境")
            self._show_nv_activation_guide()
            return False
        
        Logger.success(f"NV虚拟环境已正确激活: {virtual_env}")
        Logger.success(f"Python可执行文件: {self.venv_python}")
        return True
    
    def _show_nv_activation_guide(self):
        """显示NV激活指导"""
        Logger.error("请按以下步骤激活NV虚拟环境:")
        Logger.error(f"  cd {self.project_root}")
        Logger.error("  nv activate")
        Logger.error("  python start.py")
    
    def _show_nv_creation_guide(self):
        """显示NV创建指导"""
        Logger.error("请按以下步骤创建NV虚拟环境:")
        Logger.error(f"  cd {self.project_root}")
        Logger.error("  nv create")
        Logger.error("  nv activate")
        Logger.error("  python start.py")
    
    def auto_create_venv(self) -> bool:
        """自动创建虚拟环境"""
        Logger.info("检测到虚拟环境不存在，正在自动创建...")
        
        try:
            # 使用nv create命令创建虚拟环境
            Logger.info("执行: nv create")
            result = subprocess.run(["nv", "create"], 
                                  cwd=self.project_root, 
                                  capture_output=True, 
                                  text=True, 
                                  check=True)
            
            Logger.success("虚拟环境创建成功！")
            Logger.info("输出信息:")
            if result.stdout:
                Logger.info(result.stdout.strip())
            
            # 验证虚拟环境是否创建成功
            if self.venv_path.exists() and self.venv_python.exists():
                Logger.success(f"虚拟环境已创建: {self.venv_path}")
                Logger.success(f"Python可执行文件: {self.venv_python}")
                return True
            else:
                Logger.error("虚拟环境创建后验证失败")
                return False
                
        except subprocess.CalledProcessError as e:
            Logger.error(f"创建虚拟环境失败: {e}")
            if e.stderr:
                Logger.error(f"错误信息: {e.stderr.strip()}")
            Logger.error("可能的原因:")
            Logger.error("1. nv命令未正确安装")
            Logger.error("2. 当前目录权限不足")
            Logger.error("3. Python版本配置问题")
            return False
        except FileNotFoundError:
            Logger.error("nv命令未找到！")
            Logger.error("请确保已正确安装NV工具")
            return False
    
    def verify_venv_python(self) -> bool:
        """验证虚拟环境中的Python版本"""
        Logger.info("验证虚拟环境Python版本...")
        
        try:
            # 使用虚拟环境中的Python检查版本
            result = subprocess.run([str(self.venv_python), "--version"], 
                                  capture_output=True, text=True, check=True)
            venv_python_version = result.stdout.strip()
            Logger.success(f"虚拟环境Python版本: {venv_python_version}")
            
            # 读取期望的版本
            expected_version = self.python_version_file.read_text().strip()
            if expected_version in venv_python_version:
                Logger.success("虚拟环境Python版本与配置一致")
                return True
            else:
                Logger.warning(f"虚拟环境Python版本与配置不一致，期望: {expected_version}")
                Logger.warning("建议重新创建虚拟环境以确保版本一致")
                return True  # 不强制要求完全一致，但给出警告
        except subprocess.CalledProcessError as e:
            Logger.error(f"验证虚拟环境Python失败: {e}")
            return False
    
    def install_dependencies(self) -> bool:
        """在虚拟环境中安装项目依赖"""
        if not self.requirements_file.exists():
            Logger.error("requirements.txt文件不存在！")
            return False
        
        Logger.info("在虚拟环境中安装项目依赖...")
        Logger.info("这可能需要几分钟时间，请耐心等待...")
        
        try:
            # 第一性原理：直接使用虚拟环境中的Python和pip
            # 绝不使用系统级工具，避免环境混乱
            
            # 首先确保pip可用
            Logger.info("检查虚拟环境中的pip...")
            result = subprocess.run([str(self.venv_python), "-m", "pip", "--version"], 
                                  capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode != 0:
                Logger.warning("虚拟环境中pip损坏，尝试修复...")
                Logger.info("使用ensurepip重新安装pip...")
                try:
                    # 使用ensurepip重新安装pip
                    subprocess.run([str(self.venv_python), "-m", "ensurepip", "--upgrade"], 
                                 check=True, cwd=self.project_root)
                    
                    # 再次检查pip
                    result = subprocess.run([str(self.venv_python), "-m", "pip", "--version"], 
                                          capture_output=True, text=True, cwd=self.project_root)
                    
                    if result.returncode != 0:
                        raise RuntimeError("pip修复失败")
                    
                    Logger.success("pip修复成功！")
                    
                except subprocess.CalledProcessError as e:
                    Logger.error("pip修复失败！")
                    Logger.error("虚拟环境可能已损坏，请重新创建")
                    self._show_nv_creation_guide()
                    return False
            
            pip_version = result.stdout.strip()
            Logger.success(f"虚拟环境pip版本: {pip_version}")
            
            # 检查pip版本并给出友好提示（不强制升级）
            self._check_pip_version_and_suggest(pip_version)
            
            # 直接安装依赖（在虚拟环境中）
            Logger.info("安装项目依赖到虚拟环境...")
            subprocess.run([str(self.venv_python), "-m", "pip", "install", "-r", "requirements.txt"], 
                         check=True, cwd=self.project_root)
            
            Logger.success("依赖安装完成（已安装到虚拟环境）")
            return True
            
        except subprocess.CalledProcessError as e:
            Logger.error(f"依赖安装失败: {e}")
            Logger.error("可能的原因：")
            Logger.error("1. 网络连接问题")
            Logger.error("2. requirements.txt文件格式错误")
            Logger.error("3. 虚拟环境已损坏，请重新创建")
            Logger.error("4. Python版本不兼容")
            return False
    
    def _check_pip_version_and_suggest(self, pip_version_output: str):
        """检查pip版本并给出升级建议（不强制升级）"""
        try:
            # 提取版本号
            import re
            version_match = re.search(r'pip (\d+\.\d+\.\d+)', pip_version_output)
            if not version_match:
                return
            
            current_version = version_match.group(1)
            version_parts = [int(x) for x in current_version.split('.')]
            
            # 检查是否为较旧版本（例如低于21.0.0）
            if version_parts[0] < 21:
                Logger.warning(f"检测到较旧的pip版本: {current_version}")
                Logger.info("💡 建议升级pip以获得更好的性能和安全性：")
                Logger.info(f"   {self.venv_python} -m pip install --upgrade pip")
                Logger.info("   （可选操作，当前版本仍可正常使用）")
            elif version_parts[0] < 23:
                Logger.info(f"💡 pip版本 {current_version} 可用，如需最新功能可考虑升级：")
                Logger.info(f"   {self.venv_python} -m pip install --upgrade pip")
            else:
                Logger.success(f"pip版本 {current_version} 较新，无需升级")
                
        except Exception:
            # 如果版本解析失败，不影响主流程
            pass
    
    def check_main_file(self) -> bool:
        """检查主程序文件"""
        if not self.main_file.exists():
            Logger.error(f"主程序文件 '{self.main_file.name}' 不存在！")
            return False
        return True
    
    def check_env_file(self):
        """检查环境配置文件"""
        if not self.env_file.exists():
            Logger.warning(".env配置文件不存在！")
            Logger.warning("请先配置环境变量，或通过Web界面进行配置")
            Logger.warning("可以复制.env.example为.env并修改配置")
    
    def check_port_available(self, port: int) -> bool:
        """检查端口是否可用"""
        import socket
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return True
        except OSError:
            return False
    
    def find_available_port(self, start_port: int = 8501, max_attempts: int = 10) -> int:
        """寻找可用端口，从start_port开始依次尝试"""
        for port in range(start_port, start_port + max_attempts):
            if self.check_port_available(port):
                return port
        return 0  # 如果都被占用，返回0让Streamlit自动选择
    
    def run_docker_mode(self, host: str = "0.0.0.0", port: int = 8501, dev_mode: bool = False) -> bool:
        """Docker环境下的简化启动流程"""
        Logger.header("ArXiv 每日论文推荐系统 启动脚本 (Docker模式)")
        Logger.info(f"当前工作目录: {self.project_root}")
        Logger.info("环境管理方式: Docker容器 (系统Python)")
        Logger.info("设计原则: Docker环境隔离 - 跳过PyEnv/NV检查")
        print()
        
        # 1. 检查主程序文件
        if not self.check_main_file():
            return False
        
        # 2. 检查环境配置文件
        self.check_env_file()
        print()
        
        # 3. 使用系统Python启动应用
        return self.start_streamlit_docker(host, port, dev_mode)
    
    def start_streamlit_docker(self, host: str = "0.0.0.0", port: int = 8501, dev_mode: bool = False) -> bool:
        """Docker环境下使用系统Python启动Streamlit应用"""
        Logger.info("准备启动Streamlit应用 (Docker模式)...")
        
        # 智能端口分配策略
        original_port = port
        if not self.check_port_available(port):
            Logger.warning(f"端口{port}已被占用，正在寻找可用端口...")
            port = self.find_available_port(port + 1)
            
            if port == 0:
                Logger.warning("未找到可用端口，让Streamlit自动分配")
            else:
                Logger.success(f"找到可用端口: {port}")
        
        # Docker环境：使用系统Python
        cmd = [
            sys.executable, "-m", "streamlit", "run",
            str(self.main_file),
            "--server.headless", "true",
            "--server.address", host,
            "--server.port", str(port),
            "--browser.gatherUsageStats", "false"
        ]
        
        if dev_mode:
            cmd.extend(["--server.runOnSave", "true"])
            cmd.extend(["--server.fileWatcherType", "auto"])
        
        Logger.info(f"使用系统Python: {sys.executable}")
        
        # 正确显示访问地址
        if port == 0:
            Logger.info("浏览器将自动打开 http://localhost:自动分配")
            Logger.info("实际端口将在启动后显示")
        else:
            Logger.info(f"浏览器将自动打开 http://{host}:{port}")
        
        Logger.info("按Ctrl+C停止服务")
        Logger.header("系统启动中...")
        
        try:
            if port == 0:
                Logger.info("提示: 由于使用自动端口分配，请查看下方输出获取实际访问地址")
            
            subprocess.run(cmd, cwd=self.project_root, check=True)
            return True
        except subprocess.CalledProcessError as e:
            Logger.error(f"Streamlit启动失败: {e}")
            Logger.error("可能的原因：")
            Logger.error("1. 端口被占用或配置错误")
            Logger.error("2. Streamlit未正确安装")
            Logger.error("3. 主程序文件存在问题")
            return False
        except KeyboardInterrupt:
            Logger.info("\n应用已关闭")
            return True
    
    def start_streamlit(self, host: str = "localhost", port: int = 8501, dev_mode: bool = False) -> bool:
        """使用虚拟环境中的Python启动Streamlit应用"""
        Logger.info("启动ArXiv推荐系统...")
        
        # 智能端口分配策略
        original_port = port
        if not self.check_port_available(port):
            Logger.warning(f"端口{port}已被占用，正在寻找可用端口...")
            port = self.find_available_port(port + 1)  # 从下一个端口开始找
            
            if port == 0:
                Logger.warning("未找到可用端口，让Streamlit自动分配")
            else:
                Logger.success(f"找到可用端口: {port}")
        
        # 第一性原理：严格使用虚拟环境中的Python
        cmd = [
            str(self.venv_python), "-m", "streamlit", "run",
            str(self.main_file),
            "--server.headless", "true",
            "--server.address", host,
            "--server.port", str(port),
            "--browser.gatherUsageStats", "false"
        ]
        
        if dev_mode:
            cmd.extend(["--server.runOnSave", "true"])
            cmd.extend(["--server.fileWatcherType", "auto"])
        
        Logger.info(f"使用虚拟环境Python: {self.venv_python}")
        
        # 正确显示访问地址
        if port == 0:
            Logger.info("浏览器将自动打开 http://localhost:自动分配")
            Logger.info("实际端口将在启动后显示")
        else:
            Logger.info(f"浏览器将自动打开 http://{host}:{port}")
        
        Logger.info("按Ctrl+C停止服务")
        
        Logger.header("系统启动中...")
        
        try:
            # 如果使用自动端口分配，提供额外提示
            if port == 0:
                Logger.info("提示: 由于使用自动端口分配，请查看下方输出获取实际访问地址")
            
            subprocess.run(cmd, cwd=self.project_root, check=True)
            return True
        except subprocess.CalledProcessError as e:
            Logger.error(f"Streamlit启动失败: {e}")
            Logger.error("可能的原因：")
            if original_port != port:
                Logger.error(f"1. 原始端口{original_port}被占用，尝试的替代端口也可能有问题")
            else:
                Logger.error("1. 端口被占用或配置错误")
            Logger.error("2. 依赖包未正确安装到虚拟环境")
            Logger.error("3. NV虚拟环境未正确激活")
            Logger.error("4. 虚拟环境已损坏，请重新创建")
            return False
        except KeyboardInterrupt:
            Logger.info("\n应用已关闭")
            return True
    
    def run(self, host: str = "localhost", port: int = 8501, 
           dev_mode: bool = False, auto_init: bool = False) -> bool:
        """运行启动流程 - 第一性原理版本"""
        # Docker环境检测 - 如果在Docker环境中，使用简化启动流程
        if self.is_docker_environment():
            # Docker环境下使用0.0.0.0以允许外部访问
            return self.run_docker_mode("0.0.0.0", port, dev_mode)
        
        # Windows原生启动流程（保持不变）
        if auto_init:
            Logger.header("ArXiv 每日论文推荐系统 启动脚本 (PyEnv+NV专用 - 自动初始化模式)")
        else:
            Logger.header("ArXiv 每日论文推荐系统 启动脚本 (PyEnv+NV专用 - 第一性原理版)")
        
        Logger.info(f"当前工作目录: {self.project_root}")
        Logger.info("环境管理方式: PyEnv + NV (严格模式)")
        Logger.info("设计原则: 第一性原理 - 绝不使用系统级Python/pip")
        if auto_init:
            Logger.info("🚀 自动初始化模式：将尝试自动创建缺失的虚拟环境")
        print()
        
        # 1. 检查PyEnv安装
        if not self.check_pyenv_installation():
            return False
        print()
        
        # 2. 检查Python版本配置
        required_version = self.check_python_version_file()
        if not required_version:
            return False
        print()
        
        # 3. 检查PyEnv中的Python版本
        if not self.check_pyenv_python_version(required_version):
            return False
        print()
        
        # 4. 检查当前Python版本
        if not self.check_current_python_version(required_version):
            return False
        print()
        
        # 5. 严格检查NV虚拟环境（支持自动初始化）
        if not self.check_nv_virtual_environment(auto_init):
            if auto_init:
                Logger.info("💡 提示：虚拟环境已创建但需要手动激活")
                Logger.info("请按照上述提示激活虚拟环境后重新运行脚本")
            return False
        print()
        
        # 6. 验证虚拟环境中的Python
        if not self.verify_venv_python():
            return False
        print()
        
        # 7. 在虚拟环境中安装依赖
        if not self.install_dependencies():
            return False
        print()
        
        # 8. 检查主程序文件
        if not self.check_main_file():
            return False
        
        # 9. 检查环境配置文件
        self.check_env_file()
        print()
        
        # 10. 使用虚拟环境启动应用
        return self.start_streamlit(host, port, dev_mode)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="ArXiv 每日论文推荐系统启动脚本 (PyEnv+NV专用 - 第一性原理版)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""

使用前提条件:
  1. 已安装PyEnv和NV
  2. 项目根目录存在.python-version文件
  3. 已使用NV创建并激活虚拟环境
  4. 当前终端的VIRTUAL_ENV指向项目.venv目录

示例用法:
  python start.py                    # 默认启动 (localhost:8501)
  python start.py --port 8502        # 指定端口
  python start.py --host 0.0.0.0     # 允许外部访问
  python start.py --dev              # 开发模式
  python start.py --init             # 自动初始化模式（首次使用推荐）

首次使用推荐步骤:
  cd 项目目录
  python start.py --init             # 自动创建虚拟环境
  nv activate                        # 激活虚拟环境
  python start.py                    # 启动应用

手动环境创建步骤:
  cd 项目目录
  nv create      # 创建虚拟环境
  nv activate    # 激活虚拟环境
  python start.py # 启动应用
        """
    )
    
    parser.add_argument(
        "--host", 
        default="localhost", 
        help="服务器地址 (默认: localhost)"
    )
    
    parser.add_argument(
        "--port", 
        type=int, 
        default=8501, 
        help="服务器端口 (默认: 8501)"
    )
    
    parser.add_argument(
        "--dev", 
        action="store_true", 
        help="开发模式，启用文件监控和自动重载"
    )
    
    parser.add_argument(
        "--init", 
        action="store_true", 
        help="自动初始化模式，当虚拟环境不存在时自动创建"
    )
    
    args = parser.parse_args()
    
    launcher = PyEnvNVLauncher()
    success = launcher.run(args.host, args.port, args.dev, args.init)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()