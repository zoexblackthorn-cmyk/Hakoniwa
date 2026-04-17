"""
轻量级任务调度服务 - 基于 APScheduler AsyncIOScheduler
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# 全局 scheduler 实例
scheduler = AsyncIOScheduler()


def start_scheduler():
    """启动调度器（幂等）"""
    if not scheduler.running:
        scheduler.start()
        print("⏰ Scheduler started")
