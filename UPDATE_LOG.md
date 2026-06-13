# 更新说明

## 2026-06-12 技术债快速修复

### 修改文件

- `fastapi_services/fastapi_app.py`
  - 引入 `SaveEnvRequest`，将 `/api/env-config/save` 请求体从裸 `dict` 改为统一的 Pydantic DTO。
  - 修复 `/api/categories` 异常处理缩进，将 `raise HTTPException` 放回 `except` 块内，避免异常变量离开作用域后不可用。
  - 移除 CORS 中与 `allow_origin_regex` 重复的本地 `allow_origins` 显式列表，保留原有本地和内网访问正则策略。
  - 将两个评分文件删除接口的 Python handler 分别重命名为 `delete_score_file_legacy` 和 `delete_score_file_by_name`，保留原有 API 路径不变。
  - 全局异常处理器改为服务端记录完整异常，客户端返回通用错误消息，避免泄露内部异常细节。
- `fastapi_services/service_container.py`
  - 移除冗余 `@lru_cache` 装饰器和对应 import，保留 `_services` 字典作为单一服务实例缓存来源。
- `core/recommendation_engine.py`
  - 修正论文评估间隔注释，将“等待0.5秒”改为真实的“等待0.1秒”，不改变限流行为。
- `UPDATE_LOG.md`
  - 新增本次变更记录。

### 修改原因

- 修复已确认的异常处理 bug 和接口契约不一致问题。
- 减少重复单例机制和重复 handler 名称带来的维护成本。
- 避免全局异常响应把内部路径、变量值或异常文本暴露给前端。
- 保持本轮修复最小化，不删除现有接口、不做大规模架构重构。

### 修改影响

- `/api/env-config/save` 仍接受 `{ "config": {...} }` 请求体，但由 Pydantic 模型校验。
- `/api/matcher/scores` 与 `/api/matcher/scores/file` 两个删除接口路径均保留，前端现有调用不受影响。
- 未改动推荐流程的实际等待时间，仅修正文档性注释。
- 未修改 `requirements.txt`、CLI 包装架构、前后端启动方式。

### 验证记录

- 已通过：后端静态导入并检查 FastAPI 路由无重复 `(method, path)`；评分文件删除接口仍注册为 `/api/matcher/scores` 与 `/api/matcher/scores/file`。
- 已通过：Python 编译检查 `fastapi_services` 与 `core`。
- 已通过：前端类型检查 `npm run type-check`。
- 已确认：`/api/env-config/save` 仍使用 `{ "config": {...} }` 请求体结构，由 `SaveEnvRequest` 进行校验。

## 2026-06-12 审计报告全量处理与架构债拆分

### 修改文件

- `core/arxiv_cli.py`
  - 将原推荐主类改为 `RecommendationWorkflow`，保留 `ArxivRecommenderCLI` 作为 CLI 兼容薄入口。
  - 将调试模式假论文、假 Markdown、假 HTML 生成委托给独立调试数据模块。
  - 将报告保存和邮件发送委托给独立报告工作流，减少 CLI/入口类职责。
  - 清理未使用 import，保留现有命令行 `main()` 行为不变。
- `core/debug_recommendation_data.py`
  - 新增调试模式数据模块，集中管理假论文、调试报告生成和调试报告保存。
- `core/report_workflow.py`
  - 新增报告编排服务，统一处理 Markdown 保存、HTML 保存和邮件发送。
- `core/recommendation_workflow.py`
  - 新增公共推荐工作流导出入口，让 FastAPI 服务依赖 workflow，而不是 CLI 类。
- `fastapi_services/main_dashboard_service.py`
  - 将 `ArxivRecommenderService` 从实例化 `ArxivRecommenderCLI` 改为实例化 `RecommendationWorkflow`。
  - 清理 CLI 相关注释、未使用 import 和旧字段命名。
