# AutoAntiCC - Cloudflare WAF 自动防护脚本

## 项目简介

AutoAntiCC 是一个基于系统负载监控的自动化防护脚本，用于在服务器遭受 CC（Challenge Collapsar）攻击或高负载时，自动启用 Cloudflare WAF（Web Application Firewall）规则，提供实时防护。当系统负载恢复正常后，脚本会自动禁用 WAF 规则，确保正常访问不受影响。

## 功能特性

- **智能负载监控**：实时监控系统 1 分钟平均负载
- **自动开盾防护**：当负载超过预设阈值时，自动启用 Cloudflare WAF 规则
- **自动关盾恢复**：负载恢复正常后，自动禁用 WAF 规则
- **防重复执行**：记录开盾时间，防止短时间内重复操作
- **跨平台支持**：支持 Linux、macOS 等 Unix-like 系统
- **详细日志输出**：提供完整的操作日志和错误信息

## 工作原理

1. **负载检测**：脚本定期检查系统 1 分钟平均负载
2. **阈值判断**：如果负载超过预设阈值（默认 80.0），则触发防护机制
3. **开盾操作**：调用 Cloudflare API 启用指定的 WAF 规则
4. **记录时间**：将开盾时间记录到本地文件 `cloudflare.txt`
5. **恢复检测**：负载恢复正常后，检查开盾时间是否超过 15 分钟
6. **关盾操作**：如果开盾时间超过 15 分钟，则禁用 WAF 规则
7. **清理记录**：关盾成功后清除开盾记录

## 系统要求

- Python 3.6 或更高版本
- 支持 `os.getloadavg()` 的系统（Linux、macOS 等 Unix-like 系统）
- Cloudflare 账户及 API 访问权限
- `requests` 库（通过 pip 安装）

## 安装步骤

### 1. 克隆或下载脚本

```bash
# 将脚本下载到您的服务器
git clone <repository-url>
cd autoanticc
```

### 2. 安装 Python 依赖

```bash
pip install requests
```

或者创建 `requirements.txt` 文件：

```txt
requests>=2.25.0
```

然后运行：

```bash
pip install -r requirements.txt
```

### 3. 配置 Cloudflare API 信息

打开 `cloudflare.py` 文件，找到 `main()` 函数中的以下参数并填写您的信息：

```python
# 必填参数
api_token = "YOUR_CLOUDFLARE_API_TOKEN"      # Cloudflare API 令牌
zone_id = "YOUR_ZONE_ID"                     # 区域 ID
ruleset_id = "YOUR_RULESET_ID"               # 规则集 ID
rule_id = "YOUR_RULE_ID"                     # 规则 ID

# 负载阈值 (1分钟平均负载)
load_threshold = 80.0
```

## 获取 Cloudflare API 信息

### 1. 获取 API 令牌

1. 登录 Cloudflare 控制台
2. 进入 "My Profile" → "API Tokens"
3. 点击 "Create Token"
4. 选择 "Edit zone WAF" 模板
5. 选择需要授权的域名
6. 创建令牌并复制保存

### 2. 获取区域 ID (Zone ID)

1. 在 Cloudflare 控制台选择您的域名
2. 在右侧 "API" 部分找到 "Zone ID"
3. 复制该 ID

### 3. 获取规则集 ID 和规则 ID

1. 进入 Cloudflare 控制台 → 您的域名 → "Security" → "WAF"
2. 找到您要管理的规则集
3. 从 URL 或 API 响应中获取规则集 ID 和规则 ID

或者通过 Cloudflare API 获取：

```bash
# 列出所有规则集
curl -X GET "https://api.cloudflare.com/client/v4/zones/{zone_id}/rulesets" \
     -H "Authorization: Bearer {api_token}" \
     -H "Content-Type: application/json"

# 查看特定规则集的规则
curl -X GET "https://api.cloudflare.com/client/v4/zones/{zone_id}/rulesets/{ruleset_id}/rules" \
     -H "Authorization: Bearer {api_token}" \
     -H "Content-Type: application/json"
```

