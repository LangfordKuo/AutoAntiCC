import requests
import json
import sys
import os
import platform
import datetime

def enable_waf_rule(api_token, zone_id, ruleset_id, rule_id, enabled=True):
    """
    启用或禁用 CloudFlare WAF 规则
    
    参数:
        api_token (str): CloudFlare API 令牌
        zone_id (str): 区域 ID
        ruleset_id (str): 规则集 ID
        rule_id (str): 规则 ID
        enabled (bool): 是否启用规则，默认为 True
    """
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/rulesets/{ruleset_id}/rules/{rule_id}"
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    # 填写action，description，expression中的内容
    data = {
        "action": "",
        "description": "",
        "enabled": enabled,
        "expression": "",
        "id": rule_id,
        "ref": rule_id,
    }
    
    try:
        response = requests.patch(url, headers=headers, json=data)
        response.raise_for_status()
        
        result = response.json()
        if result.get("success"):
            return True
        else:
            # API返回错误，输出详细错误信息
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"{current_time} API调用失败，错误详情:")
            print(f"  状态码: {response.status_code}")
            print(f"  响应内容: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return False
            
    except requests.exceptions.RequestException as e:
        # 网络请求异常，输出详细错误信息
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{current_time} 网络请求异常:")
        print(f"  异常类型: {type(e).__name__}")
        print(f"  异常信息: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"  状态码: {e.response.status_code}")
            try:
                error_content = e.response.json()
                print(f"  错误内容: {json.dumps(error_content, indent=2, ensure_ascii=False)}")
            except:
                print(f"  错误内容: {e.response.text[:500]}")
        return False
    except json.JSONDecodeError as e:
        # JSON解析异常，输出详细错误信息
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{current_time} JSON解析异常:")
        print(f"  异常信息: {str(e)}")
        if hasattr(response, 'text'):
            print(f"  原始响应: {response.text[:500]}")
        return False

def get_shield_record_file():
    """
    获取盾牌记录文件的完整路径
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, "cloudflare.txt")

def record_shield_enabled():
    """
    记录开盾时间到文件
    """
    try:
        file_path = get_shield_record_file()
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(current_time)
        print(f"开盾时间已记录: {current_time}")
        return True
    except Exception as e:
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{current_time} 记录开盾时间失败: {e}")
        return False

def has_recent_shield_record(minutes=15):
    """
    检查是否有最近的开盾记录
    
    参数:
        minutes (int): 时间窗口（分钟），默认为15分钟
    
    返回:
        bool: 如果存在且在时间窗口内返回True，否则返回False
    """
    try:
        file_path = get_shield_record_file()
        if not os.path.exists(file_path):
            return False
        
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        
        if not content:
            return False
        
        # 解析记录的时间
        record_time = datetime.datetime.strptime(content, "%Y-%m-%d %H:%M:%S")
        current_time = datetime.datetime.now()
        
        # 计算时间差（分钟）
        time_diff = (current_time - record_time).total_seconds() / 60.0
        
        if time_diff <= minutes:
            return True
        else:
            return False
    except Exception as e:
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{current_time} 检查开盾记录失败: {e}")
        return False

def clear_shield_record():
    """
    清空开盾记录文件
    """
    try:
        file_path = get_shield_record_file()
        if os.path.exists(file_path):
            os.remove(file_path)
            print("开盾记录已清空")
            return True
        return True  # 文件不存在也视为成功
    except Exception as e:
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{current_time} 清空开盾记录失败: {e}")
        return False

def check_load_and_enable_rule(api_token, zone_id, ruleset_id, rule_id, threshold=80.0):
    """
    检查系统负载并在负载超过阈值时启用 WAF 规则
    """
    # 检查当前操作系统是否支持 os.getloadavg()
    system = platform.system()
    if system not in ["Linux", "Darwin", "Unix"]:
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{current_time} 当前系统 {system} 不支持负载监控，跳过检查")
        return False
    
    try:
        # 获取系统负载平均值 (1分钟, 5分钟, 15分钟)
        load_avg = os.getloadavg()
        load_1min = load_avg[0]
        
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if load_1min > threshold:
            # 负载超过阈值，需要检查是否已有最近的开盾记录
            if has_recent_shield_record(minutes=15):
                print(f"{current_time} 检测到CPU负载{load_1min:.2f}，超过阈值{threshold}，但已有最近的开盾记录，跳过重复执行")
                return True
            else:
                print(f"{current_time} 检测到CPU负载{load_1min:.2f}，超过阈值{threshold}，执行开盾策略")
                
                # 启用 WAF 规则
                success = enable_waf_rule(api_token, zone_id, ruleset_id, rule_id, enabled=True)
                
                if success:
                    print(f"{current_time} 调用API开盾成功")
                    # 记录开盾时间
                    record_shield_enabled()
                    return True
                else:
                    print(f"{current_time} 调用API开盾失败")
                    return False
        else:
            # 负载正常，检查是否需要自动关盾
            print(f"{current_time} 检测到CPU负载{load_1min:.2f}，未超过阈值{threshold}")
            
            # 检查是否有开盾记录
            try:
                file_path = get_shield_record_file()
                if os.path.exists(file_path):
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                    
                    if content:
                        # 解析记录的时间
                        record_time = datetime.datetime.strptime(content, "%Y-%m-%d %H:%M:%S")
                        current_time_dt = datetime.datetime.now()
                        time_diff = (current_time_dt - record_time).total_seconds() / 60.0
                        
                        if time_diff > 15:
                            print(f"{current_time} 检测到开盾记录已超过15分钟({time_diff:.1f}分钟)，执行关盾策略")
                            
                            # 禁用 WAF 规则
                            success = enable_waf_rule(api_token, zone_id, ruleset_id, rule_id, enabled=False)
                            
                            if success:
                                print(f"{current_time} 调用API关盾成功")
                                clear_shield_record()
                                return True
                            else:
                                print(f"{current_time} 调用API关盾失败")
                                return False
                        else:
                            print(f"{current_time} 开盾记录仍在有效期内({time_diff:.1f}分钟)，无需操作")
                            return True
                    else:
                        # 文件存在但内容为空
                        clear_shield_record()
                        return True
                else:
                    # 无开盾记录，无需操作
                    return True
            except Exception as e:
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"{current_time} 检查开盾记录时发生错误: {e}")
                return False
            
    except AttributeError:
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{current_time} 当前操作系统不支持 os.getloadavg()")
        return False
    except Exception as e:
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{current_time} 获取系统负载时发生错误: {e}")
        return False

def main():
    # 必填参数
    api_token = ""
    zone_id = ""
    ruleset_id = ""
    rule_id = ""
    
    # 负载阈值 (1分钟平均负载)
    load_threshold = 80.0
    
    # 检查系统负载并在需要时启用规则
    success = check_load_and_enable_rule(
        api_token=api_token,
        zone_id=zone_id,
        ruleset_id=ruleset_id,
        rule_id=rule_id,
        threshold=load_threshold
    )
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()