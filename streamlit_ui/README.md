# ArXiv 每日论文推荐系统 - Streamlit UI 模块

## 版本信息

- **版本**: 0.2
- **类型**: Streamlit Web UI 界面
- **状态**: 稳定版本

## 概述
这是 ArXiv 每日论文推荐系统的 Streamlit 用户界面模块，提供了一个直观的 Web 界面来配置和使用论文推荐功能。

## 架构说明

### 目录结构
```
streamlit_ui/
├── app.py                      # 主应用入口，使用 st.navigation 实现多页面
├── start.py                    # 启动脚本（PyEnv + NV 专用版本）
├── pages/                      # 页面模块
│   ├── main_dashboard.py       # 主仪表板页面
│   ├── category_matcher_ui.py  # 分类匹配器页面
│   ├── environment_config.py   # 环境配置页面
│   └── arxiv_category_browser.py # ArXiv 分类浏览器页面
├── services/                   # 业务逻辑服务层
│   ├── main_dashboard_service.py      # 主仪表板业务逻辑
│   ├── category_matcher_service.py    # 分类匹配业务逻辑
│   ├── environment_config_service.py  # 环境配置业务逻辑
│   └── category_browser_service.py    # 分类浏览业务逻辑
└── ui_components/              # UI 组件库
    ├── main_dashboard_components.py      # 主仪表板 UI 组件
    ├── category_matcher_components.py    # 分类匹配 UI 组件
    ├── environment_config_components.py  # 环境配置 UI 组件
    └── category_browser_components.py    # 分类浏览 UI 组件
```

### 架构设计原则

1. **分层架构**: 采用 Pages → Services → Components 三层架构
   - **Pages**: 页面组装层，负责页面路由和组件组装
   - **Services**: 业务逻辑层，处理数据和业务逻辑
   - **Components**: UI 组件层，提供可复用的 UI 组件

2. **模块化设计**: 每个功能模块独立，便于维护和扩展

3. **职责分离**: UI 渲染与业务逻辑分离，提高代码可维护性

## 功能模块

### 1. 主仪表板 (Main Dashboard)

- 用户配置管理
- 研究兴趣设置
- 论文推荐生成
- 历史记录查看

### 2. 分类匹配器 (Category Matcher)

- ArXiv 分类匹配
- 用户兴趣分析
- 匹配结果可视化

### 3. 环境配置 (Environment Config)

- API 密钥配置
- 系统参数设置
- 配置文件管理

### 4. 分类浏览器 (Category Browser)

- ArXiv 分类体系浏览
- 分类详情查看
- 分类搜索功能

## 启动方式

### 前提条件

1. 已安装 PyEnv 和 NV (Node Version Manager)
2. 项目根目录存在 `.python-version` 文件
3. 已使用 NV 创建并激活虚拟环境
4. 当前终端的 `VIRTUAL_ENV` 指向项目 `.venv` 目录

### 快速启动

#### 方式一：使用启动脚本（推荐）
```bash
# 进入 streamlit_ui 目录
cd streamlit_ui

# 激活虚拟环境
nv activate

# 启动应用
python start.py
```

### 手动环境创建步骤
```bash
# 进入项目目录
cd 项目根目录

# 创建虚拟环境
nv create

# 激活虚拟环境
nv activate

# 进入 streamlit_ui 目录
cd streamlit_ui

# 启动应用
python start.py
```

## 访问地址

- 默认地址: http://localhost:8501
- 自定义端口: http://localhost:{指定端口}

## 依赖关系

- 依赖项目根目录的 `core/` 模块
- 需要项目根目录的 `.env` 配置文件
- 使用项目根目录的 `requirements.txt` 安装依赖

## 注意事项

1. 确保在正确的虚拟环境中运行
2. 首次使用建议使用 `--init` 参数自动初始化
3. 开发时建议使用 `--dev` 参数启用自动重载
4. 如遇端口冲突，使用 `--port` 参数指定其他端口
