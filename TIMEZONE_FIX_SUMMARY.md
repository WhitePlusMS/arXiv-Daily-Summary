# 时区配置修复说明

## 问题描述

生成报告时，文件名中的日期（如 `2025-11-10_TEST_ARXIV_summary.md`）使用的是系统本地时区，而不是配置文件中设置的 `TIMEZONE` 参数。

## 解决方案

根据**第一性原则**和**金字塔原则**，从根本原因入手，自底向上构建解决方案：

### 1. 核心层：添加时区工具函数（`core/common_utils.py`）

新增两个基础函数，提供时区感知的日期时间功能：

- **`get_timezone_aware_now(timezone_str=None)`**
  - 功能：获取指定时区的当前时间
  - 参数：时区字符串（如 'Asia/Shanghai'），如果为None则从环境变量 TIMEZONE 读取
  - 返回：时区感知的 datetime 对象
  - 容错：如果时区无效，自动回退到 UTC 时区

- **`format_timezone_date(date_format=None, timezone_str=None)`**
  - 功能：格式化时区感知的当前日期
  - 参数：日期格式和时区字符串，支持从环境变量读取
  - 返回：格式化后的日期字符串（默认 'YYYY-MM-DD'）

### 2. 中间层：修改输出管理器（`core/output_manager.py`）

修改所有生成文件名的函数，使用新的时区工具函数：

- `save_markdown_report()` - Markdown 报告保存
- `save_markdown_report_as_html()` - HTML 报告保存
- `save_markdown_report_as_html_separated()` - 分离内容的 HTML 报告保存

**修改前：**
```python
date_str = target_date if target_date else datetime.datetime.now().strftime("%Y-%m-%d")
```

**修改后：**
```python
date_str = target_date if target_date else format_timezone_date()
```

### 3. 应用层：修改 CLI 主程序（`core/arxiv_cli.py`）

更新所有涉及日期时间生成的地方：

#### 3.1 文件名生成（3处）
- `_save_markdown_if_configured()` - Markdown 文件名
- `_save_html_report_if_configured()` - HTML 文件名
- `_save_html_report_if_configured_separated()` - 分离内容的 HTML 文件名

#### 3.2 智能回溯模式（2处）
在尝试获取昨天和前天论文时，使用时区感知的日期计算：

**修改前：**
```python
target_date = datetime.now() - timedelta(days=days_back)
```

**修改后：**
```python
target_date = get_timezone_aware_now() - timedelta(days=days_back)
```

#### 3.3 调试模式（3处）
- 调试模式的目标日期生成
- 报告中的生成时间显示
- HTML 中的生成时间显示

#### 3.4 其他
- 时间戳格式的文件名生成

## 技术实现

### 依赖库
- `pytz==2025.2`（项目已安装）

### 配置读取
从环境变量读取配置：
- `TIMEZONE`：时区设置（默认：'Asia/Shanghai'）
- `DATE_FORMAT`：日期格式（默认：'%Y-%m-%d'）

### 容错机制
1. 如果未配置 TIMEZONE，默认使用 'Asia/Shanghai'
2. 如果时区字符串无效，自动回退到 UTC 时区
3. 记录警告日志，便于调试

## 影响范围

### 修改的文件
- ✅ `core/common_utils.py` - 新增时区工具函数
- ✅ `core/output_manager.py` - 修改文件名生成逻辑（3处）
- ✅ `core/arxiv_cli.py` - 修改日期时间生成逻辑（9处）

### 向后兼容性
- ✅ 完全向后兼容
- ✅ 如果不配置 TIMEZONE，行为与之前保持一致
- ✅ 现有的 target_date 参数优先级保持不变

## 测试结果

测试时区功能：
```
[OK] Configured timezone: Asia/Shanghai
[OK] Timezone-aware current time: 2025-11-11 15:04:23.764391+08:00
[OK] Formatted date: 2025-11-11
[SUCCESS] All tests completed!
```

## 使用方法

### 配置时区
在 `.env` 文件中设置：

```env
# 时区配置（必须是 pytz 支持的时区字符串）
TIMEZONE=Asia/Shanghai

# 可选：自定义日期格式
DATE_FORMAT=%Y-%m-%d
```

### 支持的时区示例
- `Asia/Shanghai` - 中国上海
- `America/New_York` - 美国纽约
- `Europe/London` - 英国伦敦
- `Asia/Tokyo` - 日本东京
- `UTC` - 协调世界时

更多时区请参考：[pytz 时区列表](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)

## 修复验证

生成报告后，文件名中的日期将使用配置的时区：

**修复前：**
```
2025-11-10_TEST_ARXIV_summary.md  # 使用系统本地时区
```

**修复后：**
```
2025-11-11_TEST_ARXIV_summary.md  # 使用配置的 TIMEZONE（Asia/Shanghai）
```

## 注意事项

1. **时区格式**：必须使用 pytz 支持的时区字符串（如 `Asia/Shanghai`），不支持缩写（如 `CST`）
2. **日期格式**：可以自定义 `DATE_FORMAT`，但建议保持默认的 `%Y-%m-%d` 格式
3. **日志查看**：如果时区配置有问题，系统会记录警告日志并回退到 UTC 时区

## 相关文档

- [Python pytz 文档](https://pythonhosted.org/pytz/)
- [时区数据库](https://en.wikipedia.org/wiki/Tz_database)