- `core/user_config_loader.py`
  - 新增用户配置读取工具，统一处理 `user_categories.json` 的用户选择、分类解析和正负研究兴趣解析。
- `core/logging_config.py`
  - 新增共享 loguru 日志配置，FastAPI 与 CLI 入口共用。
- `core/usage_tracker.py`
  - 新增 token 用量统计器，`LLMProvider` 委托它维护累计 token 和成本估算基础数据。
- `core/llm_provider.py`
  - 接入 `UsageTracker`，减少 token 统计职责散落在 LLM 调用代码中的程度。
- `core/arxiv_fetcher.py`
  - 移除生产模块中的 `save_to_json`、`main2` 和 `__main__` 调试入口。
- `AGENTS.md`、`CLAUDE.md`
  - 清理已不存在的 Streamlit UI 启动说明和端口说明。
- `web/src/services/api.ts`
  - 直接使用 `import.meta.env.VITE_API_BASE_URL`。
  - 使用 Axios 类型守卫规范化模板错误。
  - 为分类匹配运行接口补齐异步 `task_id` 与同步结果的联合类型。
- `web/src/router/index.ts`
  - 直接使用 `import.meta.env.BASE_URL`，移除 `unknown as` 环境变量强制转换。
- `web/src/services/progress.ts`
  - 简化 API Base URL 回退表达式。
- `web/src/types/index.ts`
  - 将 `template_error` 纳入统一 `ApiResponse` 类型。
  - 新增分类匹配结果和 token 用量类型。
  - 将 `ProgressData.result` 从 `any` 收紧为 `Record<string, unknown>`。
- `web/src/composables/useRecommendation.ts`
  - 用运行时类型守卫替代 `unknown as` 响应强转。
- `web/src/composables/useCategoryMatcher.ts`
  - 用类型守卫和转换函数替代匹配结果、token 用量、模板错误的硬类型转换。
- `web/src/composables/useTime.ts`
  - 使用 `ReturnType<typeof setInterval>` 替代计时器 `unknown as number` 强转。
- `requirements.txt`
  - 移除确认仅工具脚本直接使用的 `numpy`。
- `requirements-tools.txt`
  - 新增工具脚本依赖文件，记录 `numpy==2.3.2`。
- `TECH_DEBT_AUDIT.md`
  - 新增处理状态，标注已修项、部分处理项、误判项、跳过测试项和谨慎保留依赖。

### 修改原因

- 逐条复核审计报告，把真实且可安全处理的问题尽量修掉。
- 将 FastAPI 服务从 CLI 抽象中解耦，降低 CLI-as-API 反模式影响。
- 将调试数据、报告保存、用户配置读取、日志配置、token 统计等职责拆到独立模块。
- 清理前端脆弱类型强转，让错误响应和异步任务响应进入正式类型契约。
- 不新增测试、不运行服务，保持现有 API 路径兼容。

### 修改影响

- 现有 CLI 入口仍可通过 `ArxivRecommenderCLI` 使用；FastAPI 主推荐服务改用 `RecommendationWorkflow`。
- `/api/matcher/scores`、`/api/matcher/scores/file` 等现有路径未删除。
- 调试模式输出路径和返回字段保持兼容，但假数据不再内联在主流程类中。
- `numpy` 从生产依赖拆到工具依赖；运行 `tools/score_*` 脚本前需要安装 `requirements-tools.txt`。
- `httpx`、`openai` 及其他疑似传递依赖保留，未做高风险删除。

### 验证记录

- 已通过：`.venv\Scripts\python.exe -m compileall fastapi_services core`。
- 已通过：FastAPI 静态导入并检查无重复 `(method, path)` 路由，结果 `route_count=41`、`duplicates=[]`。
- 已通过：`npm run type-check`。
- 未执行：不运行 pytest/E2E，因为本轮明确约束为不新增测试、不运行测试体系。
- 未执行：不运行 `npm run dev`、`npm run start:dev`、`python start_fastapi.py`，遵循项目约束。
