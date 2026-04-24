"""
状态监控

负责：
- 系统状态监控
- 任务进度追踪
- 资源使用监控
- 异常检测和告警
"""
import asyncio
import psutil
import platform
import logging
from datetime import datetime
from typing import Dict, Any, List
import threading
import time

from eleven_blog_tunner.gateway.task_manager import TaskManager, TaskStatus

logger = logging.getLogger(__name__)


class StatusMonitor:
    """状态监控器"""
    
    def __init__(self, task_manager: TaskManager):
        self.task_manager = task_manager
        self.running = False
        self.monitor_task = None
        self.system_status = {}
        self.task_stats = {}
        self.resource_usage = {}
        self.alerts = []
        self.lock = threading.Lock()
    
    async def start(self):
        """启动状态监控"""
        if not self.running:
            self.running = True
            self.monitor_task = asyncio.create_task(self._monitor_loop())
            logger.info("状态监控已启动")
    
    async def stop(self):
        """停止状态监控"""
        if self.running:
            self.running = False
            if self.monitor_task:
                await self.monitor_task
            logger.info("状态监控已停止")
    
    async def get_system_status(self) -> Dict[str, Any]:
        """
        获取系统状态
        
        Returns:
            系统状态
        """
        with self.lock:
            return {
                "timestamp": datetime.now().isoformat(),
                "system": self.system_status,
                "resources": self.resource_usage,
                "tasks": self.task_stats,
                "alerts": self.alerts
            }
    
    async def get_task_stats(self) -> Dict[str, Any]:
        """
        获取任务统计
        
        Returns:
            任务统计
        """
        with self.lock:
            return self.task_stats
    
    async def get_resource_usage(self) -> Dict[str, Any]:
        """
        获取资源使用情况
        
        Returns:
            资源使用情况
        """
        with self.lock:
            return self.resource_usage
    
    async def get_alerts(self) -> List[Dict[str, Any]]:
        """
        获取告警信息
        
        Returns:
            告警信息列表
        """
        with self.lock:
            return self.alerts
    
    async def _monitor_loop(self):
        """监控循环"""
        while self.running:
            try:
                await self._collect_system_status()
                await self._collect_task_stats()
                await self._collect_resource_usage()
                await self._check_alerts()
            except Exception as e:
                logger.error(f"监控循环异常: {e}")
            
            await asyncio.sleep(10)  # 每10秒收集一次状态
    
    async def _collect_system_status(self):
        """收集系统状态"""
        try:
            system_info = {
                "hostname": platform.node(),
                "platform": platform.system(),
                "platform_version": platform.version(),
                "python_version": platform.python_version(),
                "uptime": time.time() - psutil.boot_time(),
                "timestamp": datetime.now().isoformat()
            }

            with self.lock:
                self.system_status = system_info
        except Exception as e:
            logger.error(f"收集系统状态失败: {e}")
    
    async def _collect_task_stats(self):
        """收集任务统计"""
        try:
            if not self.task_manager:
                return
            
            # 统计任务状态
            task_counts = {
                "total": 0,
                "pending": 0,
                "running": 0,
                "completed": 0,
                "failed": 0,
                "cancelled": 0
            }
            
            # 统计任务类型
            task_types = {}
            
            # 统计最近任务
            recent_tasks = []
            
            # 遍历所有任务
            for task_id, task in self.task_manager.tasks.items():
                task_counts["total"] += 1
                task_counts[task.status.value] += 1
                
                # 统计任务类型
                if task.task_type not in task_types:
                    task_types[task.task_type] = 0
                task_types[task.task_type] += 1
                
                # 收集最近的任务
                if len(recent_tasks) < 10:
                    recent_tasks.append({
                        "task_id": task_id,
                        "type": task.task_type,
                        "status": task.status.value,
                        "progress": task.progress,
                        "updated_at": task.updated_at.isoformat()
                    })
            
            stats = {
                "counts": task_counts,
                "types": task_types,
                "recent_tasks": recent_tasks,
                "timestamp": datetime.now().isoformat()
            }
            
            with self.lock:
                self.task_stats = stats
        except Exception as e:
            logger.error(f"收集任务统计失败: {e}")
    
    async def _collect_resource_usage(self):
        """收集资源使用情况"""
        try:
            # CPU 使用率
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # 内存使用率
            memory = psutil.virtual_memory()
            memory_usage = {
                "total": memory.total,
                "available": memory.available,
                "used": memory.used,
                "percent": memory.percent
            }
            
            # 磁盘使用率
            disk = psutil.disk_usage('/')
            disk_usage = {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": disk.percent
            }
            
            # 网络使用率
            net_io = psutil.net_io_counters()
            network_usage = {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv
            }
            
            resources = {
                "cpu": cpu_percent,
                "memory": memory_usage,
                "disk": disk_usage,
                "network": network_usage,
                "timestamp": datetime.now().isoformat()
            }
            
            with self.lock:
                self.resource_usage = resources
        except Exception as e:
            logger.error(f"收集资源使用情况失败: {e}")
    
    async def _check_alerts(self):
        """检查告警"""
        try:
            new_alerts = []
            
            # 检查资源使用告警
            if self.resource_usage:
                # CPU 使用率告警
                if self.resource_usage.get("cpu", 0) > 80:
                    new_alerts.append({
                        "level": "warning",
                        "message": f"CPU 使用率过高: {self.resource_usage['cpu']}%",
                        "timestamp": datetime.now().isoformat(),
                        "type": "resource"
                    })
                
                # 内存使用率告警
                memory_percent = self.resource_usage.get("memory", {}).get("percent", 0)
                if memory_percent > 80:
                    new_alerts.append({
                        "level": "warning",
                        "message": f"内存使用率过高: {memory_percent}%",
                        "timestamp": datetime.now().isoformat(),
                        "type": "resource"
                    })
                
                # 磁盘使用率告警
                disk_percent = self.resource_usage.get("disk", {}).get("percent", 0)
                if disk_percent > 90:
                    new_alerts.append({
                        "level": "critical",
                        "message": f"磁盘使用率过高: {disk_percent}%",
                        "timestamp": datetime.now().isoformat(),
                        "type": "resource"
                    })
            
            # 检查任务告警
            if self.task_stats:
                # 失败任务告警
                failed_count = self.task_stats.get("counts", {}).get("failed", 0)
                if failed_count > 5:
                    new_alerts.append({
                        "level": "warning",
                        "message": f"失败任务过多: {failed_count} 个",
                        "timestamp": datetime.now().isoformat(),
                        "type": "task"
                    })
                
                # 待处理任务告警
                pending_count = self.task_stats.get("counts", {}).get("pending", 0)
                if pending_count > 10:
                    new_alerts.append({
                        "level": "info",
                        "message": f"待处理任务较多: {pending_count} 个",
                        "timestamp": datetime.now().isoformat(),
                        "type": "task"
                    })
            
            # 更新告警列表，只保留最近的20条
            with self.lock:
                self.alerts = new_alerts + self.alerts[:19]
        except Exception as e:
            logger.error(f"检查告警失败: {e}")
    
    async def clear_alerts(self):
        """
        清除告警
        """
        with self.lock:
            self.alerts = []
        logger.info("告警已清除")
