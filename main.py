"""
百度贴吧自动签到脚本
版本: 1.2.0
作者: DeepSeek-AI
日期: 2023-10-15

功能说明:
1. 使用百度BDUSS身份验证自动登录
2. 获取用户关注的所有贴吧列表
3. 为每个贴吧执行签到操作
4. 处理各种签到状态（成功、已签到、失败）
5. 提供详细的执行日志和统计信息
6. 支持GitHub Actions定时执行

注意事项:
- 需要将BDUSS存储在GitHub Secrets中
- 脚本使用BeautifulSoup解析HTML页面
- 请求之间设置了延迟以防止被百度限制
"""

import os
import re
import time
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import schedule  # 用于定时任务

class TiebaSigner:
    """
    百度贴吧签到器类
    
    主要功能:
    - 初始化会话和配置
    - 获取tbs安全令牌
    - 获取用户关注的贴吧列表
    - 执行单个贴吧签到
    - 执行所有贴吧签到
    
    参数:
    :param bduss: 百度用户身份验证令牌
    """
    
    def __init__(self, bduss):
        """
        初始化签到器
        
        :param bduss: 百度用户的BDUSS值，用于身份验证
        """
        # 创建持久会话对象，保持cookies
        self.session = requests.Session()
        
        # 设置cookies，BDUSS是百度账号的核心验证令牌
        self.cookies = {"BDUSS": bduss}
        
        # 设置请求头，模拟Chrome浏览器
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/91.0.4472.124 Safari/537.36"
        }
        
        # 请求超时时间（秒）
        self.timeout = 15
    
    def get_tbs(self):
        """
        获取tbs令牌 - 执行签到操作必需的安全令牌
        
        实现原理:
        1. 访问百度贴吧的tbs接口
        2. 解析返回的JSON数据
        3. 检查登录状态是否有效
        4. 提取tbs令牌
        
        返回:
        str: tbs令牌字符串，失败时返回空字符串
        """
        # tbs接口URL
        url = "http://tieba.baidu.com/dc/common/tbs"
        
        try:
            # 发送GET请求获取tbs
            response = self.session.get(
                url, 
                cookies=self.cookies, 
                headers=self.headers, 
                timeout=self.timeout
            )
            
            # 解析JSON响应
            data = response.json()
            
            # 检查登录状态 (1=已登录, 0=未登录)
            if data.get("is_login") == 0:
                print("[错误] 登录状态失效，请检查BDUSS")
                return ""
            
            # 返回tbs令牌
            return data.get("tbs", "")
            
        except requests.exceptions.RequestException as e:
            # 网络请求异常处理
            print(f"[网络错误] 获取tbs失败: {e}")
            return ""
        except ValueError as e:
            # JSON解析异常处理
            print(f"[解析错误] 无效的JSON响应: {e}")
            return ""
    
    def get_forums(self):
        """
        获取用户关注的贴吧列表
        
        实现原理:
        1. 分页查询用户关注的贴吧
        2. 使用BeautifulSoup解析HTML页面
        3. 提取贴吧名称
        4. 检查是否有下一页
        
        返回:
        list: 贴吧名称列表
        """
        forums = []  # 存储贴吧名称
        page = 1     # 起始页码
        
        # 循环处理所有分页
        while True:
            # 构建贴吧列表URL
            url = f"http://tieba.baidu.com/f/like/mylike?pn={page}"
            
            try:
                # 发送GET请求获取贴吧列表
                response = self.session.get(
                    url, 
                    cookies=self.cookies, 
                    headers=self.headers, 
                    timeout=self.timeout
                )
                
                # 设置正确的编码（百度使用GBK编码）
                response.encoding = 'gbk'
                
                # 检查登录状态 - 页面中是否包含未登录提示
                if "您尚未登录" in response.text:
                    print("[错误] 登录状态失效，请检查BDUSS")
                    return []
                
                # 使用BeautifulSoup解析HTML内容
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 查找所有包含贴吧名称的链接
                # 选择器说明：查找所有带有href属性且包含'/f?kw='的<a>标签
                forum_links = soup.select('a[href*="/f?kw="]')
                
                # 临时存储当前页的贴吧名称
                page_forums = []
                
                # 提取有效的贴吧名称
                for link in forum_links:
                    # 获取链接标题（贴吧名称）
                    forum_name = link.text.strip()
                    
                    # 过滤无效名称（空值或特殊名称）
                    if forum_name and forum_name not in ["百度首页", "吧广场", "进入贴吧"]:
                        page_forums.append(forum_name)
                
                # 如果没有找到贴吧，终止循环
                if not page_forums:
                    print(f"[信息] 第 {page} 页未找到贴吧列表")
                    break
                
                # 将当前页的贴吧添加到总列表
                forums.extend(page_forums)
                print(f"[信息] 第 {page} 页获取到 {len(page_forums)} 个贴吧")
                
                # 检查是否有下一页
                next_page = soup.find('a', text='下一页>')
                if not next_page:
                    break  # 没有下一页，终止循环
                
                # 准备请求下一页
                page += 1
                
                # 添加延迟，避免请求过快
                time.sleep(1)
                
            except requests.exceptions.RequestException as e:
                print(f"[网络错误] 获取贴吧列表失败: {e}")
                break
            except Exception as e:
                print(f"[解析错误] 处理页面时出错: {e}")
                break
        
        # 返回去重后的贴吧列表
        return list(set(forums))
    
    def sign_forum(self, forum_name):
        """
        为单个贴吧执行签到
        
        实现原理:
        1. 获取tbs安全令牌
        2. 构造签到请求
        3. 解析签到响应
        4. 处理各种签到状态
        
        :param forum_name: 要签到的贴吧名称
        :return: bool - 是否签到成功
        """
        # 步骤1: 获取tbs令牌
        tbs = self.get_tbs()
        if not tbs:
            print(f"[失败] {forum_name} - 无法获取tbs令牌")
            return False
        
        # 步骤2: 准备签到请求
        url = "https://tieba.baidu.com/sign/add"
        data = {
            "ie": "utf-8",     # 编码格式
            "kw": forum_name,  # 贴吧名称
            "tbs": tbs         # 安全令牌
        }
        
        try:
            # 步骤3: 发送签到POST请求
            response = self.session.post(
                url, 
                data=data, 
                cookies=self.cookies, 
                headers=self.headers, 
                timeout=self.timeout
            )
            
            # 解析JSON响应
            result = response.json()
            
            # 步骤4: 处理响应结果
            if result.get("no") == 0:
                # 签到成功
                print(f"[成功] {forum_name} - 签到成功")
                return True
            
            # 错误代码160002表示今日已签到
            if result.get("error") == "160002":
                print(f"[成功] {forum_name} - 今日已签到")
                return True
            
            # 其他错误情况
            error_msg = result.get("error", "未知错误")
            print(f"[失败] {forum_name} - 错误: {error_msg}")
            return False
            
        except requests.exceptions.RequestException as e:
            print(f"[网络错误] {forum_name} - 签到请求失败: {e}")
            return False
        except ValueError as e:
            print(f"[解析错误] {forum_name} - 无效的JSON响应: {e}")
            return False
    
    def sign_all(self):
        """
        执行所有贴吧签到
        
        实现原理:
        1. 获取贴吧列表
        2. 遍历每个贴吧执行签到
        3. 统计签到结果
        4. 输出最终报告
        
        返回:
        tuple: (成功数, 总数)
        """
        # 记录开始时间
        start_time = datetime.now()
        print(f"\n{'-'*50}")
        print(f"开始签到任务: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'-'*50}")
        
        # 步骤1: 获取贴吧列表
        print("[信息] 正在获取贴吧列表...")
        forums = self.get_forums()
        
        if not forums:
            print("[错误] 未获取到贴吧列表，任务终止")
            return 0, 0
        
        total = len(forums)
        print(f"[信息] 共获取到 {total} 个贴吧")
        
        # 步骤2: 遍历执行签到
        success = 0  # 成功计数器
        
        print("\n[信息] 开始签到...")
        for i, forum in enumerate(forums):
            # 显示进度信息
            progress = f"[进度] {i+1}/{total} ({((i+1)/total)*100:.1f}%)"
            print(f"{progress} - 正在签到: {forum.ljust(15)}", end='\r')
            
            # 执行签到并更新计数器
            if self.sign_forum(forum):
                success += 1
            
            # 添加请求延迟，防止被封IP
            time.sleep(1.5)
        
        # 步骤3: 输出统计结果
        print("\n" + "="*50)
        print("签到任务完成")
        print("="*50)
        
        # 计算耗时
        duration = datetime.now() - start_time
        mins, secs = divmod(duration.total_seconds(), 60)
        
        # 输出报告
        print(f"开始时间:    {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"完成时间:    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"总耗时:      {int(mins)}分{int(secs)}秒")
        print(f"贴吧总数:    {total}")
        print(f"签到成功:    {success}")
        print(f"失败/跳过:   {total - success}")
        
        # 计算成功率
        if total > 0:
            success_rate = (success / total) * 100
            print(f"成功率:      {success_rate:.1f}%")
        
        print("="*50 + "\n")
        
        return success, total

