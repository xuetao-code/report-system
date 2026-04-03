from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
import logging
from pathlib import Path

from app.config import settings
from app.database import engine, Base
from app.api import reports, datasources, exports, shares
from app.services.scheduler import scheduler

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    Base.metadata.create_all(bind=engine)
    logger.info("数据库表已创建")
    scheduler.start()
    logger.info("定时任务调度器已启动")
    yield
    scheduler.shutdown()
    logger.info("应用已关闭")

# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="自定义报表系统 API",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(reports.router, prefix="/api/reports", tags=["报表管理"])
app.include_router(datasources.router, prefix="/api/datasources", tags=["数据源管理"])
app.include_router(exports.router, prefix="/api/exports", tags=["导出服务"])
# 报表分享路由（公开访问不需要 /api 前缀）
app.include_router(shares.router, prefix="/api", tags=["报表分享"])

# 单独注册公开访问路由（不需要 /api 前缀）
from app.api.shares import view_shared_report
app.add_api_route("/report/{share_token}", view_shared_report, methods=["GET"], response_class=HTMLResponse, include_in_schema=False)


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/docs-center", response_class=HTMLResponse)
async def docs_center():
    """文档中心页面"""
    docs_dir = Path(__file__).parent.parent / "docs"
    
    # 文档列表配置
    docs = [
        {
            "id": "user-manual",
            "title": "📖 用户手册",
            "description": "完整的使用指南，包含快速开始、数据源配置、报表设计等",
            "icon": "📘",
            "category": "使用指南",
            "file": "USER_MANUAL.md",
            "tags": ["新手必读", "使用教程"]
        },
        {
            "id": "dashboard-guide",
            "title": "📊 销售分析仪表板",
            "description": "复杂图表报表设计指南，包含折线图、柱状图、饼图等",
            "icon": "📈",
            "category": "示例文档",
            "file": "DASHBOARD_GUIDE.md",
            "tags": ["图表", "仪表板", "示例"]
        },
        {
            "id": "preview-feature",
            "title": "📊 预览功能说明",
            "description": "可视化预览弹窗功能详细介绍和使用说明",
            "icon": "👁️",
            "category": "功能文档",
            "file": "PREVIEW_FEATURE.md",
            "tags": ["新功能", "可视化"]
        },
        {
            "id": "sqlite-guide",
            "title": "💾 SQLite 测试数据库",
            "description": "测试数据库结构说明、示例报表和常用查询",
            "icon": "🗄️",
            "category": "数据指南",
            "file": "README.md",
            "tags": ["测试数据", "SQLite"]
        },
        {
            "id": "sqlite-datasource",
            "title": "🔌 SQLite 数据源配置",
            "description": "SQLite 数据源详细配置指南和高级用法",
            "icon": "🔧",
            "category": "配置指南",
            "file": "SQLITE_DATA_SOURCE.md",
            "tags": ["数据源", "配置"]
        },
        {
            "id": "tech-design",
            "title": "🏗️ 技术设计方案",
            "description": "完整的技术架构设计、模块说明和实现方案",
            "icon": "🏛️",
            "category": "技术文档",
            "file": "../自定义报表系统方案-MVP.md",
            "tags": ["架构设计", "技术方案"]
        },
        {
            "id": "competitive-analysis",
            "title": "📊 BI 竞品调研报告",
            "description": "主流 BI 报表工具功能对比分析，包含 68 项功能点详细对比和我们的实现情况",
            "icon": "🔬",
            "category": "调研报告",
            "file": "COMPETITIVE_ANALYSIS.md",
            "tags": ["竞品分析", "功能对比", "产品规划"]
        },
        {
            "id": "api-docs",
            "title": "🔌 API 接口文档",
            "description": "Swagger UI 交互式 API 文档",
            "icon": "🌐",
            "category": "开发文档",
            "file": "/docs",
            "tags": ["API", "开发"],
            "external": True
        }
    ]
    
    categories = list(set(doc["category"] for doc in docs))
    
    # 生成分类过滤按钮
    filter_buttons = '<button class="filter-btn active" onclick="filterCategory(\'all\')">全部</button>'
    for cat in categories:
        filter_buttons += f'<button class="filter-btn" onclick="filterCategory(\'{cat}\')">{cat}</button>'
    
    # 生成文档卡片
    doc_cards = ''
    for doc in docs:
        tags_html = ''.join([f'<span class="doc-tag">{tag}</span>' for tag in doc.get('tags', [])])
        link = doc['file'] if doc.get('external') else f"/docs-view/{doc['id']}"
        
        doc_cards += f'''
        <div class="doc-card" data-category="{doc['category']}" onclick="window.location.href='{link}'">
            <div class="doc-card-header">
                <div class="doc-icon">{doc['icon']}</div>
                <div>
                    <div class="doc-title">{doc['title']}</div>
                    <span class="doc-category">{doc['category']}</span>
                </div>
            </div>
            <div class="doc-description">{doc['description']}</div>
            <div class="doc-tags">{tags_html}</div>
        </div>
        '''
    
    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>文档中心 - 自定义报表系统</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/element-plus@2.5.0/dist/index.css">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .navbar {{
            background: rgba(255, 255, 255, 0.95);
            padding: 15px 30px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.1);
            position: sticky;
            top: 0;
            z-index: 100;
        }}
        .navbar-content {{
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .navbar h1 {{
            font-size: 24px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        .navbar-links {{
            display: flex;
            gap: 20px;
        }}
        .navbar-links a {{
            color: #606266;
            text-decoration: none;
            padding: 8px 16px;
            border-radius: 4px;
            transition: all 0.3s;
        }}
        .navbar-links a:hover {{
            background: #f5f7fa;
            color: #409EFF;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 40px 20px;
        }}
        .hero {{
            text-align: center;
            color: white;
            padding: 60px 20px;
        }}
        .hero h2 {{
            font-size: 48px;
            margin-bottom: 15px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}
        .hero p {{
            font-size: 18px;
            opacity: 0.95;
        }}
        .search-box {{
            max-width: 600px;
            margin: 30px auto;
        }}
        .search-box input {{
            width: 100%;
            padding: 15px 25px;
            border: none;
            border-radius: 50px;
            font-size: 16px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            outline: none;
        }}
        .docs-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 25px;
            margin-top: 40px;
        }}
        .doc-card {{
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            transition: all 0.3s;
            cursor: pointer;
            border: 2px solid transparent;
        }}
        .doc-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 24px rgba(0,0,0,0.15);
            border-color: #667eea;
        }}
        .doc-card-header {{
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 15px;
        }}
        .doc-icon {{
            font-size: 36px;
            width: 60px;
            height: 60px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 12px;
        }}
        .doc-title {{
            font-size: 20px;
            font-weight: 600;
            color: #303133;
            margin-bottom: 5px;
        }}
        .doc-category {{
            display: inline-block;
            padding: 4px 12px;
            background: #f0f2f5;
            border-radius: 20px;
            font-size: 12px;
            color: #606266;
        }}
        .doc-description {{
            color: #606266;
            margin-bottom: 15px;
            line-height: 1.8;
        }}
        .doc-tags {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }}
        .doc-tag {{
            padding: 4px 10px;
            background: #ecf5ff;
            color: #409EFF;
            border-radius: 4px;
            font-size: 12px;
        }}
        .category-filter {{
            display: flex;
            gap: 10px;
            margin: 30px 0;
            flex-wrap: wrap;
            justify-content: center;
        }}
        .filter-btn {{
            padding: 10px 20px;
            border: 2px solid #e6e6e6;
            background: white;
            border-radius: 25px;
            cursor: pointer;
            transition: all 0.3s;
            font-size: 14px;
        }}
        .filter-btn:hover, .filter-btn.active {{
            border-color: #667eea;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        .stats {{
            display: flex;
            justify-content: center;
            gap: 40px;
            margin: 40px 0;
            color: white;
        }}
        .stat-item {{
            text-align: center;
        }}
        .stat-number {{
            font-size: 36px;
            font-weight: bold;
            display: block;
        }}
        .stat-label {{
            font-size: 14px;
            opacity: 0.9;
        }}
        .footer {{
            text-align: center;
            color: white;
            padding: 30px;
            opacity: 0.9;
        }}
    </style>
