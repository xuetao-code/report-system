from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from typing import Optional
import json
import secrets
import time
from datetime import datetime, timedelta
from urllib.parse import quote

from app.database import get_db
from app.models.report import Report
from app.schemas.report import ReportShareCreate, ReportShareResponse
from sqlalchemy.orm import Session

router = APIRouter()


def generate_share_token() -> str:
    """生成安全的分享令牌"""
    return secrets.token_urlsafe(32)


@router.post("/reports/{report_id}/share", response_model=ReportShareResponse)
async def create_share(
    report_id: str,
    share_data: ReportShareCreate,
    db: Session = Depends(get_db)
):
    """创建报表分享链接"""
    # 检查报表是否存在
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报表不存在")
    
    # 生成分享令牌
    share_token = generate_share_token()
    share_id = f"sh_{secrets.token_hex(8)}"
    
    # 计算过期时间
    expires_at = None
    if share_data.expires_days:
        expires_at = datetime.now() + timedelta(days=share_data.expires_days)
    
    # 创建分享记录
    from app.models.report import ReportShare
    share = ReportShare(
        id=share_id,
        report_id=report_id,
        share_token=share_token,
        access_level=share_data.access_level,
        expires_at=expires_at,
        max_views=share_data.max_views,
        allow_download=share_data.allow_download,
        allow_refresh=share_data.allow_refresh,
        refresh_interval=share_data.refresh_interval,
        theme=share_data.theme,
        show_header=share_data.show_header,
        show_footer=share_data.show_footer
    )
    
    db.add(share)
    db.commit()
    db.refresh(share)
    
    # 生成访问链接
    share_url = f"/report/{share_token}"
    embed_url = f"/report/{share_token}?embed=true"
    
    return {
        "share_id": share.id,
        "share_token": share.share_token,
        "share_url": share_url,
        "embed_url": embed_url,
        "expires_at": share.expires_at,
        "access_level": share.access_level
    }


@router.get("/shares/{share_id}")
async def get_share(share_id: str, db: Session = Depends(get_db)):
    """获取分享配置"""
    from app.models.report import ReportShare
    share = db.query(ReportShare).filter(ReportShare.id == share_id).first()
    if not share:
        raise HTTPException(status_code=404, detail="分享配置不存在")
    
    return {
        "share_id": share.id,
        "report_id": share.report_id,
        "access_level": share.access_level,
        "expires_at": share.expires_at,
        "view_count": share.view_count,
        "max_views": share.max_views,
        "allow_download": share.allow_download,
        "refresh_interval": share.refresh_interval
    }


@router.get("/reports/{report_id}/shares")
async def list_report_shares(report_id: str, db: Session = Depends(get_db)):
    """获取报表的所有分享链接"""
    from app.models.report import ReportShare
    shares = db.query(ReportShare).filter(ReportShare.report_id == report_id).all()
    return [
        {
            "id": share.id,
            "report_id": share.report_id,
            "share_token": share.share_token,
            "access_level": share.access_level,
            "expires_at": share.expires_at,
            "view_count": share.view_count,
            "max_views": share.max_views,
            "created_at": share.created_at
        }
        for share in shares
    ]


@router.delete("/shares/{share_id}")
async def delete_share(share_id: str, db: Session = Depends(get_db)):
    """删除分享链接"""
    from app.models.report import ReportShare
    share = db.query(ReportShare).filter(ReportShare.id == share_id).first()
    if not share:
        raise HTTPException(status_code=404, detail="分享配置不存在")
    
    db.delete(share)
    db.commit()
    return {"message": "删除成功"}


@router.get("/shares/{share_id}/stats")
async def get_share_stats(share_id: str, db: Session = Depends(get_db)):
    """获取分享统计"""
    from app.models.report import ReportShare, ReportShareLog
    from sqlalchemy import func, distinct
    
    share = db.query(ReportShare).filter(ReportShare.id == share_id).first()
    if not share:
        raise HTTPException(status_code=404, detail="分享配置不存在")
    
    # 获取访问统计
    total_views = db.query(func.count(ReportShareLog.id)).filter(
        ReportShareLog.share_id == share_id
    ).scalar()
    
    unique_visitors = db.query(func.count(distinct(ReportShareLog.visitor_ip))).filter(
        ReportShareLog.share_id == share_id
    ).scalar()
    
    last_accessed = db.query(func.max(ReportShareLog.accessed_at)).filter(
        ReportShareLog.share_id == share_id
    ).scalar()
    
    return {
        "view_count": total_views or 0,
        "unique_visitors": unique_visitors or 0,
        "last_accessed": last_accessed
    }


