from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger
import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from typing import Optional
import asyncio

from app.config import settings


class SchedulerService:
    """定时任务服务"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.tasks = {}
    
    def start(self):
        """启动调度器"""
        self.scheduler.start()
        logger.info("定时任务调度器已启动")
    
    def shutdown(self):
        """关闭调度器"""
        self.scheduler.shutdown()
        logger.info("定时任务调度器已关闭")
    
    def add_task(
        self,
        task_id: str,
        cron_expr: str,
        callback: callable,
        args: Optional[tuple] = None
    ):
        """
        添加定时任务
        
        Args:
            task_id: 任务 ID
            cron_expr: Cron 表达式 (如 "0 8 * * *")
            callback: 回调函数
            args: 回调函数参数
        """
        trigger = CronTrigger.from_crontab(cron_expr)
        
        self.scheduler.add_job(
            callback,
            trigger,
            args=args or (),
            id=task_id,
            replace_existing=True
        )
        
        self.tasks[task_id] = True
        logger.info(f"添加定时任务：{task_id}, cron={cron_expr}")
    
    def remove_task(self, task_id: str):
        """移除定时任务"""
        if task_id in self.tasks:
            try:
                self.scheduler.remove_job(task_id)
                del self.tasks[task_id]
                logger.info(f"移除定时任务：{task_id}")
            except Exception as e:
                logger.error(f"移除任务失败：{e}")
    
    async def send_email_with_attachment(
        self,
        recipient: str,
        subject: str,
        body: str,
        attachment_bytes: bytes,
        filename: str
    ):
        """
        发送带附件的邮件
        
        Args:
            recipient: 收件人
            subject: 主题
            body: 正文
            attachment_bytes: 附件字节
            filename: 附件文件名
        """
        msg = MIMEMultipart()
        msg['From'] = settings.SMTP_FROM
        msg['To'] = recipient
        msg['Subject'] = subject
        
        # 添加正文
        msg.attach(MIMEBase('text', 'plain').set_payload(body))
        
        # 添加附件
        attachment = MIMEBase('application', 'octet-stream')
        attachment.set_payload(attachment_bytes)
        attachment.add_header(
            'Content-Disposition',
            'attachment',
            filename=filename
        )
        msg.attach(attachment)
        
        # 发送邮件
        try:
            await aiosmtplib.send(
                msg,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                start_tls=True
            )
            logger.info(f"邮件发送成功：{recipient}")
        except Exception as e:
            logger.error(f"邮件发送失败：{e}")
            raise


# 全局调度器实例
scheduler = SchedulerService()