## 使用方法

### 1. 手动运行测试

```bash
python cloudflare.py
```

### 2. 配置为定时任务（推荐）

使用 crontab 设置每分钟检查一次：

```bash
# 编辑当前用户的 crontab
crontab -e

# 添加以下行（请根据实际路径修改）
* * * * * cd /path/to/autoanticc && /usr/bin/python3 cloudflare.py >> /var/log/autoanticc.log 2>&1
```

### 3. 日志查看

脚本运行时会在控制台输出详细日志，如果配置了 crontab 重定向，可以查看日志文件：

```bash
tail -f /var/log/autoanticc.log
```

## 参数说明

### 主要函数

#### `enable_waf_rule(api_token, zone_id, ruleset_id, rule_id, enabled=True)`
启用或禁用 Cloudflare WAF 规则

**参数：**
- `api_token`：Cloudflare API 令牌
- `zone_id`：区域 ID
- `ruleset_id`：规则集 ID
- `rule_id`：规则 ID
- `enabled`：是否启用规则（True=启用，False=禁用）

#### `check_load_and_enable_rule(api_token, zone_id, ruleset_id, rule_id, threshold=80.0)`
检查系统负载并在需要时启用/禁用 WAF 规则

**参数：**
- `threshold`：负载阈值（1分钟平均负载），默认 80.0

### 配置文件参数

在 `cloudflare.py` 的 `main()` 函数中可调整：

- `load_threshold`：触发开盾的负载阈值，根据您的服务器配置调整
- 时间窗口：开盾后至少保持 15 分钟（可在代码中修改）

## 文件说明

- `cloudflare.py`：主脚本文件
- `cloudflare.txt`：开盾时间记录文件（脚本自动生成）

## 故障排除

### 常见问题

1. **"当前系统不支持负载监控"**
   - 原因：脚本在 Windows 或不支持 `os.getloadavg()` 的系统上运行
   - 解决方案：在 Linux 或 macOS 系统上运行

2. **API 调用失败**
   - 检查 API 令牌是否正确且具有足够权限
   - 验证 zone_id、ruleset_id、rule_id 是否正确
   - 检查网络连接是否正常

3. **负载阈值不合适**
   - 根据服务器 CPU 核心数调整 `load_threshold` 值
   - 建议设置为 CPU 核心数的 70-80%

4. **脚本没有执行开盾操作**
   - 检查系统负载是否真的超过阈值
   - 查看日志确认是否有错误信息
   - 检查开盾记录文件是否存在且时间有效

### 调试模式

要查看更详细的调试信息，可以在脚本中添加调试输出：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 安全注意事项

1. **API 令牌安全**：不要将 API 令牌提交到版本控制系统
2. **文件权限**：确保脚本和记录文件只有授权用户可访问
3. **监控配置**：合理设置负载阈值，避免误触发
4. **备份配置**：定期备份您的 Cloudflare WAF 规则配置

## 扩展和定制

### 1. 修改时间窗口

要修改开盾后保持的时间（默认为 15 分钟），修改以下位置：

```python
# 在 check_load_and_enable_rule 函数中
if time_diff > 15:  # 将 15 改为您想要的分钟数
```

### 2. 添加邮件通知

可以在开盾/关盾时添加邮件通知功能：

```python
import smtplib
from email.mime.text import MIMEText

def send_email_notification(subject, message):
    # 实现邮件发送逻辑
    pass
```

### 3. 集成监控系统

可以将脚本集成到现有的监控系统（如 Prometheus、Zabbix）中。

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件（如有）。

## 贡献

欢迎提交 Issue 和 Pull Request 来改进本项目。

## 免责声明

本工具为自动化防护脚本，请根据自身业务需求测试和调整参数。作者不对因使用本工具造成的任何直接或间接损失负责。

---

**重要提示**：在使用本脚本前，请确保您了解 Cloudflare WAF 规则的影响，并在测试环境中充分验证。