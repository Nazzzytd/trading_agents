# debug_myfxbook_api.py
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

def explore_myfxbook_api():
    """探索MyFXBook可用的API端点"""
    
    email = os.getenv("MYFXBOOK_EMAIL")
    password = os.getenv("MYFXBOOK_PASSWORD")
    
    if not email or not password:
        print("❌ 请先设置环境变量")
        return
    
    print("🔍 探索MyFXBook API端点...")
    print(f"邮箱: {email}")
    print(f"密码: {'*' * len(password)}")
    
    # 1. 登录获取session
    login_url = "https://www.myfxbook.com/api/login.json"
    params = {"email": email, "password": password, "debug": "1"}
    
    print(f"\n1. 登录: {login_url}")
    response = requests.get(login_url, params=params)
    print(f"   状态码: {response.status_code}")
    
    data = response.json()
    print(f"   响应: {json.dumps(data, indent=2)}")
    
    if data.get("error"):
        print("❌ 登录失败")
        return
    
    session = data.get("session")
    print(f"✅ Session: {session[:30]}...")
    
    # 2. 测试可能的日历端点
    base_url = "https://www.myfxbook.com/api"
    endpoints = [
        "/economic-calendar.json",
        "/get-economic-calendar.json", 
        "/calendar.json",
        "/calendar/economic.json",
        "/getEconomicCalendar.json",
        "/economicCalendar.json",
        "/events.json",
        "/getEvents.json"
    ]
    
    print("\n2. 测试日历端点:")
    for endpoint in endpoints:
        url = base_url + endpoint
        params = {"session": session, "debug": "1"}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            print(f"\n   {endpoint}:")
            print(f"     状态码: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"     数据类型: {type(data)}")
                    if isinstance(data, dict):
                        print(f"     字典键: {list(data.keys())}")
                        # 显示前几个键值对
                        for key, value in list(data.items())[:3]:
                            print(f"     {key}: {type(value)}")
                    elif isinstance(data, list):
                        print(f"     列表长度: {len(data)}")
                        if data:
                            print(f"     第一个元素: {data[0]}")
                except json.JSONDecodeError:
                    print(f"     内容: {response.text[:200]}")
            elif response.status_code == 404:
                print(f"     ❌ 端点不存在")
            else:
                print(f"     ⚠️ 状态码: {response.status_code}")
                
        except Exception as e:
            print(f"\n   {endpoint}: ❌ 错误: {e}")
    
    # 3. 测试其他可能有用的端点
    print("\n3. 测试其他可能端点:")
    other_endpoints = [
        "/get-community-outlook.json",  # 社区情绪
        "/get-daily-data.json",         # 每日数据
        "/data.json",                   # 通用数据
    ]
    
    for endpoint in other_endpoints:
        url = base_url + endpoint
        try:
            response = requests.get(url, params={"session": session}, timeout=5)
            if response.status_code == 200:
                print(f"   ✅ {endpoint}: 可用 (200)")
            elif response.status_code != 404:
                print(f"   ⚠️ {endpoint}: {response.status_code}")
        except:
            pass

if __name__ == "__main__":
    explore_myfxbook_api()