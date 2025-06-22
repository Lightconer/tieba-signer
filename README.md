# tieba-signer
# 百度贴吧自动签到脚本

使用 GitHub Actions 自动执行百度贴吧签到任务

## 使用说明

1. Fork 此仓库
2. 在仓库设置中添加 Secrets：
   - 名称: `BDUSS`
   - 值: 你的百度BDUSS值（从浏览器Cookie中获取）
3. 脚本将每天 UTC 时间 0:00（北京时间 8:00）自动运行

## 手动运行
1. 进入仓库的 Actions 标签页
2. 选择 "Tieba Sign" 工作流
3. 点击 "Run workflow" 手动执行

## 注意事项
- 请妥善保管你的BDUSS值，不要泄露
- 脚本仅用于学习目的，请勿滥用