</head>
<body>
    <div class="navbar">
        <div class="navbar-content">
            <h1>📚 文档中心</h1>
            <div class="navbar-links">
                <a href="/">🏠 首页</a>
                <a href="/manual">📖 用户手册</a>
                <a href="/docs">🔌 API 文档</a>
                <a href="http://0.0.0.0:3000" target="_blank">🎨 前端界面</a>
            </div>
        </div>
    </div>
    
    <div class="hero">
        <h2>欢迎使用文档中心</h2>
        <p>快速查找和学习自定义报表系统的所有文档</p>
        
        <div class="search-box">
            <input type="text" id="searchInput" placeholder="🔍 搜索文档..." onkeyup="filterDocs()">
        </div>
    </div>
    
    <div class="container">
        <div class="stats">
            <div class="stat-item">
                <span class="stat-number">{len(docs)}</span>
                <span class="stat-label">篇文档</span>
            </div>
            <div class="stat-item">
                <span class="stat-number">{len(categories)}</span>
                <span class="stat-label">个分类</span>
            </div>
            <div class="stat-item">
                <span class="stat-number">100%</span>
                <span class="stat-label">覆盖率</span>
            </div>
        </div>
        
        <div class="category-filter">
            {filter_buttons}
        </div>
        
        <div class="docs-grid">
            {doc_cards}
        </div>
    </div>
    
    <div class="footer">
        <p>自定义报表系统 v1.0.0 | 文档中心 | 2026-04-02</p>
    </div>
    
    <script>
        function filterDocs() {{
            const input = document.getElementById('searchInput').value.toLowerCase();
            const cards = document.querySelectorAll('.doc-card');
            cards.forEach(card => {{
                const text = card.innerText.toLowerCase();
                card.style.display = text.includes(input) ? 'block' : 'none';
            }});
        }}
        
        function filterCategory(category) {{
            const cards = document.querySelectorAll('.doc-card');
            const buttons = document.querySelectorAll('.filter-btn');
            
            buttons.forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            
            cards.forEach(card => {{
                const cat = card.dataset.category;
                if (category === 'all' || cat === category) {{
                    card.style.display = 'block';
                }} else {{
                    card.style.display = 'none';
                }}
            }});
        }}
    </script>
