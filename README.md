# Sync Bangumi to Notion

将您的 Bangumi 动漫收藏数据同步到 Notion 数据库的工具。通过简单的配置，您可以轻松地将 Bangumi 上的动漫、书籍、游戏等收藏数据自动同步到 Notion 数据库中，实现数据的统一管理和可视化。

## 功能特点

- 自动从 Bangumi 获取您的动漫、书籍、游戏等收藏列表
- 将收藏数据同步到 Notion 数据库，包括标题、评分、标签等详细信息
- 支持多种收藏类型：想看、看过、在看、搁置、抛弃
- 自动同步封面图片和详细信息
- 支持增量同步，避免重复数据
- 本地缓存支持，提高同步效率
- 自动处理已删除的收藏条目
- 保持 Bangumi 和 Notion 数据的一致性

## 安装

### 前提条件

- Python 3.10 或更高版本
- Notion API 密钥
- Bangumi OAuth 认证令牌
- Notion 集成页面权限

### 获取必要的 API 密钥

#### Notion API 配置
1. 访问 [Notion Developers](https://developers.notion.com/) 创建一个新的集成
2. 复制生成的 API 密钥（`NOTION_API_KEY`）
3. 在您的 Notion 页面中，点击右上角的 "Share" 按钮
4. 在弹出的菜单中选择您刚刚创建的集成，授予「可以编辑」权限
5. 复制页面 URL 中的 ID 部分作为 `NOTION_PAGE_ID`

#### Bangumi API 配置
1. 访问 [Bangumi API](https://bgm.tv/dev/app) 创建新的应用
2. 获取 OAuth 认证令牌（`BGM_TOKEN`）
3. 记录您的 Bangumi 用户名（`BGM_USERNAME`）

### 安装步骤

1. 克隆仓库
```bash
git clone https://github.com/yourusername/Sync-Bangumi-to-Notion.git
cd Sync-Bangumi-to-Notion
```

2. 创建并激活虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate  # Windows
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 配置环境变量

创建 `.env` 文件并添加以下内容：
```ini
NOTION_TOKEN=your_notion_api_key
NOTION_PAGE_ID=your_notion_page_id
NOTION_DATABASE_ID=your_notion_database_id  # 首次运行时会自动创建并输出到控制台
BGM_TOKEN=your_bgm_token
```

## 使用方法

1. 确保已正确配置所有环境变量
2. 运行同步脚本
```bash
python bgm_to_notion.py
```

首次运行时，脚本会：
- 在指定的 Notion 页面创建新的数据库
- 输出数据库 ID，请将其添加到 `.env` 文件的 `NOTION_DATABASE_ID` 中
- 开始同步您的 Bangumi 收藏数据

后续运行时，脚本会：
- 自动检测新增、更新和删除的收藏条目
- 增量同步数据，避免重复操作
- 保持本地缓存以提高同步效率

## 数据同步说明

同步到 Notion 的数据包括：
- 作品标题（原名和中文名）
- 作品类型（动画、书籍、游戏等）
- 收藏状态（想看、看过、在看等）
- 评分信息（评分、评分人数、排名）
- 发行日期
- 作品标签
- 封面图片
- Bangumi 链接

## 常见问题

1. **同步失败或报错**
   - 检查网络连接
   - 确认 API 密钥是否正确
   - 验证 Notion 页面权限设置

2. **数据未完全同步**
   - 由于 API 限制，大量数据同步可能需要多次运行
   - 检查本地缓存文件是否正常

3. **Notion 数据库访问权限问题**
   - 确保已将集成添加到数据库的访问权限中
   - 检查 Notion API 密钥是否具有足够权限

## 贡献指南

欢迎通过以下方式贡献：
- 提交 Pull Request
- 创建 Issue 报告问题或提出建议
- 完善文档和使用说明

## 许可证

本项目采用 [MIT License](LICENSE) 许可证。