def job(bduss):
    """
    定时任务执行函数
    
    :param bduss: 百度用户的BDUSS值
    """
    print("="*50)
    print("执行定时签到任务")
    print("="*50)
    
    # 创建签到器实例
    signer = TiebaSigner(bduss)
    
    # 执行签到
    success, total = signer.sign_all()
    
    # 输出最终结果
    if total == 0:
        print("⚠️ 任务失败: 未获取到贴吧列表")
    else:
        print(f"✅ 任务完成: 成功签到 {success}/{total} 个贴吧")

if __name__ == "__main__":
    """
    主程序入口
    
    功能:
    1. 从环境变量获取BDUSS
    2. 设置定时任务（每天8:00执行）
    3. 启动定时任务循环
    """
    # 从环境变量获取BDUSS
    BDUSS = os.getenv('BDUSS')
    
    if not BDUSS:
        print("❌ 错误: 未找到BDUSS环境变量")
        print("请确保已在GitHub Secrets中设置BDUSS")
        exit(1)
    
    # 立即执行一次测试（首次运行）
    print("⏩ 首次运行测试...")
    job(BDUSS)
    
    # 设置定时任务（每天北京时间8:00执行）
    # 注意：GitHub Actions使用UTC时间，北京时间=UTC+8
    schedule.every().day.at("00:00").do(job, BDUSS)  # UTC时间00:00 = 北京时间08:00
    
    print("\n" + "="*50)
    print("定时任务已启动")
    print(f"下次执行时间: UTC {schedule.next_run().strftime('%H:%M')} (北京时间 {schedule.next_run().hour+8}:{schedule.next_run().minute:02d})")
    print("="*50 + "\n")
    
    # 定时任务循环
    try:
        while True:
            # 运行待处理任务
            schedule.run_pending()
            
            # 计算距离下次执行的时间
            next_run = schedule.next_run()
            now = datetime.utcnow()
            seconds_until_next = (next_run - now).total_seconds()
            
            # 显示等待信息
            if seconds_until_next > 0:
                hours, remainder = divmod(seconds_until_next, 3600)
                minutes, seconds = divmod(remainder, 60)
                print(f"⏳ 下次执行: {int(hours)}小时{int(minutes)}分钟后，等待中...", end='\r')
            
            # 休眠60秒（减少CPU使用）
            time.sleep(60)
            
    except KeyboardInterrupt:
        # 处理Ctrl+C中断
        print("\n🛑 程序已手动终止")
