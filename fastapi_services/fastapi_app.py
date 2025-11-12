#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI应用程序 - ArXiv推荐系统
"""

from fastapi import FastAPI, Depends, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pathlib import Path
import os
import sys
import logging
import asyncio
from loguru import logger
from typing import List, Optional

from .models import (
    UserProfile, 
    RecommendationRequest, 
    RecommendationResult,
    ResearchInterestsRequest,
    InitializeRequest,
    OptimizeRequest,
    MatchRequest,
    UpdateRecordRequest,
    BatchDeleteRequest,
)
from .service_container import (
    get_arxiv_service,
    get_category_matcher_service,
    get_env_config_service,
    get_prompt_service,
)
from .main_dashboard_service import ArxivRecommenderService
from .environment_config_service import EnvConfigService
from .progress_manager import get_progress_manager
from streamlit_ui.services.category_browser_service import CategoryService

# 创建FastAPI应用
app = FastAPI(
    title="ArXiv推荐系统API",
    description="基于FastAPI的ArXiv论文推荐系统",
    version="1.0.0"
)

# 添加CORS中间件
# 允许本地和内网访问（支持 localhost、127.0.0.1、192.168.x.x、10.x.x.x 等内网IP）
app.add_middleware(
    CORSMiddleware,
    # 允许的来源：本地和内网IP
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    # 使用正则表达式允许所有本地和内网IP访问
    # 支持：localhost、127.0.0.1、192.168.x.x、10.x.x.x、172.16-31.x.x 等内网IP段
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+|172\.(1[6-9]|2[0-9]|3[0-1])\.\d+\.\d+):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================
# 模板错误分类辅助函数
# =====================
def _classify_prompt_error(exc: Exception, prompt_id: Optional[str] = None) -> dict:
    """将 Prompt 模板相关异常转换为可读的错误结构，用于 400 响应。"""
    payload = {
        "error_type": "template_error",
        "message": "模板渲染错误",
        "details": {"prompt_id": prompt_id} if prompt_id else {},
    }

    if isinstance(exc, KeyError):
        msg = str(exc)
        # 未找到模板: <prompt_id>
        if msg.startswith("未找到模板"):
            tpl_id = msg.split(":", 1)[-1].strip()
            payload["error_type"] = "template_not_found"
            payload["message"] = f"未找到模板: {tpl_id}"
            payload["details"]["prompt_id"] = tpl_id
        else:
            # 缺少变量（KeyError 提供缺失键名）
            missing_field = msg.strip("'\"")
            payload["error_type"] = "variable_missing"
            payload["message"] = f"模板变量缺失: {missing_field}"
            payload["details"]["missing_field"] = missing_field
            if prompt_id and "prompt_id" not in payload["details"]:
                payload["details"]["prompt_id"] = prompt_id
        return payload

    if isinstance(exc, ValueError):
        # 格式字符串错误（如花括号不匹配等）
        payload["error_type"] = "invalid_format_string"
        payload["message"] = "模板格式字符串错误"
        payload["details"]["reason"] = str(exc)
        return payload

    payload["details"]["reason"] = str(exc)
    return payload

# 为错误详情增加友好文案与修复建议
def _decorate_error_detail(detail: dict) -> dict:
    error_type = (detail or {}).get("error_type")
    d = (detail or {}).get("details") or {}

    friendly_message = "模板处理出现异常"
    fix_suggestions = [
        "查看错误详情并修复模板或变量",
        "如近期修改过模板，可在提示词管理中恢复默认模板",
    ]

    if error_type == "template_not_found":
        pid = d.get("prompt_id")
        friendly_message = f"提示词模板未找到：{pid}" if pid else "提示词模板未找到"
        fix_suggestions = [
            "在 config/prompts.json 中添加或修复对应模板 ID",
            "若无自定义模板，可在提示词管理页面重置为默认",
            "确认后端 PromptManager.get_template 能返回该模板",
        ]
    elif error_type == "variable_missing":
        missing = d.get("missing_field") or "未知字段"
        pid = d.get("prompt_id")
        friendly_message = f"模板变量缺失：{missing}" + (f"（模板：{pid}）" if pid else "")
        fix_suggestions = [
            "检查模板占位符与后端提供的字段名一致",
            "如通过 UI 修改模板，请校验占位符名称是否正确",
        ]
    elif error_type == "invalid_format_string":
        reason = d.get("reason") or ""
        if "Replacement index out of range" in str(reason):
            friendly_message = "检测到位置占位符错误（如 {0} 或 {}），请改为命名占位符"
            fix_suggestions = [
                "避免使用位置占位符，统一使用命名占位符（例如 {user_description}）",
                "如果存在 {0}/{1} 等，请替换为对应变量名",
                "参考变量列表并对齐默认模板",
            ]
        elif "Single '}' encountered" in str(reason) or "unmatched '}'" in str(reason) or "expected '}'" in str(reason):
            friendly_message = "花括号不配对或有多余/缺失的 { 或 }"
            fix_suggestions = [
                "检查所有 { 与 } 是否成对出现",
                "避免同时混用 {{ }}（转义）与 {}（占位）",
                "参考默认模板调整花括号位置",
            ]
        else:
            friendly_message = "模板格式错误，可能存在花括号或占位符问题"
            fix_suggestions = [
                "检查模板中花括号 {} 是否配对、未被误用",
                "避免不完整占位符（例如 {var 或混用 {{ }} 与 {}）",
                "对比默认模板，修复格式差异后再试",
            ]

    detail["friendly_message"] = friendly_message
    detail["fix_suggestions"] = fix_suggestions
    return detail

# 日志配置标志，确保只配置一次
_logging_configured = False

def cleanup_old_logs_by_size(files: list, max_size_mb: int = 500):
    """清理旧日志文件，确保总大小不超过指定值（MB）
    
    Args:
        files: 日志文件路径列表（loguru传入的）
        max_size_mb: 最大总大小（MB），默认500MB
    """
    if not files:
        return
    
    max_size_bytes = max_size_mb * 1024 * 1024  # 转换为字节
    
    # 将文件路径转换为Path对象，并按修改时间排序（最旧的在前）
    file_paths = [Path(f) for f in files if Path(f).exists()]
    file_paths.sort(key=lambda f: f.stat().st_mtime)
    
    # 计算当前总大小
    total_size = sum(f.stat().st_size for f in file_paths)
    
    # 如果总大小超过限制，删除最旧的文件
    while total_size > max_size_bytes and len(file_paths) > 1:
        oldest_file = file_paths.pop(0)
        file_size = oldest_file.stat().st_size
        try:
            oldest_file.unlink()
            total_size -= file_size
        except Exception:
            # 如果删除失败，跳过这个文件
            pass

def cleanup_old_logs(logs_dir: Path, max_size_mb: int = 500):
    """清理旧日志文件，确保日志目录总大小不超过指定值（MB）
    用于启动时的初始清理
    """
    # 获取所有日志文件（包括轮转的文件）
    log_files = list(logs_dir.glob("fastapi.log*"))
    if log_files:
        cleanup_old_logs_by_size([str(f) for f in log_files], max_size_mb)

def setup_logging():
    """配置日志记录到文件"""
    global _logging_configured
    if _logging_configured:
        return
    
    # 创建logs目录
    project_root = Path(__file__).parent.parent
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # 日志文件路径
    log_file = logs_dir / "fastapi.log"
    
    # 移除默认的loguru处理器
    logger.remove()
    
    # 添加控制台输出（保持原有格式）
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="DEBUG"
    )
    
    # 自定义retention函数，确保总大小不超过500MB
    def retention_function(files):
        """在日志轮转时调用，清理旧日志确保总大小不超过500MB
        files: loguru传入的日志文件路径列表
        """
        cleanup_old_logs_by_size(files, max_size_mb=500)
    
    # 添加文件输出（纯文本格式，便于查看）
    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="10 MB",  # 文件大小达到10MB时轮转
        retention=retention_function,  # 自定义清理函数，确保总大小不超过500MB
        encoding="utf-8",
        enqueue=True  # 异步写入，提高性能
    )
    
    # 启动时也执行一次清理
    cleanup_old_logs(logs_dir, max_size_mb=500)
    
    # 拦截uvicorn和uvicorn.access的日志，使其也写入文件
    class InterceptHandler(logging.Handler):
        def emit(self, record):
            # 获取对应的loguru级别
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                # 如果级别名称不存在，根据级别号映射
                level_map = {
                    logging.DEBUG: "DEBUG",
                    logging.INFO: "INFO",
                    logging.WARNING: "WARNING",
                    logging.ERROR: "ERROR",
                    logging.CRITICAL: "CRITICAL",
                }
                level = level_map.get(record.levelno, "INFO")

            # 使用loguru记录日志
            logger.opt(depth=6, exception=record.exc_info).log(level, record.getMessage())

    # 拦截uvicorn的日志
    logging.getLogger("uvicorn").handlers = [InterceptHandler()]
    logging.getLogger("uvicorn.access").handlers = [InterceptHandler()]
    logging.getLogger("uvicorn.error").handlers = [InterceptHandler()]
    
    _logging_configured = True

@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    # 配置日志
    setup_logging()
    logger.info("FastAPI应用启动")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("FastAPI应用关闭")

@app.get("/")
async def root():
    """根路径"""
    return {"message": "ArXiv推荐系统API", "version": "1.0.0"}

@app.get("/api/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "service": "arxiv-recommender-backend"}

@app.post("/api/initialize")
async def initialize_service(
    service: ArxivRecommenderService = Depends(get_arxiv_service)
):
    """初始化服务"""
    logger.info("API调用: 初始化服务")
    try:
        result = await service.initialize_service()
        return result
    except Exception as e:
        logger.error(f"初始化服务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/config")
async def get_config(
    service: ArxivRecommenderService = Depends(get_arxiv_service)
):
    """获取配置"""
    logger.info("API调用: 获取配置")
    try:
        result = await service.get_config()
        return result
    except Exception as e:
        logger.error(f"获取配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/user-profiles")
async def get_user_profiles(
    service: ArxivRecommenderService = Depends(get_arxiv_service)
):
    """获取用户配置列表"""
    logger.info("API调用: 获取用户配置列表")
    try:
        result = await service.get_user_profiles()
        return result
    except Exception as e:
        logger.error(f"获取用户配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/research-interests")
async def get_research_interests(
    service: ArxivRecommenderService = Depends(get_arxiv_service)
):
    """获取研究兴趣"""
    logger.info("API调用: 获取研究兴趣")
    try:
        result = await service.get_research_interests()
        return result
    except Exception as e:
        logger.error(f"获取研究兴趣失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/research-interests")
async def update_research_interests(
    request: ResearchInterestsRequest,
    service: ArxivRecommenderService = Depends(get_arxiv_service)
):
    """更新研究兴趣"""
    logger.info(f"API调用: 更新研究兴趣 - {len(request.interests)}个兴趣, {len(request.negative_interests) if request.negative_interests else 0}个负面偏好")
    try:
        result = await service.update_research_interests(
            request.interests,
            request.negative_interests if request.negative_interests else None
        )
        return result
    except Exception as e:
        logger.error(f"更新研究兴趣失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/initialize-components")
async def initialize_components(
    request: InitializeRequest,
    service: ArxivRecommenderService = Depends(get_arxiv_service)
):
    """初始化系统组件"""
    logger.info(f"API调用: 初始化系统组件 - 配置: {request.profile_name}")
    try:
        result = await service.initialize_components(request.profile_name)
        return result
    except Exception as e:
        logger.error(f"初始化系统组件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def _run_recommendation_task(
    task_id: str,
    profile_name: str,
    debug_mode: bool,
    target_date: Optional[str],
    service: ArxivRecommenderService
):
    """在后台线程中运行推荐任务"""
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    
    progress_manager = get_progress_manager()
    
    try:
        # 创建新的事件循环（因为在新线程中）
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # 运行推荐
        result = loop.run_until_complete(
            service.run_recommendation_with_progress(
                task_id,
                profile_name,
                debug_mode,
                target_date
            )
        )
        
        loop.close()
        
    except (KeyError, ValueError) as e:
        # 模板错误
        error_msg = f"模板错误: {str(e)}"
        logger.error(f"运行推荐系统失败（模板错误）: {error_msg}")
        progress_manager.fail_task(task_id, error_msg)
    except Exception as e:
        error_msg = f"推荐系统运行失败: {str(e)}"
        logger.error(error_msg)
        progress_manager.fail_task(task_id, error_msg)

@app.post("/api/run-recommendation")
async def run_recommendation(
    request: RecommendationRequest,
    background_tasks: BackgroundTasks,
    service: ArxivRecommenderService = Depends(get_arxiv_service)
):
    """运行推荐系统（异步模式，立即返回task_id）"""
    logger.info(
        f"API调用: 运行推荐系统 - 配置: {request.profile_name}, 调试模式: {request.debug_mode}, 目标日期: {getattr(request, 'target_date', None)}"
    )
    try:
        # 创建任务
        progress_manager = get_progress_manager()
        task_id = progress_manager.create_task("初始化推荐系统...")
        
        # 在后台执行推荐任务
        from threading import Thread
        thread = Thread(
            target=_run_recommendation_task,
            args=(
                task_id,
                request.profile_name,
                request.debug_mode,
                getattr(request, "target_date", None),
                service
            )
        )
        thread.daemon = True
        thread.start()
        
        # 立即返回task_id
        return {
            "success": True,
            "data": {
                "task_id": task_id,
                "message": "推荐任务已启动，请使用task_id查询进度"
            }
        }
        
    except Exception as e:
        logger.error(f"启动推荐系统失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/recent-reports")
async def get_recent_reports(
    username: Optional[str] = Query(None, description="可选的用户名筛选"),
    service: ArxivRecommenderService = Depends(get_arxiv_service)
):
    """获取最近报告"""
    logger.info(f"API调用: 获取最近报告 - 用户名筛选: {username}")
    try:
        result = await service.get_recent_reports(username=username)
        return result
    except Exception as e:
        logger.error(f"获取最近报告失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 新增：分类浏览器相关API
@app.get("/api/categories")
async def get_categories():
    """获取合并后的ArXiv分类数据"""
    logger.info("API调用: 获取分类数据")
    try:
        category_service = CategoryService()
        data = category_service.load_categories_data()
        return {"success": True, "data": data}
    except Exception as e:
        logger.error(f"获取分类数据失败: {str(e)}")
    raise HTTPException(status_code=500, detail=str(e))

# =====================
# 环境配置相关 API
# =====================

@app.get("/api/env-config")
async def get_env_config(service: EnvConfigService = Depends(get_env_config_service)):
    """获取 .env 配置"""
    logger.info("API调用: 获取环境配置")
    try:
        result = await service.get_config()
        return result
    except Exception as e:
        logger.error(f"获取环境配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/env-config/save")
async def save_env_config(request: dict, service: EnvConfigService = Depends(get_env_config_service)):
    """保存 .env 配置。请求体需包含 { config: {...} }"""
    logger.info("API调用: 保存环境配置")
    try:
        cfg = request.get("config", {}) if isinstance(request, dict) else {}
        result = await service.save_config(cfg)
        return result
    except Exception as e:
        logger.error(f"保存环境配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/env-config/reload")
async def reload_env_config(service: EnvConfigService = Depends(get_env_config_service)):
    """重新加载 .env 配置"""
    logger.info("API调用: 重新加载环境配置")
    try:
        result = await service.reload_config()
        return result
    except Exception as e:
        logger.error(f"重新加载环境配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/env-config/restore-default")
async def restore_default_env_config(service: EnvConfigService = Depends(get_env_config_service)):
    """从 .env.example 恢复默认配置"""
    logger.info("API调用: 恢复默认环境配置")
    try:
        result = await service.restore_default()
        return result
    except Exception as e:
        logger.error(f"恢复默认环境配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# =====================
# 提示词管理相关 API
# =====================

@app.get("/api/prompts")
async def list_prompts(service = Depends(get_prompt_service)):
    """获取所有提示词列表"""
    logger.info("API调用: 获取提示词列表")
    try:
        res = await service.get_all_prompts()
        return res
    except Exception as e:
        logger.error(f"获取提示词列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/prompts/{prompt_id}")
async def get_prompt(prompt_id: str, service = Depends(get_prompt_service)):
    """获取单个提示词详情"""
    logger.info(f"API调用: 获取提示词 - {prompt_id}")
    try:
        res = await service.get_prompt(prompt_id)
        if not res.success:
            raise HTTPException(status_code=res.status_code or 404, detail=res.message or "未找到提示词")
        return res
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取提示词失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/prompts/{prompt_id}")
async def update_prompt(prompt_id: str, request: dict, service = Depends(get_prompt_service)):
    """更新提示词（允许更新 name/template）"""
    logger.info(f"API调用: 更新提示词 - {prompt_id}")
    try:
        updates = request if isinstance(request, dict) else {}
        res = await service.update_prompt(prompt_id, updates)
        if not res.success:
            # 将服务层消息统一规范为结构化模板错误详情
            msg = res.message or res.error or "更新失败"
            # 根据消息内容推断异常类型（缺失变量 vs 格式错误）
            if msg and (msg.startswith("模板格式错误") or msg.startswith("模板占位符不匹配")):
                detail = _decorate_error_detail(_classify_prompt_error(ValueError(msg), prompt_id))
            elif msg and (msg.startswith("'") and msg.endswith("'")):
                # KeyError("'field'") 的字符串形式，视为变量缺失
                detail = _decorate_error_detail(_classify_prompt_error(KeyError(msg), prompt_id))
            elif msg and msg.startswith("未找到指定的提示词"):
                detail = _decorate_error_detail(_classify_prompt_error(KeyError(msg), prompt_id))
            else:
                detail = _decorate_error_detail(_classify_prompt_error(ValueError(msg), prompt_id))
            raise HTTPException(status_code=res.status_code or 400, detail=detail)
        return res
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新提示词失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/prompts/{prompt_id}/reset")
async def reset_prompt(prompt_id: str, service = Depends(get_prompt_service)):
    """重置单个提示词为默认版本"""
    logger.info(f"API调用: 重置提示词 - {prompt_id}")
    try:
        res = await service.reset_prompt(prompt_id)
        if not res.success:
            raise HTTPException(status_code=res.status_code or 400, detail=res.message or "重置失败")
        return res
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重置提示词失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/prompts/reset")
async def reset_all_prompts(service = Depends(get_prompt_service)):
    """重置所有提示词为默认版本"""
    logger.info("API调用: 重置所有提示词")
    try:
        res = await service.reset_all_prompts()
        return res
    except Exception as e:
        logger.error(f"重置所有提示词失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 辅助函数：解析报告文件路径
def _resolve_report_path(name: str, fmt: str) -> Path:
    base_dirs = [
        Path(os.path.join(Path(__file__).parent.parent, 'output', 'reports')),
        Path(os.path.join(Path(__file__).parent.parent, 'arxiv_history')),
    ]
    filename = f"{name}.{fmt}"
    for base in base_dirs:
        candidate = base / filename
        if candidate.exists():
            return candidate
    # 如果找不到，返回默认路径（用于错误提示）
    return base_dirs[0] / filename

@app.get("/api/reports/preview")
async def preview_report(
    name: str = Query(..., description="报告文件名（不含扩展名）"),
    format: str = Query("md", description="报告格式：md 或 html")
):
    """预览报告内容（返回文本或HTML内容）"""
    logger.info(f"API调用: 预览报告 - {name}.{format}")
    try:
        fmt = format.lower()
        if fmt not in ("md", "html"):
            raise HTTPException(status_code=400, detail="不支持的格式")
        filepath = _resolve_report_path(name, fmt)
        if not filepath.exists():
            raise HTTPException(status_code=404, detail="报告文件不存在")
        content = filepath.read_text(encoding="utf-8")
        return {"success": True, "data": {"content": content, "name": name, "format": fmt}}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"预览报告失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reports/download")
async def download_report(
    name: str = Query(..., description="报告文件名（不含扩展名）"),
    format: str = Query("md", description="报告格式：md 或 html")
):
    """下载报告文件（返回文件响应）"""
    logger.info(f"API调用: 下载报告 - {name}.{format}")
    try:
        fmt = format.lower()
        if fmt not in ("md", "html"):
            raise HTTPException(status_code=400, detail="不支持的格式")
        filepath = _resolve_report_path(name, fmt)
        if not filepath.exists():
            raise HTTPException(status_code=404, detail="报告文件不存在")
        return FileResponse(str(filepath), filename=f"{name}.{fmt}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载报告失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/reports/file")
async def delete_report(
    name: str = Query(..., description="报告文件名（不含扩展名）"),
    format: str = Query("md", description="报告格式：md 或 html")
):
    """删除报告文件"""
    logger.info(f"API调用: 删除报告 - {name}.{format}")
    try:
        fmt = format.lower()
        if fmt not in ("md", "html"):
            raise HTTPException(status_code=400, detail="不支持的格式")
        filepath = _resolve_report_path(name, fmt)
        if not filepath.exists():
            raise HTTPException(status_code=404, detail="报告文件不存在")
        os.remove(str(filepath))
        return {"success": True, "message": "删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除报告失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# =====================
# 分类匹配器相关 API
# =====================

@app.get("/api/matcher/provider")
async def get_matcher_provider_config(
    service = Depends(get_category_matcher_service)
):
    """获取分类匹配器提供商配置信息"""
    logger.info("API调用: 获取匹配器提供商配置")
    try:
        return {"success": True, "data": service.get_provider_config()}
    except Exception as e:
        logger.error(f"获取提供商配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/matcher/data")
async def get_matcher_data(
    service = Depends(get_category_matcher_service)
):
    """获取用户匹配数据及统计"""
    logger.info("API调用: 获取分类匹配数据")
    try:
        data = service.load_existing_data()
        stats = service.get_statistics(data)
        return {"success": True, "data": data, "stats": stats}
    except Exception as e:
        logger.error(f"获取匹配数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/matcher/optimize")
async def optimize_description(
    request: OptimizeRequest,
    service = Depends(get_category_matcher_service)
):
    """使用AI优化研究描述"""
    logger.info("API调用: 优化研究描述")
    try:
        optimized = service.optimize_research_description(request.user_input)
        return {"success": True, "data": {"optimized": optimized}}
    except (KeyError, ValueError) as e:
        # 识别并返回模板相关错误（400）
        logger.error(f"优化研究描述失败（模板错误）: {str(e)}")
        detail = _classify_prompt_error(e, prompt_id="research_description_optimization")
        raise HTTPException(status_code=400, detail=_decorate_error_detail(detail))
    except Exception as e:
        logger.error(f"优化研究描述失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def _run_category_matching_task(
    task_id: str,
    user_input: str,
    username: str,
    top_n: int,
    negative_query: str,
    service
):
    """在后台线程中运行分类匹配任务"""
    from fastapi_services.progress_manager import get_progress_manager
    
    progress_manager = get_progress_manager()
    
    try:
        # 执行匹配
        results, token_usage = service.execute_matching(user_input, username, top_n, negative_query, task_id=task_id)
        
        # 保存结果
        progress_manager.update_progress(
            task_id,
            step="保存匹配结果...",
            percentage=98,
            log_message="正在保存匹配结果到数据库"
        )
        service.save_matching_results(username, user_input, results, negative_query)
        
        # 完成
        progress_manager.complete_task(task_id, f"分类匹配完成，共匹配到 {len(results)} 个分类")
        
    except (KeyError, ValueError) as e:
        error_msg = f"模板错误: {str(e)}"
        logger.error(f"执行分类匹配失败（模板错误）: {error_msg}")
        progress_manager.fail_task(task_id, error_msg)
    except Exception as e:
        error_msg = f"分类匹配失败: {str(e)}"
        logger.error(error_msg)
        progress_manager.fail_task(task_id, error_msg)

@app.post("/api/matcher/run")
async def run_category_matching(
    request: MatchRequest,
    service = Depends(get_category_matcher_service)
):
    """执行分类匹配（异步模式，立即返回task_id）"""
    logger.info(f"API调用: 执行分类匹配 - 用户: {request.username}, Top {request.top_n}")
    try:
        # 创建任务
        progress_manager = get_progress_manager()
        task_id = progress_manager.create_task("初始化分类匹配器...")
        
        # 在后台执行匹配任务
        from threading import Thread
        thread = Thread(
            target=_run_category_matching_task,
            args=(
                task_id,
                request.user_input,
                request.username,
                request.top_n,
                request.negative_query or "",
                service
            )
        )
        thread.daemon = True
        thread.start()
        
        # 立即返回task_id
        return {
            "success": True,
            "data": {
                "task_id": task_id,
                "message": "分类匹配任务已启动，请使用task_id查询进度"
            }
        }
        
    except Exception as e:
        logger.error(f"启动分类匹配失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/matcher/record")
async def update_matcher_record(
    request: UpdateRecordRequest,
    service = Depends(get_category_matcher_service)
):
    """更新单条匹配记录"""
    logger.info(f"API调用: 更新匹配记录 - 索引: {request.index}")
    try:
        success = service.update_record(request.index, request.username, request.category_id, request.user_input, request.negative_query or "")
        if not success:
            raise HTTPException(status_code=400, detail="更新失败或索引无效")
        return {"success": True, "message": "更新成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新匹配记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/matcher/record")
async def delete_matcher_record(
    index: int = Query(..., description="记录索引"),
    service = Depends(get_category_matcher_service)
):
    """删除单条匹配记录"""
    logger.info(f"API调用: 删除匹配记录 - 索引: {index}")
    try:
        success = service.delete_single_record(index)
        if not success:
            raise HTTPException(status_code=400, detail="删除失败或索引无效")
        return {"success": True, "message": "删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除匹配记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/matcher/records")
async def batch_delete_matcher_records(
    request: BatchDeleteRequest,
    service = Depends(get_category_matcher_service)
):
    """批量删除匹配记录"""
    logger.info(f"API调用: 批量删除匹配记录 - {len(request.indices)} 条")
    try:
        deleted_count = service.batch_delete_records(request.indices)
        return {"success": True, "data": {"deleted": deleted_count}}
    except Exception as e:
        logger.error(f"批量删除记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/matcher/scores")
async def list_score_files(
    service = Depends(get_category_matcher_service)
):
    """列出详细评分文件"""
    logger.info("API调用: 列出评分文件")
    try:
        files = service.list_detailed_score_files()
        return {"success": True, "data": files}
    except Exception as e:
        logger.error(f"列出评分文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/matcher/scores/content")
async def read_score_file_content(
    name: str = Query(..., description="评分文件名"),
    service = Depends(get_category_matcher_service)
):
    """读取评分文件内容"""
    logger.info(f"API调用: 读取评分文件 - {name}")
    try:
        content = service.read_score_file_content(name)
        return {"success": True, "data": {"name": name, "content": content}}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="评分文件不存在")
    except Exception as e:
        logger.error(f"读取评分文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/matcher/scores")
async def delete_score_file(
    name: str = Query(..., description="评分文件名"),
    service = Depends(get_category_matcher_service)
):
    """删除详细评分文件"""
    logger.info(f"API调用: 删除评分文件 - {name}")
    try:
        success = service.delete_score_file(name)
        if not success:
            raise HTTPException(status_code=404, detail="评分文件不存在或删除失败")
        return {"success": True, "message": "删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除评分文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/matcher/scores/file")
async def delete_score_file(
    name: str = Query(..., description="评分文件名"),
    service = Depends(get_category_matcher_service)
):
    """删除评分文件"""
    logger.info(f"API调用: 删除评分文件 - {name}")
    try:
        success = service.delete_score_file(name)
        if not success:
            raise HTTPException(status_code=400, detail="删除失败或文件不存在")
        return {"success": True, "message": "删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除评分文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# =====================
# 进度管理相关 API
# =====================

@app.get("/api/tasks/{task_id}/progress")
async def get_task_progress(task_id: str):
    """获取任务进度（轮询接口）
    
    Args:
        task_id: 任务ID
        
    Returns:
        任务进度数据
    """
    try:
        progress_manager = get_progress_manager()
        progress = progress_manager.get_progress(task_id)
        
        if progress is None:
            raise HTTPException(status_code=404, detail="任务不存在或已过期")
        
        return {"success": True, "data": progress}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务进度失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: str):
    """删除任务
    
    Args:
        task_id: 任务ID
        
    Returns:
        删除结果
    """
    logger.debug(f"API调用: 删除任务 - {task_id}")
    try:
        progress_manager = get_progress_manager()
        success = progress_manager.delete_task(task_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        return {"success": True, "message": "任务已删除"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/tasks/cleanup")
async def cleanup_expired_tasks():
    """清理过期任务（管理接口）
    
    Returns:
        清理的任务数量
    """
    logger.info("API调用: 清理过期任务")
    try:
        progress_manager = get_progress_manager()
        count = progress_manager.cleanup_expired_tasks()
        return {"success": True, "data": {"cleaned": count}}
    except Exception as e:
        logger.error(f"清理过期任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理器"""
    logger.error(f"未处理的异常: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": f"服务器内部错误: {str(exc)}"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)