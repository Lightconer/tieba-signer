#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
百度贴吧自动签到脚本（手机客户端接口版）

特性：
- 使用手机端签到接口 c.tieba.baidu.com/c/c/forum/sign，单吧经验 +6（PC 网页端仅 +2）
- 仅需 BDUSS，自动获取关注的贴吧列表，无需手动维护吧名
- 最多支持 200 个贴吧（贴吧关注上限），自动跳过今日已签到的吧
- 兼容 GitHub Actions 定时部署 / 本地 Python / Docker 运行
- 支持多账号（BDUSS 用 # 分隔）

用法：
    # 本地运行
    python tieba_sign.py            # 读取环境变量 BDUSS
    或
    $env:BDUSS="你的BDUSS"; python tieba_sign.py

接口说明：
    GET  http://tieba.baidu.com/dc/common/tbs       获取 tbs 并校验登录态（仅需 BDUSS）
    GET  https://tieba.baidu.com/mo/q/newmoindex    获取关注的吧列表（手机版，仅需 BDUSS，一次返回全部）
    POST http://c.tieba.baidu.com/c/c/forum/sign    手机端签到（经验 +6）

免责声明：本脚本仅用于学习与技术交流，请勿用于任何违反相关平台规则的用途。
"""

import hashlib
import os
import random
import sys
import time

import requests

# ---------------------------------------------------------------------------
# 常量配置
# ---------------------------------------------------------------------------
TBS_URL = "http://tieba.baidu.com/dc/common/tbs"       # 获取 tbs
LIKE_URL = "https://tieba.baidu.com/mo/q/newmoindex"   # 获取关注的吧（手机版）
SIGN_URL = "http://c.tieba.baidu.com/c/c/forum/sign"   # 手机端签到接口

SIGN_INTERVAL = (2.0, 4.0)   # 每个吧签到之间的随机间隔(秒)，避免触发风控
REQUEST_TIMEOUT = 15         # 单次请求超时(秒)
MAX_FORUMS = 200             # 最多签到数量（贴吧关注上限）

USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 10; SM-G9810) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36"
)

# 签到返回错误码含义
ERROR_MSG = {
    "0": "签到成功",
    "160002": "今日已签到",
    "340006": "贴吧目录异常",
    "110001": "吧名含 + 号未转义",
    "1990055": "操作过于频繁",
}


class TiebaSigner:
    """贴吧签到器：登录校验 -> 获取关注列表 -> 逐吧签到"""

    def __init__(self, bduss: str):
        self.bduss = bduss.strip()
        self.cookies = {"BDUSS": self.bduss}
        self.session = requests.Session()
        self.session.headers["User-Agent"] = USER_AGENT

    # -- 1. 获取 tbs 并校验登录态 ------------------------------------------
    def get_tbs(self) -> str:
        resp = self.session.get(
            TBS_URL, cookies=self.cookies, timeout=REQUEST_TIMEOUT
        )
        data = resp.json()
        if data.get("is_login") != 1:
            raise RuntimeError(
                f"BDUSS 无效或已过期：{data.get('error', '未知错误')}"
            )
        return data["tbs"]

    # -- 2. 获取关注的贴吧列表 ----------------------------------------------
    def get_like_forums(self) -> list:
        resp = self.session.get(
            LIKE_URL, cookies=self.cookies, timeout=REQUEST_TIMEOUT
        )
        data = resp.json()
        forums = data.get("data", {}).get("like_forum", []) or []
        # 贴吧关注上限约 200 个，这里再兜底截断
        return forums[:MAX_FORUMS]

    # -- 3. 生成手机端接口签名 ----------------------------------------------
    @staticmethod
    def _make_sign(kw: str, tbs: str) -> str:
        raw = f"kw={kw}tbs={tbs}tiebaclient!!!"
        return hashlib.md5(raw.encode("utf-8")).hexdigest()

    # -- 4. 签到单个贴吧 -----------------------------------------------------
    def sign_one(self, kw: str, tbs: str) -> dict:
        # 吧名中的 + 需要转义为 %2B（否则报错码 110001）
        kw_esc = kw.replace("+", "%2B")
        payload = {
            "kw": kw_esc,
            "tbs": tbs,
            "sign": self._make_sign(kw, tbs),
        }
        resp = self.session.post(
            SIGN_URL, cookies=self.cookies, data=payload,
            timeout=REQUEST_TIMEOUT,
        )
        return resp.json()

    # -- 5. 主流程 ------------------------------------------------------------
    def run(self) -> dict:
        print("=" * 56)
        print("  百度贴吧自动签到（手机客户端接口 · 经验 +6/吧）")
        print("=" * 56)

        # ① 登录校验
        tbs = self.get_tbs()
        print(f"[OK] 登录校验通过，tbs={tbs}")

        # ② 获取关注列表
        forums = self.get_like_forums()
        total = len(forums)
        print(f"[OK] 获取关注列表成功，共 {total} 个贴吧")

        if total == 0:
            print("[!] 没有获取到任何关注的贴吧，请检查 BDUSS 是否有效")
            return {"total": 0, "success": 0, "already": 0, "failed": 0}

        # ③ 过滤今日已签到的
        pending = [f for f in forums if f.get("is_sign") != 1]
        signed_cnt = total - len(pending)
        print(f"[OK] 今日已签到 {signed_cnt} 个，待签到 {len(pending)} 个\n")

        # ④ 逐吧签到
        success = already = failed = 0
        fail_details = []
        for i, forum in enumerate(pending, 1):
            kw = forum.get("forum_name", "")
            if not kw:
                continue
            try:
                result = self.sign_one(kw, tbs)
                code = str(result.get("error_code", "unknown"))
                msg = result.get("error_msg", "")
                if code == "0":
                    success += 1
                    print(f"  [{i}/{len(pending)}]  ✔  {kw}  →  {ERROR_MSG.get(code, msg)}")
                elif code == "160002":
                    already += 1
                    print(f"  [{i}/{len(pending)}]  ≡  {kw}  →  {ERROR_MSG.get(code, msg)}")
                else:
                    failed += 1
                    fail_details.append((kw, code, msg))
                    print(f"  [{i}/{len(pending)}]  ✘  {kw}  →  {ERROR_MSG.get(code, msg)} (code={code})")
            except Exception as exc:
                failed += 1
                fail_details.append((kw, "exception", str(exc)))
                print(f"  [{i}/{len(pending)}]  ✘  {kw}  →  请求异常：{exc}")

            # 随机间隔，降低风控概率
            if i < len(pending):
                time.sleep(random.uniform(*SIGN_INTERVAL))

        # ⑤ 汇总
        print("\n" + "=" * 56)
        print(f"签到完成 → 成功 {success} | 今日已签 {already} | 失败 {failed} | 共 {total}")
        if fail_details:
            print("失败明细（前 20 条）：")
            for kw, code, msg in fail_details[:20]:
                print(f"  - {kw}: {code} {msg}")
        print("=" * 56)
        return {"total": total, "success": success, "already": already, "failed": failed}


def main() -> None:
    bduss_raw = os.getenv("BDUSS", "").strip()
    if not bduss_raw:
        print("错误：未检测到环境变量 BDUSS。")
        print("  - GitHub Actions：在仓库 Settings → Secrets and variables → Actions 中添加 BDUSS")
        print("  - 本地运行：$env:BDUSS='你的BDUSS'; python tieba_sign.py")
        sys.exit(1)

    # 多账号支持：BDUSS 之间用 # 分隔
    accounts = [a for a in bduss_raw.replace("\n", "#").split("#") if a.strip()]
    for idx, account in enumerate(accounts, 1):
        if len(accounts) > 1:
            print(f"\n===== 账号 {idx}/{len(accounts)} =====")
        TiebaSigner(account).run()


if __name__ == "__main__":
    main()
