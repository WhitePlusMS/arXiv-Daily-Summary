#!/bin/bash

# ArXiv 每日论文推荐系统 - 后端 Docker 入口脚本

# 标记为Docker环境
export IS_DOCKER_ENV=true

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 初始化 .env 文件
init_env_file() {
    log_info "检查 .env 文件..."
    
    # .env 文件路径（保存在持久化数据目录中，确保重启后保留）
    ENV_FILE_PATH="/app/.env"
    ENV_EXAMPLE_PATH="/app/.env.example"
    
    # 如果 .env 文件不存在，从 .env.example 创建
    if [ ! -f "$ENV_FILE_PATH" ]; then
        if [ -f "$ENV_EXAMPLE_PATH" ]; then
            log_info "从 .env.example 创建 .env 文件"
            cp "$ENV_EXAMPLE_PATH" "$ENV_FILE_PATH"
            log_info "✅ .env 文件已创建，包含所有默认配置参数"
            log_warn "⚠️  请通过前端界面配置您的 API 密钥和其他设置"
            
            # 显示创建的配置项数量
            CONFIG_COUNT=$(grep -c "^[A-Z_]*=" "$ENV_FILE_PATH" 2>/dev/null || echo "0")
            log_info "📋 已加载 $CONFIG_COUNT 个默认配置参数"
        else
            log_warn ".env.example 文件不存在，创建空的 .env 文件"
            touch "$ENV_FILE_PATH"
        fi
    else
        log_info ".env 文件已存在，跳过初始化"
        # 显示现有配置项数量
        CONFIG_COUNT=$(grep -c "^[A-Z_]*=" "$ENV_FILE_PATH" 2>/dev/null || echo "0")
        log_info "📋 当前 .env 文件包含 $CONFIG_COUNT 个配置参数"
    fi
}

# 创建必要的目录
create_directories() {
    log_info "创建必要的目录结构..."
    
    mkdir -p logs
    mkdir -p arxiv_history
    mkdir -p data/users
    
    # 设置目录权限
    chmod 755 logs arxiv_history data data/users 2>/dev/null || true
    
    log_info "目录结构创建完成"
}

# 初始化用户分类文件
init_user_categories() {
    if [ ! -f "data/users/user_categories.json" ]; then
        log_info "创建默认用户分类配置文件"
        cat > data/users/user_categories.json << EOF
{
    "default_user": {
        "categories": ["cs.CV", "cs.LG", "cs.AI"],
        "keywords": ["machine learning", "computer vision", "artificial intelligence"],
        "created_at": "$(date -Iseconds)",
        "updated_at": "$(date -Iseconds)"
    }
}
EOF
    fi
}

# 主函数
main() {
    log_info "=== ArXiv 每日论文推荐系统 - 后端容器启动 ==="
    log_info "容器启动时间: $(date)"
    log_info "工作目录: $(pwd)"
    log_info "Python版本: $(python --version)"
    
    # 执行初始化步骤
    init_env_file
    create_directories
    init_user_categories
    
    log_info "=== 初始化完成，启动 FastAPI 服务 ==="
    
    # 启动应用
    exec "$@"
}

# 执行主函数
main "$@"

