#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI应用程序 - ArXiv推荐系统
"""

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pathlib import Path
import os
from loguru import logger
from typing import List, Optional

from fastapi_services.models import (
    UserProfile, 
    RecommendationRequest, 
    RecommendationResult,
    ResearchInterestsRequest,
    InitializeRequest
)
from fastapi_services.service_container import get_arxiv_service
from fastapi_services.arxiv_service import ArxivRecommenderService

# 创建FastAPI应用
app = FastAPI(
    title="ArXiv推荐系统API",
    description="基于FastAPI的ArXiv论文推荐系统",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("FastAPI应用启动")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("FastAPI应用关闭")

@app.get("/")
async def root():
    """根路径"""
    return {"message": "ArXiv推荐系统API", "version": "1.0.0"}

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
    logger.info(f"API调用: 更新研究兴趣 - {len(request.interests)}个兴趣")
    try:
        result = await service.update_research_interests(request.interests)
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

@app.post("/api/run-recommendation")
async def run_recommendation(
    request: RecommendationRequest,
    service: ArxivRecommenderService = Depends(get_arxiv_service)
):
    """运行推荐系统"""
    logger.info(f"API调用: 运行推荐系统 - 配置: {request.profile_name}, 调试模式: {request.debug_mode}")
    try:
        result = await service.run_recommendation(request.profile_name, request.debug_mode)
        return result
    except Exception as e:
        logger.error(f"运行推荐系统失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/recent-reports")
async def get_recent_reports(
    service: ArxivRecommenderService = Depends(get_arxiv_service)
):
    """获取最近报告"""
    logger.info("API调用: 获取最近报告")
    try:
        result = await service.get_recent_reports()
        return result
    except Exception as e:
        logger.error(f"获取最近报告失败: {str(e)}")
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