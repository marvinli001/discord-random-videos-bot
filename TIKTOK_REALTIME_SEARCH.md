# TikTok 实时搜索功能

## ✨ 功能说明

`/randomtiktok` 命令现在支持**实时搜索** TikTok 视频！

### 特点：
- 🔍 **实时搜索** - Bot 自动从 TikTok 搜索标签视频
- 🎲 **智能队列** - 已播放视频不重复，轮播完自动刷新
- 💾 **Redis 持久化** - 容器重启后保留播放进度
- 🔄 **自动刷新** - 每小时自动获取最新视频
- 🎵 **Discord 内嵌** - 自动转换为 vxtiktok.com 格式

## 🚀 快速开始

### 1. 安装依赖

Bot 启动时会自动安装，或手动运行：

```bash
pip install -r requirements.txt
python -m playwright install
```

### 2. 配置环境变量

在 `.env` 或 Railway 中设置：

```env
# TikTok 搜索标签（默认：cosplaydance）
TIKTOK_HASHTAG=cosplaydance

# 可选：ms_token 提高 API 稳定性
# TIKTOK_MS_TOKEN=your_ms_token_here
```

### 3. 使用命令

Discord 中输入：
```
/randomtiktok
```

Bot 会：
1. 搜索 #cosplaydance 标签
2. 随机选择一个视频
3. 自动转换为 Discord 可播放链接
4. 显示"下一个"按钮

## 📋 工作原理

### 搜索流程

```python
1. 初始化 TikTok API
   └─> TikTokApi() 创建会话

2. 搜索标签
   └─> api.hashtag("cosplaydance").videos(count=50)

3. 提取视频链接
   └─> https://tiktok.com/@username/video/123456

4. 转换为可嵌入格式
   └─> https://vxtiktok.com/@username/video/123456

5. 保存到队列并持久化
   └─> Redis 存储用户队列
```

### 缓存机制

- ✅ 首次搜索：从 TikTok 获取 50 个视频
- ✅ 后续请求：使用缓存（1小时内）
- ✅ 自动刷新：每小时重新搜索
- ✅ 降级模式：API 失败时使用fallback列表

## ⚙️ 配置选项

### 更改搜索标签

编辑环境变量：
```env
TIKTOK_HASHTAG=animecosplay
```

支持的标签示例：
- `cosplaydance`
- `animecosplay`
- `kpopdance`
- `genshinimpact`

### 获取 ms_token（可选，提高稳定性）

1. 打开 TikTok.com 并登录
2. 按 F12 打开开发者工具
3. 进入 Application → Cookies
4. 找到 `ms_token` 的值
5. 添加到环境变量：

```env
TIKTOK_MS_TOKEN=你的ms_token值
```

## 🔧 故障排查

### 问题：EmptyResponseException

**原因：** TikTok 检测到bot请求并拦截

**解决方案：**
1. 添加 `ms_token`（见上方）
2. 降低请求频率
3. 使用代理（高级）

### 问题：Playwright 安装失败

**解决：**
```bash
python -m playwright install chromium
```

### 问题：没有视频返回

**解决：**
1. 检查标签是否存在视频
2. 查看 bot 日志
3. 会自动使用 fallback 列表

## 📊 API 使用

### 手动搜索示例

```python
from tiktok_manager import TikTokManager

manager = TikTokManager(hashtag="cosplaydance")
await manager.fetch_videos(count=100)

# 获取视频
user_id = 123
video_url = manager.get_next_video(user_id)
print(video_url)  # https://vxtiktok.com/@user/video/123
```

### 队列状态

```python
status = manager.get_queue_status(user_id)
print(f"已播放: {status['current_position']}/{status['total_videos']}")
```

## 🔒 隐私与安全

- ✅ 仅搜索公开视频
- ✅ 不存储用户个人信息
- ✅ 遵守 TikTok 服务条款
- ✅ 不进行高频爬取

## 📈 性能优化

### Railway 部署

TikTok API 需要浏览器环境，在 Railway 上：

1. 添加 Playwright buildpack（自动完成）
2. 缓存视频列表（1小时）
3. 异步搜索，不阻塞命令响应

### 内存优化

- 缓存最多 50 个视频
- 每小时刷新一次
- 用户队列保存到 Redis

## 🌟 高级功能

### 多标签搜索（未来）

```env
TIKTOK_HASHTAGS=cosplaydance,animecosplay,kpop
```

### 自定义搜索条件

修改 `tiktok_manager.py` 中的 `fetch_videos()`：

```python
# 按用户搜索
user = api.user(username="cosplay_artist")
async for video in user.videos(count=30):
    ...

# 按声音搜索
sound = api.sound(id="1234567890")
async for video in sound.videos(count=30):
    ...
```

## 📝 依赖库

- **TikTokApi** >= 6.0.0 - TikTok 非官方 API
- **playwright** >= 1.40.0 - 浏览器自动化

## 🆘 支持

- 问题反馈：GitHub Issues
- 文档：[TikTokApi GitHub](https://github.com/davidteather/TikTok-Api)
