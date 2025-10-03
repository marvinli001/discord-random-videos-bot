# TikTok 功能设置指南

## 功能说明

`/randomtiktok` 命令允许用户获取随机的 TikTok 视频（Cosplay Dance 主题）

### 特点：
- ✅ 独立的随机队列（与 `/randomvideo` 分离）
- ✅ 已播放的视频不会重复，直到所有视频播放完
- ✅ 自动转换为 Discord 可内嵌格式（vxtiktok.com）
- ✅ "下一个"按钮快速切换
- ✅ Redis 持久化队列状态

## 配置步骤

### 1. 准备 TikTok 视频列表

创建一个 JSON 文件，包含 TikTok 视频链接数组：

```json
[
  "https://tiktok.com/@username/video/7123456789012345678",
  "https://tiktok.com/@cosplayer1/video/7234567890123456789",
  "https://tiktok.com/@dancer2/video/7345678901234567890"
]
```

### 2. 获取 TikTok 视频链接的方法

#### 方法 1: 手动收集（推荐）
1. 在 TikTok 搜索 "Cosplay dance"
2. 找到喜欢的视频，点击分享 → 复制链接
3. 将链接添加到 JSON 文件

#### 方法 2: 使用 TikTok Downloader 工具
```bash
# 安装 yt-dlp
pip install yt-dlp

# 获取视频信息（不下载）
yt-dlp --get-url "https://tiktok.com/..."
```

#### 方法 3: 使用 TikTok API（高级）
```python
# 使用 TikTokApi Python 库
from TikTokApi import TikTokApi

api = TikTokApi()
videos = api.by_hashtag("cosplaydance", count=30)
```

### 3. 托管 JSON 文件

将 JSON 文件上传到：
- **GitHub Gist** (推荐)
- **自己的服务器**
- **CDN 服务**

获取公开的 URL，例如：
```
https://gist.githubusercontent.com/你的用户名/xxx/raw/tiktok.json
```

### 4. 配置环境变量

在 `.env` 文件或 Railway 环境变量中添加：

```env
TIKTOK_JSON_URL=https://你的域名/tiktok.json
```

### 5. 部署

推送代码到 Railway，bot 会自动：
1. 读取 TikTok JSON 列表
2. 将链接转换为 vxtiktok.com 格式
3. 在 Discord 中内嵌播放

## 使用方法

### Discord 命令

```
/randomtiktok
```

或文本命令：
```
!randomtiktok
```

### 按钮操作

- **⏭️ 下一个**: 获取下一个随机 TikTok 视频

## 视频格式转换

Bot 会自动将 TikTok 链接转换为 Discord 可内嵌格式：

**输入格式：**
```
https://tiktok.com/@username/video/7123456789
```

**转换后：**
```
https://vxtiktok.com/@username/video/7123456789
```

这样 Discord 就能直接播放视频，无需跳转！

## 维护 TikTok 列表

### 添加新视频

1. 编辑你的 JSON 文件
2. 添加新的 TikTok 链接
3. 保存并更新

Bot 会在下次重启或刷新时自动加载新视频

### 删除视频

直接从 JSON 中删除不想要的链接即可

## 故障排查

### 问题：视频无法播放

**原因：** TikTok 链接格式不正确

**解决：**
- 确保链接格式为：`https://tiktok.com/@用户名/video/视频ID`
- Bot 会自动转换为 `vxtiktok.com`

### 问题：没有视频返回

**原因：** JSON 文件无法访问

**解决：**
1. 检查 `TIKTOK_JSON_URL` 是否正确
2. 确保 JSON 文件公开可访问
3. 查看 bot 日志

### 问题：队列重复播放

**原因：** Redis 未正确配置

**解决：**
- 确保 Railway Redis 已连接
- 查看 [RAILWAY_SETUP.md](RAILWAY_SETUP.md)

## 高级功能（未来）

### 自动抓取 TikTok 视频

可以使用 Python 脚本定期更新 JSON：

```python
# auto_update_tiktok.py
from TikTokApi import TikTokApi
import json

api = TikTokApi()
videos = []

# 搜索标签
for video in api.by_hashtag("cosplaydance", count=50):
    videos.append(video['video']['playAddr'])

# 保存到 JSON
with open('tiktok.json', 'w') as f:
    json.dump(videos, f)
```

### 多标签支持

修改配置支持多个标签：
```env
TIKTOK_TAGS=cosplaydance,animecosplay,kpopdance
```

## 示例 JSON

参考 [tiktok_example.json](tiktok_example.json)