</body>
</html>"""
    
    return html_content


@app.get("/docs-view/{doc_id}")
async def view_doc(doc_id: str, response_class=HTMLResponse):
    """查看文档详情"""
    docs_config = {
        "user-manual": {"title": "📖 用户手册", "file": "USER_MANUAL.md", "dir": "docs"},
        "dashboard-guide": {"title": "📊 销售分析仪表板", "file": "DASHBOARD_GUIDE.md", "dir": "data"},
        "preview-feature": {"title": "📊 预览功能说明", "file": "PREVIEW_FEATURE.md", "dir": "docs"},
        "sqlite-guide": {"title": "💾 SQLite 测试数据库", "file": "README.md", "dir": "data"},
        "sqlite-datasource": {"title": "🔌 SQLite 数据源配置", "file": "SQLITE_DATA_SOURCE.md", "dir": "docs"},
        "tech-design": {"title": "🏗️ 技术设计方案", "file": "自定义报表系统方案-MVP.md", "dir": "workspace"},
        "competitive-analysis": {"title": "📊 BI 竞品调研报告", "file": "COMPETITIVE_ANALYSIS.md", "dir": "docs"}
    }
    
    if doc_id not in docs_config:
        return HTMLResponse("<h1>文档不存在</h1>", status_code=404)
    
    doc_info = docs_config[doc_id]
    project_root = Path(__file__).parent.parent.parent
    
    # 根据目录配置构建路径
    if doc_info["dir"] == "docs":
        doc_path = project_root / "docs" / doc_info["file"]
    elif doc_info["dir"] == "data":
        doc_path = project_root / "data" / doc_info["file"]
    elif doc_info["dir"] == "workspace":
        # workspace 在 project_root 的父目录
        doc_path = project_root.parent / doc_info["file"]
    else:  # root
        doc_path = project_root / doc_info["file"]
    
    try:
        with open(doc_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        html_content = markdown_to_html(content, doc_info["title"])
        return HTMLResponse(html_content)
    except Exception as e:
        return HTMLResponse(f"<h1>文档加载失败</h1><p>{str(e)}</p>", status_code=500)


def markdown_to_html(md_content: str, title: str) -> str:
    """使用 markdown 库渲染 Markdown 为 HTML，支持目录锚点跳转"""
    import markdown
    import re
    
    # 提取目录项（用于生成侧边栏 TOC）
    toc_items = []
    
    # 使用 Python markdown 库渲染
    html_body = markdown.markdown(
        md_content,
        extensions=[
            'fenced_code',      # 支持 ``` 代码块
            'codehilite',       # 代码高亮
            'tables',           # 表格支持
            'toc',              # 目录支持（但我们自己实现）
            'nl2br',            # 换行转 <br>
        ],
        extension_configs={
            'codehilite': {
                'linenums': False,
                'guess_lang': False,
            }
        }
    )
    
    # 为标题添加锚点 ID 并收集目录项（替换 markdown 库生成的 id）
    def add_heading_anchor(match):
        tag = match.group(1)  # h1, h2, h3, etc.
        text = match.group(2)
        # 生成有意义的锚点 ID（中文保留）
        anchor_id = re.sub(r'[^\w\u4e00-\u9fa5]', '', text)
        if not anchor_id:
            anchor_id = f'heading-{len(toc_items)}'
        level = int(tag[1])
        toc_items.append({'level': level, 'text': text, 'id': anchor_id})
        return f'<{tag} id="{anchor_id}">'
    
    # 匹配带或不带 id 的标题
    html_body = re.sub(r'<(h[1-6])(?:\s+id="[^"]*")?>(.*?)</\1>', add_heading_anchor, html_body)
    
    # 为内部锚点链接添加平滑滚动
    def fix_internal_links(match):
        href = match.group(1)
        text = match.group(2)
        if href.startswith('#'):
            anchor = href[1:]
            return f'<a href="{href}" onclick="scrollToSection(\'{anchor}\'); return false;">{text}</a>'
        return f'<a href="{href}" target="_blank">{text}</a>'
    
    html_body = re.sub(r'<a href="([^"]+)">(.*?)</a>', fix_internal_links, html_body)
    
    # 生成目录 HTML
    toc_html = ''
    if toc_items:
        toc_items_html = ''
        for item in toc_items:
            indent = (item['level'] - 1) * 15
            toc_items_html += f'<li style="margin-left: {indent}px;"><a href="#{item["id"]}" onclick="scrollToSection(\'{item["id"]}\'); return false;">{item["text"]}</a></li>'
        toc_html = f'''
        <div class="toc-sidebar">
            <div class="toc-title">📑 目录</div>
            <ul class="toc-list">{toc_items_html}</ul>
        </div>
        '''
    
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - 自定义报表系统</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/element-plus@2.5.0/dist/index.css">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            line-height: 1.8;
            color: #333;
            background: #f5f7fa;
            padding: 20px;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            display: flex;
            gap: 30px;
        }}
        .navbar {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 30px;
            margin: -40px -40px 30px;
            border-radius: 12px 12px 0 0;
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: 0 2px 12px rgba(0,0,0,0.1);
        }}
        .navbar a {{
            color: white;
            text-decoration: none;
            margin-right: 20px;
        }}
        .toc-sidebar {{
            width: 250px;
            flex-shrink: 0;
            position: sticky;
            top: 20px;
            align-self: flex-start;
            max-height: calc(100vh - 140px);
            overflow-y: auto;
        }}
        .toc-title {{
            font-size: 16px;
            font-weight: 600;
            color: #303133;
            padding: 15px 0;
            border-bottom: 2px solid #e6e8eb;
            margin-bottom: 10px;
        }}
        .toc-list {{
            list-style: none;
            padding: 0;
        }}
        .toc-list li {{
            margin: 8px 0;
        }}
        .toc-list a {{
            color: #606266;
            text-decoration: none;
            font-size: 14px;
            line-height: 1.6;
            display: block;
            padding: 6px 10px;
            border-radius: 4px;
            transition: all 0.2s;
        }}
        .toc-list a:hover {{
            background: #f5f7fa;
            color: #409EFF;
            text-decoration: none;
        }}
        .toc-list a.active {{
            background: #ecf5ff;
            color: #409EFF;
            font-weight: 500;
        }}
        .doc-content {{
            flex: 1;
            min-width: 0;
            scroll-margin-top: 20px;
        }}
        h1 {{
            color: #409EFF;
            border-bottom: 3px solid #409EFF;
            padding-bottom: 15px;
            margin-bottom: 30px;
            scroll-margin-top: 20px;
        }}
        h2 {{
            color: #303133;
            margin: 35px 0 20px;
            border-left: 4px solid #667eea;
            padding-left: 15px;
            scroll-margin-top: 20px;
        }}
        h3 {{
            color: #606266;
            margin: 25px 0 15px;
            scroll-margin-top: 20px;
        }}
        p {{ margin: 15px 0; }}
        ul, ol {{
            margin: 15px 0;
            padding-left: 40px;
        }}
        li {{
            margin: 8px 0;
            line-height: 1.8;
        }}
        li > ol, li > ul {{
            margin-top: 5px;
            margin-bottom: 5px;
        }}
        a {{
            color: #409EFF;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        code {{
            background: #f4f4f5;
            padding: 3px 8px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            color: #e83e8c;
        }}
        pre {{
            background: #282c34;
            color: #abb2bf;
            padding: 20px;
            border-radius: 6px;
            overflow-x: auto;
            margin: 20px 0;
        }}
        pre code {{ background: none; color: inherit; padding: 0; }}
        /* CodeHilite 语法高亮样式 */
        .codehilite {{ background: #282c34; color: #abb2bf; padding: 20px; border-radius: 6px; overflow-x: auto; margin: 20px 0; }}
        .codehilite pre {{ background: none; padding: 0; margin: 0; }}
        .codehilite .k {{ color: #c678dd; }} /* keyword */
        .codehilite .kc {{ color: #c678dd; }} /* keyword.constant */
        .codehilite .kd {{ color: #c678dd; }} /* keyword.declaration */
        .codehilite .kn {{ color: #c678dd; }} /* keyword.namespace */
        .codehilite .kp {{ color: #c678dd; }} /* keyword.pseudo */
        .codehilite .kr {{ color: #c678dd; }} /* keyword.reserved */
        .codehilite .kt {{ color: #e5c07b; }} /* keyword.type */
        .codehilite .n {{ color: #abb2bf; }} /* name */
        .codehilite .na {{ color: #d19a66; }} /* name.attribute */
        .codehilite .nb {{ color: #e5c07b; }} /* name.builtin */
        .codehilite .bp {{ color: #e5c07b; }} /* name.builtin.pseudo */
        .codehilite .nc {{ color: #e5c07b; }} /* name.class */
        .codehilite .no {{ color: #d19a66; }} /* name.constant */
        .codehilite .nd {{ color: #61afef; }} /* name.decorator */
        .codehilite .ni {{ color: #abb2bf; }} /* name.entity */
        .codehilite .ne {{ color: #e5c07b; }} /* name.exception */
        .codehilite .nf {{ color: #61afef; }} /* name.function */
        .codehilite .fm {{ color: #61afef; }} /* name.function.magic */
        .codehilite .nl {{ color: #e5c07b; }} /* name.label */
        .codehilite .nn {{ color: #e5c07b; }} /* name.namespace */
        .codehilite .nx {{ color: #abb2bf; }} /* name.other */
        .codehilite .py {{ color: #abb2bf; }} /* name.property */
        .codehilite .nt {{ color: #e06c75; }} /* name.tag */
        .codehilite .nv {{ color: #e06c75; }} /* name.variable */
        .codehilite .vc {{ color: #e06c75; }} /* name.variable.class */
        .codehilite .vg {{ color: #e06c75; }} /* name.variable.global */
        .codehilite .vi {{ color: #e06c75; }} /* name.variable.instance */
        .codehilite .vm {{ color: #e06c75; }} /* name.variable.magic */
        .codehilite .l {{ color: #d19a66; }} /* literal */
        .codehilite .ld {{ color: #98c379; }} /* literal.date */
        .codehilite .s {{ color: #98c379; }} /* string */
        .codehilite .sa {{ color: #98c379; }} /* string.affix */
        .codehilite .sb {{ color: #98c379; }} /* string.backtick */
        .codehilite .sc {{ color: #98c379; }} /* string.char */
        .codehilite .dl {{ color: #98c379; }} /* string.delimiter */
        .codehilite .sd {{ color: #98c379; }} /* string.doc */
        .codehilite .s2 {{ color: #98c379; }} /* string.double */
        .codehilite .se {{ color: #d19a66; }} /* string.escape */
        .codehilite .sh {{ color: #98c379; }} /* string.heredoc */
        .codehilite .si {{ color: #98c379; }} /* string.interpol */
        .codehilite .sx {{ color: #98c379; }} /* string.other */
        .codehilite .sr {{ color: #98c379; }} /* string.regex */
        .codehilite .s1 {{ color: #98c379; }} /* string.single */
        .codehilite .ss {{ color: #98c379; }} /* string.symbol */
        .codehilite .m {{ color: #d19a66; }} /* number */
        .codehilite .mb {{ color: #d19a66; }} /* number.bin */
        .codehilite .mf {{ color: #d19a66; }} /* number.float */
        .codehilite .mh {{ color: #d19a66; }} /* number.hex */
        .codehilite .mi {{ color: #d19a66; }} /* number.integer */
        .codehilite .il {{ color: #d19a66; }} /* number.integer.long */
        .codehilite .mo {{ color: #d19a66; }} /* number.oct */
        .codehilite .o {{ color: #56b6c2; }} /* operator */
        .codehilite .ow {{ color: #c678dd; }} /* operator.word */
        .codehilite .p {{ color: #abb2bf; }} /* punctuation */
        .codehilite .c {{ color: #5c6370; font-style: italic; }} /* comment */
        .codehilite .ch {{ color: #5c6370; font-style: italic; }} /* comment.hashbang */
        .codehilite .cm {{ color: #5c6370; font-style: italic; }} /* comment.multiline */
        .codehilite .c1 {{ color: #5c6370; font-style: italic; }} /* comment.single */
        .codehilite .cs {{ color: #5c6370; font-style: italic; }} /* comment.special */
        .codehilite .cp {{ color: #5c6370; font-style: italic; }} /* comment.preproc */
        .codehilite .cpf {{ color: #5c6370; font-style: italic; }} /* comment.preprocfile */
        .codehilite .gd {{ color: #e06c75; }} /* generic.deleted */
        .codehilite .ge {{ color: #abb2bf; font-style: italic; }} /* generic.emph */
        .codehilite .gr {{ color: #e06c75; }} /* generic.error */
        .codehilite .gh {{ color: #e5c07b; font-weight: bold; }} /* generic.heading */
        .codehilite .gi {{ color: #98c379; }} /* generic.inserted */
        .codehilite .go {{ color: #5c6370; }} /* generic.output */
        .codehilite .gp {{ color: #5c6370; }} /* generic.prompt */
        .codehilite .gs {{ color: #abb2bf; font-weight: bold; }} /* generic.strong */
        .codehilite .gu {{ color: #56b6c2; }} /* generic.subheading */
        .codehilite .gt {{ color: #e06c75; }} /* generic.traceback */
        .codehilite .w {{ color: #abb2bf; }} /* whitespace */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #dcdfe6;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background: #f5f7fa;
            color: #606266;
            font-weight: 600;
        }}
        tr:nth-child(even) {{ background: #fafafa; }}
        .back-link {{
            display: inline-block;
            margin-bottom: 20px;
            color: #409EFF;
            text-decoration: none;
        }}
        .back-link:hover {{ text-decoration: underline; }}
        @media (max-width: 900px) {{
            .container {{
                flex-direction: column;
            }}
            .toc-sidebar {{
                width: 100%;
                position: static;
                max-height: none;
                border-bottom: 2px solid #e6e8eb;
                padding-bottom: 15px;
            }}
        }}
        .navbar-full {{
            width: 100%;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 1000;
            margin: 0;
            border-radius: 0;
        }}
        .doc-page-wrapper {{
            margin-top: 60px;
        }}
    </style>
</head>
<body>
    <div class="navbar navbar-full">
        <div class="navbar-content" style="max-width: 1400px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center;">
            <div>
                <a href="/docs-center" style="color: white; text-decoration: none; margin-right: 20px;">📚 返回文档中心</a>
                <a href="/" style="color: white; text-decoration: none; margin-right: 20px;">🏠 首页</a>
                <a href="/manual" style="color: white; text-decoration: none;">📖 用户手册</a>
            </div>
        </div>
    </div>
    <div class="doc-page-wrapper">
        <div class="container">
            {toc_html}
            <div class="doc-content">
                <a href="/docs-center" class="back-link">← 返回文档中心</a>
                <div class="doc-content-inner">
                    <h1>{title}</h1>
                    {html_body}
                </div>
            </div>
        </div>
    </div>
    <script>
        function scrollToSection(id) {{
            const element = document.getElementById(id);
            if (element) {{
                const offset = 100;
                const elementPosition = element.getBoundingClientRect().top;
                const offsetPosition = elementPosition + window.pageYOffset - offset;
                window.scrollTo({{
                    top: offsetPosition,
                    behavior: 'smooth'
                }});
                // 更新 URL hash 但不触发滚动
                history.pushState(null, null, '#' + id);
                // 高亮当前目录项
                document.querySelectorAll('.toc-list a').forEach(a => a.classList.remove('active'));
                const activeLink = document.querySelector('.toc-list a[href="#' + id + '"]');
                if (activeLink) activeLink.classList.add('active');
            }}
        }}
        // 页面加载时检查 hash 并滚动
        window.addEventListener('DOMContentLoaded', () => {{
            const hash = window.location.hash.substring(1);
            if (hash) {{
                setTimeout(() => scrollToSection(hash), 100);
            }}
            // 监听滚动，高亮对应目录
            let ticking = false;
            window.addEventListener('scroll', () => {{
                if (!ticking) {{
                    window.requestAnimationFrame(() => {{
                        const headings = document.querySelectorAll('h1[id], h2[id], h3[id]');
                        let currentId = '';
                        headings.forEach(h => {{
                            const rect = h.getBoundingClientRect();
                            if (rect.top <= 120 && rect.bottom >= 120) {{
                                currentId = h.id;
                            }}
                        }});
                        if (currentId) {{
                            document.querySelectorAll('.toc-list a').forEach(a => a.classList.remove('active'));
                            const activeLink = document.querySelector('.toc-list a[href="#' + currentId + '"]');
                            if (activeLink) activeLink.classList.add('active');
                        }}
                        ticking = false;
                    }});
                    ticking = true;
                }}
            }});
        }});
    </script>
</body>
</html>"""


@app.get("/manual")
async def user_manual():
    """重定向到文档查看器"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs-view/user-manual")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)
