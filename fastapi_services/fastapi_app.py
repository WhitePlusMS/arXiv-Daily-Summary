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
from .service_container import get_arxiv_service, get_category_matcher_service, get_env_config_service
from .main_dashboard_service import ArxivRecommenderService
from .environment_config_service import EnvConfigService
from streamlit_ui.services.category_browser_service import CategoryService

# 创建FastAPI应用
app = FastAPI(
    title="ArXiv推荐系统API",
    description="基于FastAPI的ArXiv论文推荐系统",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
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
    logger.info(
        f"API调用: 运行推荐系统 - 配置: {request.profile_name}, 调试模式: {request.debug_mode}, 目标日期: {getattr(request, 'target_date', None)}"
    )
    try:
        result = await service.run_recommendation(
            request.profile_name,
            request.debug_mode,
            getattr(request, "target_date", None),
        )
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
    except Exception as e:
        logger.error(f"优化研究描述失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/matcher/run")
async def run_category_matching(
    request: MatchRequest,
    service = Depends(get_category_matcher_service)
):
    """执行分类匹配，并保存结果"""
    logger.info(f"API调用: 执行分类匹配 - 用户: {request.username}, Top {request.top_n}")
    try:
        results, token_usage = service.execute_matching(request.user_input, request.username, request.top_n)
        # 保存结果
        service.save_matching_results(request.username, request.user_input, results)
        return {"success": True, "data": {"results": results, "token_usage": token_usage}}
    except Exception as e:
        logger.error(f"执行分类匹配失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/matcher/record")
async def update_matcher_record(
    request: UpdateRecordRequest,
    service = Depends(get_category_matcher_service)
):
    """更新单条匹配记录"""
    logger.info(f"API调用: 更新匹配记录 - 索引: {request.index}")
    try:
        success = service.update_record(request.index, request.username, request.category_id, request.user_input)
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