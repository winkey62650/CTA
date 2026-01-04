# Quant/CTA

该仓库用于量化交易 CTA 项目代码的版本管理与协作。

## 快速开始
- 初始化已完成，默认分支为 `main`
- 建议首次提交包含 `.gitignore`、`.gitattributes` 和本文件

## 常用命令
- 查看状态：`git status`
- 添加文件：`git add <path>`
- 提交记录：`git commit -m "message"`
- 关联远程：`git remote add origin <repo-url>`
- 首次推送：`git push -u origin main`

## 推荐配置
- 设置身份：`git config user.name "<Your Name>"`，`git config user.email "<Your Email>"`
- 行尾统一：`.gitattributes` 已设置文本自动规范
- 大文件：如需跟踪数据文件（如 `data/`、`*.parquet`），考虑使用 Git LFS

## 目录建议
- `src/` 源码
- `data/` 原始与中间数据（慎入库或使用 LFS）
- `notebooks/` 研究笔记本
- `tests/` 测试用例

## 许可证
如需开源，建议选择 MIT 或 Apache-2.0；如仅内部使用可暂不添加。