@router.get("/shares/{share_token}/data")
async def get_shared_report_data(
    share_token: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """获取分享报表的数据（JSON API）"""
    from app.models.report import ReportShare
    
    # 查找分享配置
    share = db.query(ReportShare).filter(ReportShare.share_token == share_token).first()
    if not share:
        raise HTTPException(status_code=404, detail="分享链接不存在")
    
    # 检查状态
    if share.status != 'active':
        raise HTTPException(status_code=403, detail="分享链接已禁用")
    
    # 检查过期时间
    if share.expires_at:
        from datetime import datetime
        expires_at = datetime.fromisoformat(share.expires_at)
        if expires_at < datetime.now():
            share.status = 'expired'
            db.commit()
            raise HTTPException(status_code=403, detail="分享链接已过期")
    
    # 获取报表
    report = db.query(Report).filter(Report.id == share.report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报表不存在")
    
    dsl_definition = report.dsl_definition
    if isinstance(dsl_definition, str):
        dsl_definition = json.loads(dsl_definition)
    
    config = {
        "allow_download": share.allow_download,
        "allow_refresh": share.allow_refresh,
        "refresh_interval": share.refresh_interval,
        "show_header": share.show_header,
        "show_footer": share.show_footer,
        "theme": share.theme
    }
    
    # 为每个组件执行查询
    try:
        from app.core.engine import ReportEngine
        engine = ReportEngine()
        
        components_with_data = []
        for comp in dsl_definition.get('components', []):
            comp_copy = comp.copy()
            try:
                single_dsl = {
                    'dataSource': comp.get('dataSource', dsl_definition.get('dataSource')),
                    'components': [comp]
                }
                result = engine.execute_report(single_dsl, {})
                comp_copy['data'] = result.get('data', [])
            except Exception as comp_error:
                print(f"组件 {comp.get('id', 'unknown')} 查询失败：{comp_error}")
                comp_copy['data'] = []
            components_with_data.append(comp_copy)
        
        dsl_definition['components'] = components_with_data
    except Exception as e:
        print(f"执行报表查询失败：{e}")
    
    return {
        "name": report.name,
        "config": config,
        "components": dsl_definition.get('components', [])
    }


@router.get("/report/{share_token}", response_class=HTMLResponse)
async def view_shared_report(
    share_token: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """公开访问报表（无需登录）"""
    from app.models.report import ReportShare
    
    # 查找分享配置
    share = db.query(ReportShare).filter(ReportShare.share_token == share_token).first()
    if not share:
        raise HTTPException(status_code=404, detail="分享链接不存在")
    
    # 检查状态
    if share.status != 'active':
        raise HTTPException(status_code=403, detail="分享链接已禁用")
    
    # 检查过期时间
    if share.expires_at:
        expires_at = datetime.fromisoformat(share.expires_at)
        if expires_at < datetime.now():
            share.status = 'expired'
            db.commit()
            raise HTTPException(status_code=403, detail="分享链接已过期")
    
    # 检查访问次数
    if share.max_views and share.view_count >= share.max_views:
        share.status = 'expired'
        db.commit()
        raise HTTPException(status_code=403, detail="分享链接已达到最大访问次数")
    
    # 获取报表
    report = db.query(Report).filter(Report.id == share.report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报表不存在")
    
    # 记录访问日志
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "")
    
    log_entry = {
        "share_id": share.id,
        "visitor_ip": client_ip,
        "visitor_ua": user_agent,
        "accessed_at": datetime.now().isoformat(),
        "params": dict(request.query_params)
    }
    
    # 异步记录日志（不阻塞响应）
    try:
        from app.models.report import ReportShareLog
        log = ReportShareLog(**log_entry)
        db.add(log)
        
        # 更新访问次数
        share.view_count += 1
        db.commit()
    except Exception as e:
        print(f"记录访问日志失败：{e}")
        db.rollback()
    
    # 检查是否需要密码验证
    if share.access_level == 'password':
        # 返回密码验证页面
        return get_password_verify_page(share_token)
    
    # 返回报表页面
    dsl_definition = report.dsl_definition
    if isinstance(dsl_definition, str):
        dsl_definition = json.loads(dsl_definition)
    
    config = {
        "allow_download": share.allow_download,
        "allow_refresh": share.allow_refresh,
        "refresh_interval": share.refresh_interval,
        "show_header": share.show_header,
        "show_footer": share.show_footer,
        "theme": share.theme
    }
    
    # 使用 ReportEngine 为每个组件单独执行查询
    try:
        from app.core.engine import ReportEngine
        engine = ReportEngine()
        
        # 为每个组件单独执行查询
        components_with_data = []
        for comp in dsl_definition.get('components', []):
            comp_copy = comp.copy()
            try:
                # 构建单个组件的 DSL
                single_dsl = {
                    'dataSource': comp.get('dataSource', dsl_definition.get('dataSource')),
                    'components': [comp]
                }
                # 执行查询
                result = engine.execute_report(single_dsl, {})
                comp_copy['data'] = result.get('data', [])
            except Exception as comp_error:
                print(f"组件 {comp.get('id', 'unknown')} 查询失败：{comp_error}")
                comp_copy['data'] = []
            components_with_data.append(comp_copy)
        
        dsl_definition['components'] = components_with_data
    except Exception as e:
        print(f"执行报表查询失败：{e}")
        # 继续渲染，但数据为空
    
    return get_report_standalone_page(
        report_name=report.name,
        dsl_definition=dsl_definition,
        config=config,
        is_embed="embed" in request.query_params
    )


def get_password_verify_page(share_token: str) -> str:
    """生成密码验证页面"""
    return f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>访问验证</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        .verify-card {{
            background: white;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.2);
            width: 100%;
            max-width: 400px;
        }}
        h1 {{
            text-align: center;
            color: #333;
            margin-bottom: 30px;
        }}
        input[type="password"] {{
            width: 100%;
            padding: 12px 16px;
            border: 2px solid #e6e6e6;
            border-radius: 8px;
            font-size: 16px;
            margin-bottom: 20px;
            transition: border-color 0.3s;
        }}
        input[type="password"]:focus {{
            outline: none;
            border-color: #667eea;
        }}
        button {{
            width: 100%;
            padding: 12px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
            transition: transform 0.2s;
        }}
        button:hover {{
            transform: translateY(-2px);
        }}
        .error {{
            color: #f56c6c;
            margin-top: 10px;
            text-align: center;
            display: none;
        }}
    </style>
</head>
<body>
    <div class="verify-card">
        <h1>🔐 访问验证</h1>
        <p style="text-align: center; color: #666; margin-bottom: 20px;">请输入访问密码</p>
        <input type="password" id="password" placeholder="密码" onkeypress="if(event.keyCode==13) verifyPassword()">
        <button onclick="verifyPassword()">验证</button>
        <p class="error" id="error">密码错误</p>
    </div>
    
    <script>
        async function verifyPassword() {{
            const password = document.getElementById('password').value;
            const shareToken = '{share_token}';
            
            try {{
                const res = await fetch(`/api/shares/${{shareToken}}/verify`, {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ password }})
                }});
                
                if (res.ok) {{
                    window.location.href = `/report/${{shareToken}}`;
                }} else {{
                    document.getElementById('error').style.display = 'block';
                }}
            }} catch (e) {{
                document.getElementById('error').style.display = 'block';
            }}
        }}
    </script>
