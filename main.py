import os
import requests
import time
from datetime import datetime
from bs4 import BeautifulSoup

class TiebaSigner:
    def __init__(self, bduss):
        self.session = requests.Session()
        self.cookies = {"BDUSS": bduss}
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
    
    def get_tbs(self):
        """获取tbs令牌"""
        url = "http://tieba.baidu.com/dc/common/tbs"
        try:
            response = self.session.get(url, cookies=self.cookies, headers=self.headers, timeout=10)
            result = response.json()
            if result.get("is_login") == 0:
                print("登录状态失效，请检查BDUSS")
                return ""
            return result.get("tbs", "")
        except Exception as e:
            print(f"获取tbs失败: {e}")
            return ""
    
    def get_forums(self):
        """使用BeautifulSoup解析关注的贴吧列表"""
        forums = []
        page = 1
        while True:
            url = f"http://tieba.baidu.com/f/like/mylike?pn={page}"
            try:
                response = self.session.get(url, cookies=self.cookies, headers=self.headers, timeout=10)
                response.encoding = 'gbk'  # 贴吧返回的数据是gbk编码
                
                # 检查登录状态
                if "您尚未登录" in response.text:
                    print("登录状态失效，请检查BDUSS")
                    return []
                
                # 使用BeautifulSoup解析HTML
                soup = BeautifulSoup(response.text, 'lxml')
                
                # 查找所有贴吧行 - 每个贴吧都在一个<tr>标签中
                rows = soup.find_all('tr', attrs={'class': 'j_forum_row'})
                
                # 如果没有找到贴吧行，尝试另一种选择器
                if not rows:
                    rows = soup.select('tr[class^="forum"]')
                
                # 如果没有找到任何贴吧行，结束循环
                if not rows:
                    print(f"第 {page} 页未找到贴吧列表")
                    break
                
                # 解析每个贴吧名称
                for row in rows:
                    # 查找包含贴吧名称的单元格
                    name_cell = row.find('td', class_='forum_name')
                    if name_cell:
                        # 获取贴吧名称
                        forum_name = name_cell.a.text.strip()
                        if forum_name:
                            forums.append(forum_name)
                
                # 检查是否有下一页
                next_page = soup.find('a', text='下一页>')
                if not next_page:
                    break
                    
                page += 1
                time.sleep(1)  # 避免请求过快
            except Exception as e:
                print(f"获取贴吧列表失败: {e}")
                break
        return list(set(forums))  # 去重
    
    def sign_forum(self, forum_name):
        """单个贴吧签到"""
        tbs = self.get_tbs()
        if not tbs:
            return False
        
        url = "https://tieba.baidu.com/sign/add"
        data = {
            "ie": "utf-8",
            "kw": forum_name,
            "tbs": tbs
        }
        
        try:
            response = self.session.post(url, data=data, cookies=self.cookies, headers=self.headers, timeout=10)
            result = response.json()
            if result.get("no") == 0:
                return True
            # 处理特定错误码
            if result.get("error") == "160002":  # 已签到
                print(f"✓ {forum_name} 今日已签到")
                return True
            print(f"签到失败 {forum_name}: {result.get('error', '未知错误')}")
        except Exception as e:
            print(f"签到异常 {forum_name}: {e}")
        return False
    
    def sign_all(self):
        """签到所有贴吧"""
        print(f"\n开始签到 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        forums = self.get_forums()
        if not forums:
            print("未获取到贴吧列表，签到终止")
            return 0
            
        print(f"获取到 {len(forums)} 个贴吧")
        
        success = 0
        total = len(forums)
        for i, forum in enumerate(forums):
            print(f"签到进度: {i+1}/{total} - {forum.ljust(15)}", end='\r')
            if self.sign_forum(forum):
                success += 1
            time.sleep(1.5)  # 防止请求过快被封
        
        print(f"\n签到完成: 成功 {success}/{total}")
        return success

if __name__ == "__main__":
    # 从环境变量获取BDUSS
    BDUSS = os.getenv('BDUSS')
    if not BDUSS:
        print("环境变量中未找到BDUSS")
        exit(1)
        
    signer = TiebaSigner(BDUSS)
    signer.sign_all()
