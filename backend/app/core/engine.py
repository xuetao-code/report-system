import asyncio
from typing import Dict, Any, List
from sqlalchemy import create_engine, text
from jinja2 import Template
from loguru import logger
from functools import lru_cache


class ReportEngine:
    """报表引擎核心 - 支持批量并发查询"""
    
    def __init__(self):
        self.engine_cache = {}
        self.query_cache = {}  # 查询结果缓存
    
    def execute_report(self, report_dsl: dict, params: dict) -> dict:
        """
        执行报表查询
        
        Args:
            report_dsl: 报表 DSL 定义
            params: 查询参数
            
        Returns:
            查询结果 + 组件配置
        """
        # 1. 参数替换（Jinja2 模板）
        query_template = Template(report_dsl["dataSource"]["query"])
        final_query = query_template.render(**params)
        logger.info(f"执行查询：{final_query}")
        
        # 2. 获取数据源连接
        ds_config = report_dsl["dataSource"]
        engine = self._get_engine(ds_config)
        
        # 3. 执行查询
        try:
            with engine.connect() as conn:
                result = conn.execute(text(final_query))
                # 获取列名
                columns = result.keys()
                # 转换为字典列表
                data = [dict(zip(columns, row)) for row in result]
            
            logger.info(f"查询完成，返回 {len(data)} 条记录")
            
            # 4. 返回数据 + 组件配置
            return {
                "data": data,
                "components": report_dsl.get("components", [])
            }
        except Exception as e:
            logger.error(f"查询执行失败：{e}")
            raise
    
    def _get_engine(self, ds_config: dict):
        """获取或创建数据库引擎"""
        # 根据类型生成缓存键
        if ds_config["type"] == "sqlite":
            cache_key = f"sqlite://{ds_config.get('file_path', '')}"
        else:
            cache_key = f"{ds_config['type']}://{ds_config.get('host', '')}:{ds_config.get('port', '')}/{ds_config.get('database', '')}"
        
        if cache_key not in self.engine_cache:
            if ds_config["type"] == "mysql":
                url = f"mysql+pymysql://{ds_config.get('username', '')}:{ds_config.get('password', '')}@{ds_config.get('host', 'localhost')}:{ds_config.get('port', 3306)}/{ds_config.get('database', '')}"
            elif ds_config["type"] == "postgresql":
                url = f"postgresql://{ds_config.get('username', '')}:{ds_config.get('password', '')}@{ds_config.get('host', 'localhost')}:{ds_config.get('port', 5432)}/{ds_config.get('database', '')}"
            else:  # sqlite
                file_path = ds_config.get('file_path', ':memory:')
                url = f"sqlite:///{file_path}"
            
            self.engine_cache[cache_key] = create_engine(url, pool_pre_ping=True, connect_args={"check_same_thread": False} if ds_config["type"] == "sqlite" else {})
            logger.info(f"创建数据库引擎：{cache_key}")
        
        return self.engine_cache[cache_key]
    
    def clear_cache(self, ds_id: str = None):
        """清除引擎缓存"""
        if ds_id:
            keys_to_remove = [k for k in self.engine_cache.keys() if ds_id in k]
            for key in keys_to_remove:
                del self.engine_cache[key]
        else:
            self.engine_cache.clear()
    
    async def execute_batch(self, components: List[Dict], dsl_definition: Dict, params: Dict) -> List[Dict]:
        """
        批量并发执行多个组件的查询
        
        Args:
            components: 组件列表
            dsl_definition: 完整 DSL 定义（包含顶层 dataSource）
            params: 查询参数
            
        Returns:
            带数据的组件列表
        """
        # 顶层 dataSource（如果组件没有单独的 dataSource）
        top_ds = dsl_definition.get('dataSource', {})
        
        async def execute_single(comp: dict) -> dict:
            """单个组件查询"""
            try:
                comp_copy = comp.copy()
                # 如果组件没有 dataSource，使用顶层的
                if not comp_copy.get('dataSource'):
                    comp_copy['dataSource'] = top_ds
                result = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.execute_report_for_component(comp_copy, params)
                )
                comp_copy['data'] = result
                return comp_copy
            except Exception as e:
                logger.error(f"组件 {comp.get('id', 'unknown')} 查询失败：{e}")
                comp_copy = comp.copy()
                comp_copy['data'] = []
                comp_copy['error'] = str(e)
                return comp_copy
        
        # 并发执行所有组件
        tasks = [execute_single(comp) for comp in components]
        results = await asyncio.gather(*tasks)
        
        logger.info(f"批量查询完成，{len(results)} 个组件")
        return list(results)
    
    def execute_report_for_component(self, component: dict, params: dict) -> list:
        """为单个组件执行查询"""
        ds_config = component.get('dataSource', {})
        
        if not ds_config:
            return []
        
        # 参数替换
        query_template = Template(ds_config.get('query', ''))
        final_query = query_template.render(**params)
        logger.info(f"执行组件查询：{final_query[:100]}...")
        
        # 获取数据库连接
        engine = self._get_engine(ds_config)
        
        # 执行查询
        try:
            with engine.connect() as conn:
                result = conn.execute(text(final_query))
                columns = result.keys()
                data = [dict(zip(columns, row)) for row in result]
            
            logger.info(f"组件查询完成，返回 {len(data)} 条记录")
            return data
        except Exception as e:
            logger.error(f"组件查询失败：{e}")
            raise