</body>
</html>
"""


def get_report_standalone_page(
    report_name: str,
    dsl_definition: dict,
    config: dict,
    is_embed: bool = False
) -> str:
    """生成独立报表页面（带 ECharts 图表支持）"""
    components_json = json.dumps(dsl_definition.get('components', []), ensure_ascii=False)
    config_json = json.dumps(config, ensure_ascii=False)
    
    return f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{report_name}</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/element-plus@2.5.0/dist/index.css">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            background: #f5f7fa;
            min-height: 100vh;
        }}
        .report-standalone {{
            min-height: 100vh;
            padding: 20px;
        }}
        .report-standalone.embed-mode {{
            background: transparent;
            padding: 0;
        }}
        .report-standalone.embed-mode header,
        .report-standalone.embed-mode footer {{
            display: none;
        }}
        header {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.1);
        }}
        .header-top {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}
        h1 {{
            color: #303133;
            font-size: 24px;
        }}
        .header-actions {{
            display: flex;
            gap: 10px;
        }}
        .last-update {{
            color: #909399;
            font-size: 14px;
        }}
        .components-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
            gap: 20px;
        }}
        .component-card {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.1);
        }}
        .component-title {{
            margin: 0 0 15px 0;
            color: #303133;
            font-size: 16px;
            border-left: 4px solid #409EFF;
            padding-left: 12px;
        }}
        footer {{
            text-align: center;
            padding: 20px;
            color: #909399;
            font-size: 14px;
        }}
        .data-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        .data-table th,
        .data-table td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e6e6e6;
        }}
        .data-table th {{
            background: #f5f7fa;
            color: #606266;
            font-weight: 600;
        }}
        .metric-card {{
            text-align: center;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 8px;
            color: white;
            min-width: 120px;
            flex: 1;
        }}
        .metric-value {{
            font-size: 32px;
            font-weight: bold;
            margin: 10px 0;
        }}
        .metric-label {{
            font-size: 14px;
            opacity: 0.9;
        }}
        .metric-prefix, .metric-suffix {{
            font-size: 18px;
            opacity: 0.8;
        }}
        .cards-container {{
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }}
        .cards-chart-wrapper {{
            width: 100%;
            margin-top: 10px;
        }}
        .cards-chart-container {{
            width: 100%;
            height: 300px;
            border-radius: 8px;
            background: #fafafa;
        }}
        .table-container {{
            overflow-x: auto;
        }}
        .chart-container {{
            width: 100%;
            height: 350px;
        }}
        @media (max-width: 768px) {{
            .components-grid {{
                grid-template-columns: 1fr;
            }}
            .metric-card {{
                min-width: 100%;
            }}
        }}
    </style>
</head>
<body>
    <div class="report-standalone" id="app" :class="{{ 'embed-mode': isEmbed }}">
        <!-- 头部 -->
        <header v-if="config.show_header">
            <div class="header-top">
                <h1>{report_name}</h1>
                <div class="header-actions">
                    <el-button v-if="config.allow_download" type="primary" size="small" @click="download">📥 下载</el-button>
                    <el-button v-if="config.allow_refresh" type="success" size="small" @click="refresh">🔄 刷新</el-button>
                </div>
            </div>
            <div class="last-update">最后更新：{{{{ lastUpdate }}}}</div>
        </header>
        
        <!-- 报表内容 -->
        <main class="components-grid">
            <div v-for="comp in components" :key="comp.id" class="component-card">
                <h3 class="component-title">{{{{ comp.title }}}}</h3>
                
                <!-- 表格组件 -->
                <div v-if="comp.type === 'table'" class="table-container">
                    <el-table :data="comp.data" style="width: 100%" border stripe size="small">
                        <el-table-column 
                            v-for="col in comp.columns" 
                            :key="col.field"
                            :prop="col.field"
                            :label="col.label"
                            :width="col.width"
                        >
                            <template #default="{{ row }}">
                                {{{{ formatValue(row[col.field], col.format) }}}}
                            </template>
                        </el-table-column>
                    </el-table>
                </div>
                
                <!-- 指标卡组件 -->
                <div v-else-if="comp.type === 'cards'" class="cards-container">
                    <!-- 如果配置了 chartType，则显示 ECharts 图表 -->
                    <div v-if="comp.config?.chartType" class="cards-chart-wrapper">
                        <div :id="'chart-' + comp.id" class="cards-chart-container"></div>
                    </div>
                    <!-- 否则显示传统指标卡 -->
                    <div v-else>
                        <div v-for="card in (comp.cards || comp.config?.cards || [])" :key="card.field" class="metric-card">
                            <div class="metric-prefix">{{{{ card.prefix || '' }}}}</div>
                            <div class="metric-value">{{{{ formatMetric(getCardValue(comp.data, card.field), card.format) }}}}</div>
                            <div class="metric-label">{{{{ card.label }}}}</div>
                            <div class="metric-suffix">{{{{ card.suffix || '' }}}}</div>
                        </div>
                    </div>
                </div>
                
                <!-- 折线图 -->
                <div v-else-if="comp.type === 'line'" :id="'chart-' + comp.id" class="chart-container"></div>
                
                <!-- 柱状图 -->
                <div v-else-if="comp.type === 'bar'" :id="'chart-' + comp.id" class="chart-container"></div>
                
                <!-- 饼图 -->
                <div v-else-if="comp.type === 'pie'" :id="'chart-' + comp.id" class="chart-container"></div>
                
                <!-- 未知组件 -->
                <div v-else class="unknown-component" style="text-align: center; color: #909399; padding: 40px;">
                    未知组件类型：{{{{ comp.type }}}}
                </div>
            </div>
        </main>
        
        <!-- 底部 -->
        <footer v-if="config.show_footer">
            <p>Powered by 自定义报表系统 | Powered by Vue 3 + ECharts</p>
        </footer>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/vue@3.4.0/dist/vue.global.prod.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/element-plus@2.5.0/dist/index.full.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
    <script>
        const {{ createApp }} = Vue;
        let charts = {{}};
        
        createApp({{
            data() {{
                return {{
                    isEmbed: {str(is_embed).lower()},
                    config: {config_json},
                    components: {components_json},
                    lastUpdate: new Date().toLocaleString('zh-CN')
                }}
            }},
            mounted() {{
                this.$nextTick(() => {{
                    this.renderCharts();
                }});
                
                // 自动刷新
                if (this.config.refresh_interval > 0) {{
                    setInterval(this.refresh, this.config.refresh_interval * 1000);
                }}
            }},
            beforeUnmount() {{
                // 销毁所有图表实例
                Object.values(charts).forEach(chart => {{
                    if (chart) chart.dispose();
                }});
            }},
            methods: {{
                formatValue(value, format) {{
                    if (value === null || value === undefined) return '-';
                    if (format === 'currency') {{
                        return '¥' + Number(value).toLocaleString('zh-CN', {{ minimumFractionDigits: 2 }});
                    }} else if (format === 'number') {{
                        return Number(value).toLocaleString('zh-CN');
                    }} else if (format === 'percent') {{
                        return (Number(value) * 100).toFixed(2) + '%';
                    }} else if (format === 'date') {{
                        return new Date(value).toLocaleDateString('zh-CN');
                    }}
                    return value;
                }},
                formatMetric(value, format) {{
                    if (value === null || value === undefined) return '0';
                    if (format === 'currency') {{
                        return '¥' + Number(value).toLocaleString('zh-CN', {{ minimumFractionDigits: 2 }});
                    }} else if (format === 'number') {{
                        return Number(value).toLocaleString('zh-CN');
                    }}
                    return value;
                }},
                getCardValue(data, field) {{
                    if (!data || !data[0]) return 0;
                    return data[0][field];
                }},
                renderCharts() {{
                    this.components.forEach(comp => {{
                        if (['line', 'bar', 'pie'].includes(comp.type)) {{
                            this.renderChart(comp);
                        }}
                        // 指标卡带图表的情况
                        if (comp.type === 'cards' && comp.config?.chartType) {{
                            this.renderCardsChart(comp);
                        }}
                    }});
                }},
                renderChart(comp) {{
                    const chartDom = document.getElementById('chart-' + comp.id);
                    if (!chartDom || !comp.data || comp.data.length === 0) return;

                    const myChart = echarts.init(chartDom);
                    let option = {{}};

                    if (comp.type === 'line') {{
                        // 折线图
                        const xData = comp.data.map(item => item[comp.config.xField]);
                        const yFields = comp.config.yFields || [Object.keys(comp.data[0]).find(k => k !== comp.config.xField)];
                        
                        option = {{
                            tooltip: {{
                                trigger: 'axis',
                                formatter: (params) => {{
                                    let result = params[0].name + '<br/>';
                                    params.forEach(p => {{
                                        result += p.marker + p.seriesName + ': ¥' + p.value.toLocaleString() + '<br/>';
                                    }});
                                    return result;
                                }}
                            }},
                            legend: {{
                                data: yFields.map(f => comp.columns?.find(c => c.field === f)?.label || f)
                            }},
                            xAxis: {{
                                type: 'category',
                                data: xData,
                                axisLabel: {{ rotate: 45 }}
                            }},
                            yAxis: {{
                                type: 'value',
                                axisLabel: {{
                                    formatter: (value) => '¥' + value.toLocaleString()
                                }}
                            }},
                            series: yFields.map((field, idx) => ({{
                                name: comp.columns?.find(c => c.field === field)?.label || field,
                                type: 'line',
                                data: comp.data.map(item => item[field]),
                                smooth: comp.config.smooth !== false,
                                areaStyle: comp.config.areaStyle || {{ opacity: 0 }},
                                itemStyle: {{
                                    pointSize: 5,
                                    pointShape: 'circle'
                                }},
                                lineStyle: {{
                                    width: comp.config.lineStyle?.width || 2
                                }}
                            }}))
                        }};
                    }} else if (comp.type === 'bar') {{
                        // 柱状图
                        const xData = comp.data.map(item => item[comp.config.xField]);
                        const yField = comp.config.yField || Object.keys(comp.data[0]).find(k => k !== comp.config.xField);
                        const seriesField = comp.config.seriesField;
                        
                        if (seriesField) {{
                            // 分组柱状图
                            const groups = [...new Set(comp.data.map(item => item[seriesField]))];
                            option = {{
                                tooltip: {{
                                    trigger: 'axis',
                                    axisPointer: {{ type: 'shadow' }}
                                }},
                                legend: {{
                                    data: groups
                                }},
                                xAxis: {{
                                    type: 'category',
                                    data: xData,
                                    axisLabel: {{ rotate: 45 }}
                                }},
                                yAxis: {{
                                    type: 'value',
                                    axisLabel: {{
                                        formatter: (value) => '¥' + value.toLocaleString()
                                    }}
                                }},
                                series: groups.map(group => ({{
                                    name: group,
                                    type: 'bar',
                                    data: comp.data
                                        .filter(item => item[seriesField] === group)
                                        .map(item => item[yField]),
                                    barWidth: '60%'
                                }}))
                            }};
                        }} else {{
                            // 简单柱状图
                            option = {{
                                tooltip: {{
                                    trigger: 'axis',
                                    axisPointer: {{ type: 'shadow' }}
                                }},
                                xAxis: {{
                                    type: 'category',
                                    data: xData,
                                    axisLabel: {{ rotate: 45 }}
                                }},
                                yAxis: {{
                                    type: 'value',
                                    axisLabel: {{
                                        formatter: (value) => '¥' + value.toLocaleString()
                                    }}
                                }},
                                series: [{{
                                    name: comp.columns?.find(c => c.field === yField)?.label || yField,
                                    type: 'bar',
                                    data: comp.data.map(item => item[yField]),
                                    barWidth: '60%',
                                    label: {{
                                        show: true,
                                        position: 'top',
                                        formatter: (params) => '¥' + params.value.toLocaleString()
                                    }}
                                }}]
                            }};
                        }}
                    }} else if (comp.type === 'pie') {{
                        // 饼图
                        const nameField = comp.config.colorField || comp.columns?.[0]?.field || Object.keys(comp.data[0])[0];
                        const valueField = comp.config.angleField || comp.columns?.find(c => c.format !== 'percent')?.field || Object.keys(comp.data[0]).find(k => k !== nameField);
                        
                        option = {{
                            tooltip: {{
                                trigger: 'item',
                                formatter: '{{b}}: {{c}} ({{d}}%)'
                            }},
                            legend: {{
                                orient: 'vertical',
                                left: 'left'
                            }},
                            series: [{{
                                name: comp.title,
                                type: 'pie',
                                radius: comp.config.innerRadius ? [comp.config.innerRadius * 100 + '%', comp.config.radius * 100 + '%'] : (comp.config.radius * 100 + '%'),
                                data: comp.data.map(item => ({{
                                    name: item[nameField],
                                    value: item[valueField]
                                }})),
                                emphasis: {{
                                    itemStyle: {{
                                        shadowBlur: 10,
                                        shadowOffsetX: 0,
                                        shadowColor: 'rgba(0, 0, 0, 0.5)'
                                    }}
                                }},
                                label: {{
                                    formatter: '{{b}}: {{d}}%'
                                }}
                            }}]
                        }};
                    }}
                    
                    myChart.setOption(option);
                    charts[comp.id] = myChart;

                    // 响应式调整
                    window.addEventListener('resize', () => {{
                        myChart.resize();
                    }});
                }},
                renderCardsChart(comp) {{
                    const chartDom = document.getElementById('chart-' + comp.id);
                    if (!chartDom || !comp.data || comp.data.length === 0) return;

                    const myChart = echarts.init(chartDom);
                    const chartType = comp.config.chartType;
                    const cards = comp.cards || comp.config?.cards || [];
                    const data = comp.data[0] || {{}};

                    const names = cards.map(c => c.label || c.field);
                    const values = cards.map(c => {{
                        const val = data[c.field];
                        return val !== null && val !== undefined ? Number(val) : 0;
                    }});

                    let option = {{}};

                    if (chartType === 'gauge') {{
                        option = {{
                            series: cards.map((card, idx) => {{
                                const total = cards.length;
                                const angle = 360 / total;
                                const startAngle = -90 + idx * angle;
                                return {{
                                    type: 'gauge',
                                    startAngle: startAngle,
                                    endAngle: startAngle + angle - 5,
                                    min: card.min || 0,
                                    max: card.max || Math.max(values[idx] * 1.5, 100),
                                    radius: '90%',
                                    center: ['50%', '50%'],
                                    progress: {{
                                        show: true,
                                        width: 12,
                                        itemStyle: {{
                                            color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
                                                {{ offset: 0, color: '#667eea' }},
                                                {{ offset: 1, color: '#764ba2' }}
                                            ])
                                        }}
                                    }},
                                    pointer: {{ show: false }},
                                    axisLine: {{ lineStyle: {{ width: 12, color: [[1, '#eee']] }} }},
                                    axisTick: {{ show: false }},
                                    splitLine: {{ show: false }},
                                    axisLabel: {{ show: false }},
                                    detail: {{
                                        valueAnimation: true,
                                        formatter: (val) => {{
                                            if (card.format === 'currency') return '¥' + val.toLocaleString();
                                            if (card.format === 'percent') return val.toFixed(1) + '%';
                                            return val.toLocaleString();
                                        }},
                                        fontSize: 20,
                                        fontWeight: 'bold',
                                        color: '#333',
                                        offsetCenter: [0, '30%']
                                    }},
                                    title: {{
                                        offsetCenter: [0, '60%'],
                                        fontSize: 12,
                                        color: '#666'
                                    }},
                                    data: [{{
                                        value: values[idx],
                                        name: card.prefix ? card.prefix + ' ' + (card.label || card.field) : (card.label || card.field)
                                    }}]
                                }};
                            }})
                        }};
                    }} else if (chartType === 'bar') {{
                        option = {{
                            tooltip: {{
                                trigger: 'axis',
                                axisPointer: {{ type: 'shadow' }},
                                formatter: (params) => {{
                                    const p = params[0];
                                    const card = cards[p.dataIndex];
                                    let val = p.value;
                                    if (card?.format === 'currency') val = '¥' + val.toLocaleString();
                                    else if (card?.format === 'percent') val = val.toFixed(2) + '%';
                                    else val = val.toLocaleString();
                                    return `${{p.name}}<br/>${{val}}`;
                                }}
                            }},
                            grid: {{ left: '3%', right: '4%', bottom: '3%', top: '10%', containLabel: true }},
                            xAxis: {{
                                type: 'category',
                                data: names,
                                axisLabel: {{ fontSize: 11, rotate: 15 }},
                                axisTick: {{ alignWithLabel: true }}
                            }},
                            yAxis: {{
                                type: 'value',
                                axisLabel: {{
                                    formatter: (val) => {{
                                        if (values.some(v => v > 10000)) return (val / 10000).toFixed(0) + '万';
                                        return val.toLocaleString();
                                    }}
                                }}
                            }},
                            series: [{{
                                name: comp.title,
                                type: 'bar',
                                data: values,
                                barWidth: '50%',
                                itemStyle: {{
                                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                                        {{ offset: 0, color: '#667eea' }},
                                        {{ offset: 1, color: '#764ba2' }}
                                    ]),
                                    borderRadius: [4, 4, 0, 0]
                                }},
                                label: {{
                                    show: true,
                                    position: 'top',
                                    formatter: (params) => {{
                                        const card = cards[params.dataIndex];
                                        const val = params.value;
                                        if (card?.format === 'currency') return '¥' + val.toLocaleString();
                                        if (card?.format === 'percent') return val.toFixed(2) + '%';
                                        return val.toLocaleString();
                                    }},
                                    fontSize: 11
                                }}
                            }}]
                        }};
                    }} else if (chartType === 'radar') {{
                        const maxValue = Math.max(...values) * 1.2;
                        option = {{
                            tooltip: {{
                                trigger: 'item',
                                formatter: (params) => {{
                                    const card = cards[params.dataIndex];
                                    let val = params.value;
                                    if (card?.format === 'currency') val = '¥' + val.toLocaleString();
                                    else if (card?.format === 'percent') val = val.toFixed(2) + '%';
                                    else val = val.toLocaleString();
                                    return `${{params.name}}<br/>${{val}}`;
                                }}
                            }},
                            radar: {{
                                indicator: names.map(name => ({{ name, max: maxValue }})),
                                radius: '70%',
                                axisName: {{ fontSize: 11 }},
                                splitArea: {{ areaStyle: {{ color: ['#f8f9fa', '#fff'] }} }}
                            }},
                            series: [{{
                                type: 'radar',
                                data: [{{
                                    value: values,
                                    name: comp.title,
                                    areaStyle: {{ color: 'rgba(102, 126, 234, 0.3)' }},
                                    lineStyle: {{ color: '#667eea', width: 2 }},
                                    itemStyle: {{ color: '#667eea' }},
                                    label: {{
                                        show: true,
                                        formatter: (params) => {{
                                            const card = cards[params.dataIndex];
                                            const val = params.value;
                                            if (card?.format === 'currency') return '¥' + val.toLocaleString();
                                            if (card?.format === 'percent') return val.toFixed(1) + '%';
                                            return val.toLocaleString();
                                        }},
                                        fontSize: 10
                                    }}
                                }}]
                            }}]
                        }};
                    }} else if (chartType === 'funnel') {{
                        const sortedData = cards.map((c, i) => ({{
                            name: c.label || c.field,
                            value: values[i]
                        }})).sort((a, b) => b.value - a.value);

                        option = {{
                            tooltip: {{
                                trigger: 'item',
                                formatter: (params) => {{
                                    const card = cards.find(c => (c.label || c.field) === params.name);
                                    let val = params.value;
                                    if (card?.format === 'currency') val = '¥' + val.toLocaleString();
                                    else if (card?.format === 'percent') val = val.toFixed(2) + '%';
                                    else val = val.toLocaleString();
                                    return `${{params.name}}<br/>${{val}}`;
                                }}
                            }},
                            legend: {{ orient: 'vertical', left: 'left', textStyle: {{ fontSize: 11 }} }},
                            series: [{{
                                type: 'funnel',
                                left: '20%',
                                width: '60%',
                                min: 0,
                                max: Math.max(...values),
                                minSize: '0%',
                                maxSize: '100%',
                                sort: 'descending',
                                gap: 5,
                                label: {{
                                    show: true,
                                    position: 'inside',
                                    formatter: (params) => {{
                                        const card = cards.find(c => (c.label || c.field) === params.name);
                                        if (card?.format === 'currency') return '¥' + params.value.toLocaleString();
                                        if (card?.format === 'percent') return params.value.toFixed(2) + '%';
                                        return params.value.toLocaleString();
                                    }},
                                    fontSize: 11
                                }},
                                itemStyle: {{
                                    borderColor: '#fff',
                                    borderWidth: 1
                                }},
                                data: sortedData
                            }}]
                        }};
                    }}

                    myChart.setOption(option);
                    charts[comp.id] = myChart;

                    window.addEventListener('resize', () => {{
                        myChart.resize();
                    }});
                }},
                refresh() {{
                    this.lastUpdate = new Date().toLocaleString('zh-CN');
                    // 重新渲染图表
                    this.$nextTick(() => {{
                        this.renderCharts();
                    }});
                }},
                download() {{
                    alert('下载功能开发中...');
                }}
            }}
        }}).use(ElementPlus).mount('#app');
    </script>
</body>
</html>
"""
