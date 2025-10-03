# Railway 部署指南

## 步骤 1: 创建 Redis 服务

1. 在 Railway 项目中，点击 **"+ New"**
2. 选择 **"Database"** → **"Add Redis"**
3. Redis 服务会自动创建并生成环境变量

## 步骤 2: 关联 Redis 到 Worker 服务

**重要：** 必须将 Redis 的环境变量共享给 worker 服务

### 方法 1: 使用 Variable References（推荐）

1. 进入你的 **worker** 服务设置
2. 点击 **"Variables"** 标签
3. 点击 **"+ New Variable"** → **"Add Reference"**
4. 选择 Redis 服务的以下变量：
   - `REDIS_PRIVATE_URL` （推荐，使用内网连接更快）
   - 或 `REDIS_PUBLIC_URL`
   - 或 `REDIS_URL`

### 方法 2: 在同一个项目中（自动共享）

如果 Redis 和 worker 在同一个 Railway 项目中：
- Railway 会自动注入 Redis 的环境变量
- 变量名格式：`REDIS_PRIVATE_URL`, `REDIS_PUBLIC_URL` 等

## 步骤 3: 验证连接

部署后，检查日志应该看到：

```
✅ Redis connected successfully
```

如果看到以下信息说明 Redis 未正确配置：

```
⚠️  Redis not available: ... Running without persistence.
```

## 步骤 4: 重新部署

修改配置后，重新部署 worker 服务：
1. 点击 **"Deploy"** 按钮
2. 或者推送新的代码到 GitHub 触发自动部署

## 排查问题

### 问题：无法连接 Redis

**检查清单：**

1. ✅ Redis 服务是否正在运行？
   - 进入 Redis 服务，查看状态是否为 "Active"

2. ✅ 环境变量是否已共享？
   - 进入 worker 服务 → Variables
   - 检查是否有 `REDIS_PRIVATE_URL` 或类似变量

3. ✅ 变量名是否正确？
   - 代码会自动检测：`REDIS_PRIVATE_URL`, `REDIS_URL`, `REDIS_PUBLIC_URL`
   - 查看日志中的连接信息

### 问题：数据丢失

- Redis 数据保存 30 天
- 如果 Redis 服务重启，内存数据会丢失（除非配置了持久化）
- Railway Redis 默认已启用持久化

## 本地开发

如果在本地测试 Redis：

```bash
# 使用 Docker 运行 Redis
docker run -d -p 6379:6379 redis:latest

# 设置环境变量
export REDISHOST=localhost
export REDISPORT=6379
```

或在 `.env` 文件中：

```env
REDISHOST=localhost
REDISPORT=6379
```

## 功能说明

### Redis 存储的数据

- **用户队列状态**：每个用户的播放队列和当前位置
- **过期时间**：30 天自动清理
- **键格式**：`user_queue:{user_id}`

### 自动刷新

- 每 10 分钟自动刷新视频列表
- 新视频自动加入用户当前轮次
- 删除的视频自动从队列移除
- 用户播放进度保留

## 测试

运行测试脚本验证 Redis 连接：

```bash
python test_redis.py
```

预期输出：
```
✅ Redis connected successfully!
✅ Save successful
✅ Load successful
✅ All tests passed!
```
