# 优化 CTA 框架工程质量

## 1. 清理与归档
- [ ] 将已弃用的 `cta_api/cta_core.py` 移动到 `_backup/legacy_code/` 目录，保持核心库整洁。

## 2. 增强日志系统
- [ ] 创建 `cta_api/logger.py`，配置标准日志格式（时间+级别+消息）。
- [ ] 在 `cta_api/engine.py` 中替换 `print` 为 `logger.info/error`，实现规范化输出。

## 3. 核心代码类型增强
- [ ] 为 `cta_api/function.py` 中的 `cal_equity_curve` 等核心函数添加 Python 类型提示 (Type Hints)，提高代码健壮性。
