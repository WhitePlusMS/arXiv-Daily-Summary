#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI + Web 前端联合启动脚本

功能目标：
1) 启动 FastAPI 后端服务（来自 fastapi_app:app）
2) 同时启动 web 目录下的前端（Vite/Vue）开发服务器
3) 在启动前进行完备环境检查（参考 start.py 的结构与设计）
4) 提供清晰的日志与引导信息，并支持常用 CLI 参数
"""

import os
import sys
import json
import time
import signal
import platform
import argparse
import subprocess
from pathlib import Path
from typing import Optional


class Logger:
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


def check_port_available(port: int) -> bool:
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', port))
            return True
    except OSError:
        return False


def find_available_port(start_port: int, max_attempts: int = 20) -> int:
    for p in range(start_port, start_port + max_attempts):
        if check_port_available(p):
            return p
    return 0


class FastAPIWebLauncher:
    def __init__(self):
        self.project_root = Path(os.path.dirname(os.path.abspath(__file__)))
        self.fastapi_module = "fastapi_app:app"
        self.web_dir = self.project_root / "web"
        self.python_version_file = self.project_root / ".python-version"
        self.env_file = self.project_root / ".env"
        self.venv_path = self.project_root / ".venv"

        if platform.system() == "Windows":
            self.venv_python = self.venv_path / "Scripts" / "python.exe"
        else:
            self.venv_python = self.venv_path / "bin" / "python"

        # Windows PowerShell 激活脚本路径（用于自动引导）
        self.activate_ps1 = self.venv_path / "Scripts" / "Activate.ps1"

        # 运行时子进程句柄
        self.backend_proc: Optional[subprocess.Popen] = None
        self.web_proc: Optional[subprocess.Popen] = None
        # Node/npm 可执行路径（Windows 上可能需要使用 npm.cmd）
        self.node_path: Optional[str] = None
        self.npm_path: Optional[str] = None

    # ===== 预引导：在 Windows 终端中自动激活 .venv 并重新运行当前脚本 =====
    def try_bootstrap_via_powershell(self, no_exit: bool = True) -> bool:
        """
        当检测到未在项目 .venv 中运行、且在 Windows 环境下时：
        - 若存在 .venv\\Scripts\\Activate.ps1，则启动一个 PowerShell 终端，按用户提供的命令激活 .venv
        - 显示 Python 版本，并自动继续运行本启动脚本（避免手动再次输入）
        - 返回 True 表示已启动新终端并进行引导，当前进程可安全退出
        """
        if platform.system() != "Windows":
            return False

        # 如果已在 .venv 中，则无需引导
        virtual_env = os.environ.get('VIRTUAL_ENV', '')
        try:
            if virtual_env and Path(virtual_env).resolve() == self.venv_path.resolve():
                return False
        except Exception:
            # 解析失败则继续尝试引导
            pass

        # 仅在激活脚本存在时才进行引导
        if not self.activate_ps1.exists():
            Logger.warning("未找到 PowerShell 激活脚本 .venv/\\Scripts/Activate.ps1，跳过自动引导")
            return False

        Logger.info("准备在新的 PowerShell 终端中激活 .venv 并重新运行启动脚本...")
        # 组装 PowerShell 命令（按用户示例融合，并自动继续运行脚本）
        ps_cmd = (
            "Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; "
            "& .\\.venv\\Scripts\\Activate.ps1; "
            "Write-Host '✅ 已激活 .venv'; "
            "python --version; "
            "Write-Host '提示：自动继续运行 python start_fastapi.py'; "
            "python .\\start_fastapi.py --no-bootstrap"
        )

        try:
            args = ["powershell", "-NoExit" if no_exit else "-Command", "-Command", ps_cmd]
            subprocess.Popen(args, cwd=self.project_root)
            Logger.success("已在新终端触发 .venv 激活与二次启动")
            return True
        except Exception as e:
            Logger.error(f"PowerShell 自动引导失败: {e}")
            return False

    # ===== 通用检查（参考 start.py 设计） =====
    def check_python_version_file(self) -> Optional[str]:
        if not self.python_version_file.exists():
            Logger.warning(".python-version 文件不存在（可选）")
            return None
        try:
            version = self.python_version_file.read_text().strip()
            if version:
                Logger.success(f"项目声明的 Python 版本: {version}")
            return version
        except Exception as e:
            Logger.error(f"读取 .python-version 失败: {e}")
            return None

    def check_nv_virtual_environment(self, auto_init: bool = False) -> bool:
        """
        参考 start.py 的 NV 环境检查逻辑：
        - 存在 .venv 目录且包含 Python 可执行文件
        - 如未激活，给予清晰的引导
        - 可选自动创建
        """
        Logger.info("检查 NV 虚拟环境状态...")

        if not self.venv_path.exists():
            Logger.warning("项目 .venv 目录不存在！")
            if auto_init:
                return self.auto_create_venv()
            else:
                self._show_nv_creation_guide()
                return False

        if not self.venv_python.exists():
            Logger.error(f"虚拟环境 Python 不存在: {self.venv_python}")
            self._show_nv_creation_guide()
            return False

        # 环境变量提示（不强制）
        virtual_env = os.environ.get('VIRTUAL_ENV', '')
        if not virtual_env:
            Logger.warning("VIRTUAL_ENV 未设置，可能未激活 .venv 环境")
            self._show_nv_activation_guide()
        else:
            try:
                if Path(virtual_env).resolve() != self.venv_path.resolve():
                    Logger.warning("当前激活的虚拟环境并非项目 .venv")
                    self._show_nv_activation_guide()
                else:
                    Logger.success(f"NV 虚拟环境已激活: {virtual_env}")
            except Exception:
                self._show_nv_activation_guide()

        return True

    def assert_running_in_venv(self) -> bool:
        """严格断言：必须在项目 .venv 中运行当前 Python"""
        Logger.info("验证当前 Python 是否来自项目 .venv 环境...")
        virtual_env = os.environ.get('VIRTUAL_ENV', '')
        expected_venv_path = str(self.venv_path.resolve())

        if not virtual_env:
            Logger.error("检测到未激活 NV 虚拟环境 (VIRTUAL_ENV 未设置)")
            self._show_nv_activation_guide()
            return False

        try:
            if Path(virtual_env).resolve() != self.venv_path.resolve():
                Logger.error(f"当前激活的虚拟环境不是项目 .venv: {virtual_env}")
                Logger.error(f"期望路径: {expected_venv_path}")
                self._show_nv_activation_guide()
                return False
        except Exception:
            Logger.error("无法解析当前虚拟环境路径")
            self._show_nv_activation_guide()
            return False

        # 校验当前 Python 解释器路径
        current_python = Path(sys.executable).resolve()
        venv_python = self.venv_python.resolve()
        if current_python != venv_python:
            Logger.error("当前 Python 并非来自项目 .venv 环境")
            Logger.error(f"当前: {current_python}")
            Logger.error(f"期望: {venv_python}")
            self._show_nv_activation_guide()
            return False

        Logger.success("已确认：当前运行环境为项目 .venv")
        return True

    def _show_nv_activation_guide(self):
        Logger.info("请在项目根目录执行以下命令激活 NV 环境：")
        Logger.info(f"  cd {self.project_root}")
        Logger.info("  nv activate")

    def _show_nv_creation_guide(self):
        Logger.info("如需创建 NV 虚拟环境，可执行：")
        Logger.info(f"  cd {self.project_root}")
        Logger.info("  nv create && nv activate")

    def auto_create_venv(self) -> bool:
        Logger.info("自动创建虚拟环境: nv create")
        try:
            subprocess.run(["nv", "create"], cwd=self.project_root, check=True, text=True, capture_output=True)
            if self.venv_path.exists() and self.venv_python.exists():
                Logger.success("虚拟环境创建成功！请执行 nv activate 后再次运行本脚本。")
                return True
            Logger.error("虚拟环境创建后验证失败")
            return False
        except FileNotFoundError:
            Logger.error("未检测到 nv 命令，请先安装 NV 工具")
            return False
        except subprocess.CalledProcessError as e:
            Logger.error(f"nv create 执行失败: {e}")
            return False

    def check_env_file(self):
        if not self.env_file.exists():
            Logger.warning(".env 配置文件不存在（可选）")

    # ===== 后端（FastAPI）检查与启动 =====
    def check_backend_entry(self) -> bool:
        entry_file = self.project_root / "fastapi_app.py"
        if not entry_file.exists():
            Logger.error("后端入口 fastapi_app.py 不存在！")
            return False
        Logger.success("已找到后端入口 fastapi_app.py")
        return True

    def start_backend(self, host: str, port: int, reload: bool, log_level: str = "info") -> Optional[subprocess.Popen]:
        # 使用 CLI 方式运行 uvicorn，避免阻塞当前进程
        # 强制使用 .venv 的 Python 解释器启动后端
        cmd = [str(self.venv_python), "-m", "uvicorn", self.fastapi_module, "--host", host, "--port", str(port), "--log-level", log_level]
        if reload:
            cmd.append("--reload")
        Logger.info(f"启动 FastAPI: http://{host}:{port}")
        try:
            proc = subprocess.Popen(cmd, cwd=self.project_root)
            Logger.success("FastAPI 已启动（子进程）")
            return proc
        except Exception as e:
            Logger.error(f"启动 FastAPI 失败: {e}")
            return None

    # ===== 前端（Vite/Vue）检查与启动 =====
    def check_node_and_npm(self) -> bool:
        import shutil
        # 尝试通过 PATH 定位
        node = shutil.which("node")
        npm = shutil.which("npm")
        # Windows 上 npm 可能是 npm.cmd
        if platform.system() == "Windows" and not npm:
            npm = shutil.which("npm.cmd")

        # 额外检测常见安装目录（Windows）
        if platform.system() == "Windows":
            default_node = Path("C:/Program Files/nodejs/node.exe")
            default_npm = Path("C:/Program Files/nodejs/npm.cmd")
            if not node and default_node.exists():
                node = str(default_node)
            if not npm and default_npm.exists():
                npm = str(default_npm)

        if not node or not npm:
            Logger.error("未检测到 Node/npm，请先安装 Node.js 环境")
            Logger.error("下载地址：https://nodejs.org/")
            return False

        self.node_path = node
        self.npm_path = npm

        try:
            r1 = subprocess.run([node, "-v"], capture_output=True, text=True, check=True)
            r2 = subprocess.run([npm, "-v"], capture_output=True, text=True, check=True)
            Logger.success(f"Node 版本: {r1.stdout.strip()}")
            Logger.success(f"npm  版本: {r2.stdout.strip()}")
            return True
        except subprocess.CalledProcessError as e:
            Logger.error(f"Node/npm 检查失败: {e}")
            return False

    def check_web_project(self) -> bool:
        if not self.web_dir.exists():
            Logger.error("web 前端目录不存在！")
            return False
        pkg = self.web_dir / "package.json"
        if not pkg.exists():
            Logger.error("未找到 web/package.json，无法启动前端！")
            return False
        try:
            data = json.loads(pkg.read_text(encoding="utf-8"))
            scripts = (data.get("scripts") or {})
            if "dev" not in scripts:
                Logger.error("package.json 未定义 dev 脚本")
                return False
            Logger.success("已验证 web 项目结构与脚本")
            return True
        except Exception as e:
            Logger.error(f"读取 package.json 失败: {e}")
            return False

    def install_web_dependencies(self) -> bool:
        lockfile = self.web_dir / "package-lock.json"
        try:
            if lockfile.exists():
                Logger.info("安装前端依赖（npm ci）...")
                subprocess.run(["npm", "ci"], cwd=self.web_dir, check=True)
            else:
                Logger.info("安装前端依赖（npm install）...")
                subprocess.run(["npm", "install"], cwd=self.web_dir, check=True)
            Logger.success("前端依赖安装完成")
            return True
        except subprocess.CalledProcessError as e:
            Logger.error(f"前端依赖安装失败: {e}")
            return False

    def start_web(self, host: str, port: int) -> Optional[subprocess.Popen]:
        # 通过 npm run dev 传递 Vite 参数需要使用 -- 进行分隔
        npm_exec = self.npm_path or ("npm.cmd" if platform.system() == "Windows" else "npm")
        cmd = [npm_exec, "run", "dev", "--", "--host", host, "--port", str(port)]
        Logger.info(f"启动前端开发服务器: http://{host}:{port}")
        try:
            proc = subprocess.Popen(cmd, cwd=self.web_dir)
            Logger.success("前端开发服务器已启动（子进程）")
            return proc
        except Exception as e:
            Logger.error(f"启动前端失败: {e}")
            return None

    # ===== 统一运行流 =====
    def run(self, args) -> bool:
        Logger.header("ArXiv 系统 - FastAPI + Web 联合启动")
        Logger.info(f"项目根目录: {self.project_root}")

        # Python/NV 环境检查
        self.check_python_version_file()
        # 始终进行 NV 虚拟环境检查，并要求在 .venv 中运行
        if not self.check_nv_virtual_environment(auto_init=args.auto_init_venv):
            return False
        if not self.assert_running_in_venv():
            return False

        self.check_env_file()

        # 后端文件检查
        if not self.check_backend_entry():
            return False

        # 端口策略（后端）
        backend_port = args.port
        if not check_port_available(backend_port):
            Logger.warning(f"后端端口 {backend_port} 被占用，尝试寻找可用端口...")
            alt = find_available_port(backend_port + 1)
            if alt == 0:
                Logger.warning("未找到可用端口，uvicorn 将自行报错")
            else:
                backend_port = alt
                Logger.success(f"后端端口已调整为 {backend_port}")

        # 启动后端
        self.backend_proc = self.start_backend(args.host, backend_port, args.reload, args.backend_log)
        if self.backend_proc is None:
            return False

        # 是否启用前端
        if not args.no_web:
            if not self.check_node_and_npm():
                Logger.error("前端启动已跳过：Node/npm 不可用")
            elif not self.check_web_project():
                Logger.error("前端启动已跳过：web 项目结构不合法")
            else:
                # 端口策略（前端）
                web_port = args.web_port
                if not check_port_available(web_port):
                    Logger.warning(f"前端端口 {web_port} 被占用，尝试寻找可用端口...")
                    alt = find_available_port(web_port + 1)
                    if alt == 0:
                        Logger.warning("未找到可用端口，Vite 启动可能失败")
                    else:
                        web_port = alt
                        Logger.success(f"前端端口已调整为 {web_port}")

                # 自动安装依赖（可选）
                if args.auto_install_web:
                    self.install_web_dependencies()
                else:
                    node_modules = self.web_dir / "node_modules"
                    if not node_modules.exists():
                        Logger.warning("检测到未安装前端依赖，请先执行：")
                        Logger.warning(f"  cd {self.web_dir}")
                        Logger.warning("  npm install")

                # 启动前端
                self.web_proc = self.start_web(args.web_host, web_port)

        # 汇总信息
        Logger.header("服务已启动")
        Logger.info(f"后端地址: http://{args.host}:{backend_port}")
        if self.web_proc:
            Logger.info(f"前端地址: http://{args.web_host}:{args.web_port}")
            if args.web_port != web_port:
                Logger.info(f"实际前端端口: {web_port}")
        else:
            Logger.info("前端未启动或已跳过")

        Logger.info("按 Ctrl+C 终止所有服务")

        # 主循环，保持进程
        try:
            while True:
                time.sleep(1)
                # 如果后端进程退出，则同时退出
                if self.backend_proc and self.backend_proc.poll() is not None:
                    Logger.warning("后端进程已退出，准备清理并结束...")
                    break
        except KeyboardInterrupt:
            Logger.info("收到中断信号，正在停止服务...")
        finally:
            self._terminate_children()
        return True

    def _terminate_children(self):
        # 优雅终止子进程
        for proc, name in [(self.web_proc, "前端"), (self.backend_proc, "后端")]:
            try:
                if proc and proc.poll() is None:
                    if platform.system() == "Windows":
                        proc.terminate()
                    else:
                        proc.send_signal(signal.SIGINT)
                    proc.wait(timeout=10)
                    Logger.success(f"{name}进程已终止")
            except Exception:
                pass


def build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="启动 FastAPI 后端与 web 前端开发环境")
    parser.add_argument("--host", default="0.0.0.0", help="后端绑定地址")
    parser.add_argument("--port", type=int, default=8000, help="后端端口")
    parser.add_argument("--reload", action="store_true", help="启用后端热重载")
    parser.add_argument("--backend-log", default="info", help="后端日志级别")
    parser.add_argument("--no-web", action="store_true", help="仅启动后端，跳过前端")
    parser.add_argument("--web-host", default="localhost", help="前端绑定地址（Vite --host）")
    parser.add_argument("--web-port", type=int, default=5173, help="前端端口（Vite --port）")
    parser.add_argument("--auto-install-web", action="store_true", help="自动安装前端依赖")
    parser.add_argument("--check-venv", action="store_true", help="启用 NV 虚拟环境检查")
    parser.add_argument("--auto-init-venv", action="store_true", help="缺失时尝试自动创建 NV 虚拟环境")
    parser.add_argument("--no-bootstrap", action="store_true", help="禁用 Windows PowerShell 自动引导 .venv 激活")
    return parser


if __name__ == "__main__":
    # 保证项目根目录在 Python 路径中
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root)

    args = build_argparser().parse_args()
    launcher = FastAPIWebLauncher()
    # 在 Windows 环境下，若未处于 .venv，则先尝试以 PowerShell 自动激活并重新运行本脚本
    if platform.system() == "Windows" and not args.no_bootstrap:
        try:
            # 仅在未激活 .venv 时触发
            virtual_env = os.environ.get('VIRTUAL_ENV', '')
            need_bootstrap = True
            try:
                if virtual_env and Path(virtual_env).resolve() == launcher.venv_path.resolve():
                    need_bootstrap = False
            except Exception:
                need_bootstrap = True

            if need_bootstrap:
                if launcher.try_bootstrap_via_powershell(no_exit=True):
                    # 已在新终端中完成激活并启动，当前进程直接退出
                    sys.exit(0)
        except Exception:
            # 引导失败则继续后续逻辑，由原有 NV 检查与提示处理
            pass
    ok = launcher.run(args)
    sys.exit(0 if ok else 1)