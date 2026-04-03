# SQLite 数据源配置示例

## 快速开始

### 1. 创建内存数据库（测试用）

```json
{
  "name": "测试 SQLite 内存库",
  "type": "sqlite",
  "file_path": ":memory:"
}
```

### 2. 创建文件数据库（持久化）

```json
{
  "name": "本地 SQLite 数据库",
  "type": "sqlite",
  "file_path": "/data/mydb.db"
}
```

### 3. 使用相对路径

```json
{
  "name": "项目数据库",
  "type": "sqlite",
  "file_path": "./data/app.db"
}
```

---

## 报表 DSL 示例

```json
{
  "dataSource": {
    "type": "sqlite",
    "file_path": "/data/sales.db",
    "query": "SELECT * FROM orders WHERE date >= '${start_date}'"
  },
  "parameters": [
    {
      "name": "start_date",
      "type": "date",
      "default": "2026-01-01"
    }
  ],
  "components": [
    {
      "type": "table",
      "columns": [
        {"field": "order_id", "label": "订单号"},
        {"field": "customer", "label": "客户"},
        {"field": "amount", "label": "金额", "format": "currency"},
        {"field": "date", "label": "日期"}
      ]
    }
  ]
}
```

---

## SQLite 特性支持

### ✅ 支持的功能
- 本地文件数据库
- 内存数据库（`:memory:`）
- 只读模式访问
- WAL 日志模式
- 自定义 PRAGMA 设置

### ⚠️ 注意事项
1. **并发写入**：SQLite 不支持高并发写入
2. **网络访问**：不支持远程连接（仅限本地文件）
3. **文件大小**：建议单文件 < 10GB
4. **路径权限**：确保应用有文件读写权限

---

## 高级配置（可选）

```json
{
  "name": "高性能 SQLite",
  "type": "sqlite",
  "file_path": "/data/fast.db",
  "extra_config": {
    "journal_mode": "WAL",
    "synchronous": "NORMAL",
    "cache_size": 10000,
    "temp_store": "MEMORY"
  }
}
```

---

## 使用场景

| 场景 | 推荐配置 |
|------|----------|
| **开发测试** | `:memory:` 内存数据库 |
| **小型应用** | 本地 `.db` 文件 |
| **数据分析** | WAL 模式 + 大缓存 |
| **只读报表** | 只读模式打开现有数据库 |

---

## 常见问题

### Q: 如何创建 SQLite 数据库文件？
A: 无需预先创建，首次连接时会自动创建。也可以用以下命令：
```bash
sqlite3 /data/mydb.db "SELECT 1"
```

### Q: 如何导入现有 SQLite 数据库？
A: 将 `.db` 文件放到服务器，然后在数据源配置中指定路径。

### Q: 支持加密吗？
A: 原生 SQLite 不支持，可使用 SQLCipher 扩展（需额外安装）。
