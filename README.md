# 百度贴吧自动签到（手机客户端接口版）

> 使用 **手机端接口** 签到，单吧经验 **+6**（PC 网页端仅 +2）。
> 你只需要提供 **BDUSS**，部署到 GitHub 后每日自动签到，**最多支持 200 个贴吧**。

## 功能特性

- ✅ 手机客户端签到接口，签到经验更多（+6/吧，PC 端仅 +2）
- ✅ 仅需 **BDUSS**，自动拉取关注的贴吧列表，无需手动维护吧名
- ✅ 自动跳过今日已签到的吧，最多支持 200 个贴吧
- ✅ 使用 GitHub Actions 定时任务，**每日 06:30（北京时间）自动签到**
- ✅ 支持多账号（BDUSS 用 `#` 分隔）
- ✅ 请求之间随机延时，降低风控概率
- ✅ 支持手动触发（补签 / 首次运行）

## 工作原理（接口说明）

| 用途 | 接口 | 说明 |
| --- | --- | --- |
| 获取 tbs + 校验登录 | `GET tieba.baidu.com/dc/common/tbs` | Cookie 携带 BDUSS，返回 `is_login` 与 `tbs` |
| 获取关注的吧 | `GET tieba.baidu.com/mo/q/newmoindex` | 手机版接口，一次返回全部关注（≤200），含 `is_sign` 是否已签 |
| 手机端签到 | `POST c.tieba.baidu.com/c/c/forum/sign` | 参数 `kw`、`tbs`、`sign`；`sign = md5("kw=吧名tbs=tbs值tiebaclient!!!")` |

> 返回码：`0`=签到成功；`160002`=今日已签到；`110001`=吧名含 `+` 未转义；`340006`=贴吧目录异常。

## 部署步骤（GitHub Actions）

### 1. Fork 本项目

点击仓库右上角 **Fork**，把项目复制到你自己的 GitHub 账号下。

### 2. 获取 BDUSS

1. 电脑浏览器登录 [百度贴吧](https://tieba.baidu.com/)；
2. 按 `F12` 打开开发者工具 → `Application/应用` → `Cookies` → `https://tieba.baidu.com`；
3. 找到 **`BDUSS`** 字段，复制它的 `Value`（一长串字符）。

> ⚠️ BDUSS 等同账号登录凭证，**切勿**提交到代码或公开渠道。

### 3. 添加 Secrets

进入你 Fork 后的仓库：

`Settings` → `Secrets and variables` → `Actions` → `New repository secret`

| Name | Value |
| --- | --- |
| `BDUSS` | 你复制的 BDUSS 值（多账号用 `#` 分隔） |

### 4. 开启 Actions

`Settings` → `Actions` → `General` → `Actions permissions` 选择 **Allow all actions and reusable workflows**（允许工作流运行）。

> ⚠️ 若仓库是从私有模板创建的，需确认仓库未被 Archive，且 `.github/workflows/` 已随 Fork 带入。

### 5. 首次运行

进入 `Actions` 页 → 左侧选择 **Tieba Auto Sign** → 右侧 **Run workflow** → 绿色按钮确认。

运行成功后，工作流即会在**每天北京时间 06:30** 自动签到。

> 也可以修改 `.github/workflows/tieba-sign.yml` 中 `cron: '30 22 * * *'`（UTC）调整签到时间。
> 例如想改到北京 08:00，则写 `cron: '0 0 * * *'`。

## 本地运行（可选）

```bash
# Windows PowerShell
$env:BDUSS = "你的BDUSS"
python tieba_sign.py

# Linux / macOS
export BDUSS="你的BDUSS"
python3 tieba_sign.py
```

首次运行前安装依赖：

```bash
pip install -r requirements.txt
```

## 目录结构

```
tieba-sign/
├── .github/
│   └── workflows/
│       └── tieba-sign.yml     # GitHub Actions 定时任务配置
├── docs/
│   ├── deploy_flow.png        # 部署流程图
│   └── make_deploy_flow.py    # 流程图生成脚本（可自行调整后重新生成）
├── tieba_sign.py              # 签到主脚本
├── requirements.txt           # Python 依赖
├── .gitignore
└── README.md
```

## 常见问题

| 现象 | 原因 / 处理 |
| --- | --- |
| 提示「BDUSS 无效或已过期」 | BDUSS 过期，重新登录贴吧获取并更新 Secrets |
| 某个吧签到失败 `160002` | 该吧今日已签到，属正常 |
| 某个吧签到失败 `110001` | 吧名含 `+`，脚本已自动转义，如仍出现可手动反馈 |
| 定时任务未触发 | 检查 `Settings → Actions` 是否已开启，且仓库未被禁用 |
| 连续多吧失败 | 可能触发风控，可调大 `SIGN_INTERVAL` 间隔 |

## 免责声明

本项目仅用于**学习与个人自动化签到**，请遵守百度贴吧相关规则与所在地区法律法规；请勿批量注册、滥用接口或用于任何商业与恶意用途。使用本项目产生的任何后果由使用者自行承担。
