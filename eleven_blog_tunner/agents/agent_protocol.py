"""
Agent 通信协议模块

定义 Agent 之间的通信标准和调用链机制。
"""
from typing import Dict, List, Optional, Any, Callable, Awaitable
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
import uuid
import asyncio
import time
from collections import defaultdict


class MessageType(Enum):
    """消息类型枚举"""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CircuitBreakerStatus(Enum):
    """熔断器状态枚举"""
    CLOSED = "closed"      # 关闭状态 - 正常服务
    OPEN = "open"          # 开启状态 - 熔断中
    HALF_OPEN = "half_open"  # 半开状态 - 试探性服务


class CircuitBreaker:
    """熔断器

    实现熔断机制，当 Agent 连续失败次数超过阈值时，
    自动熔断该 Agent 一段时间，防止级联故障。
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 30,
        half_open_max_calls: int = 3
    ):
        """初始化熔断器

        Args:
            failure_threshold: 失败阈值，超过此值触发熔断
            recovery_timeout: 熔断恢复时间（秒）
            half_open_max_calls: 半开状态下最大试探调用次数
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls

        # 状态管理
        self._status: Dict[str, CircuitBreakerStatus] = defaultdict(
            lambda: CircuitBreakerStatus.CLOSED
        )
        self._failure_counts: Dict[str, int] = defaultdict(int)
        self._last_failure_time: Dict[str, float] = defaultdict(float)
        self._half_open_calls: Dict[str, int] = defaultdict(int)

    def get_status(self, agent_name: str) -> CircuitBreakerStatus:
        """获取 Agent 的熔断状态

        Args:
            agent_name: Agent 名称

        Returns:
            熔断状态
        """
        status = self._status[agent_name]

        # 检查是否需要从 OPEN 转换为 HALF_OPEN
        if status == CircuitBreakerStatus.OPEN:
            last_failure = self._last_failure_time[agent_name]
            if time.time() - last_failure >= self.recovery_timeout:
                self._status[agent_name] = CircuitBreakerStatus.HALF_OPEN
                self._half_open_calls[agent_name] = 0
                return CircuitBreakerStatus.HALF_OPEN

        return status

    def can_execute(self, agent_name: str) -> bool:
        """检查是否可以执行 Agent

        Args:
            agent_name: Agent 名称

        Returns:
            是否可以执行
        """
        status = self.get_status(agent_name)

        if status == CircuitBreakerStatus.CLOSED:
            return True

        if status == CircuitBreakerStatus.OPEN:
            return False

        if status == CircuitBreakerStatus.HALF_OPEN:
            # 半开状态下限制试探调用次数
            return self._half_open_calls[agent_name] < self.half_open_max_calls

        return True

    def record_success(self, agent_name: str):
        """记录成功调用

        Args:
            agent_name: Agent 名称
        """
        status = self._status[agent_name]

        if status == CircuitBreakerStatus.HALF_OPEN:
            self._half_open_calls[agent_name] += 1
            # 如果半开状态下成功次数达到阈值，关闭熔断器
            if self._half_open_calls[agent_name] >= self.half_open_max_calls:
                self._reset(agent_name)
        else:
            # 正常状态下重置失败计数
            self._failure_counts[agent_name] = 0

    def record_failure(self, agent_name: str):
        """记录失败调用

        Args:
            agent_name: Agent 名称
        """
        status = self._status[agent_name]
        self._failure_counts[agent_name] += 1
        self._last_failure_time[agent_name] = time.time()

        if status == CircuitBreakerStatus.HALF_OPEN:
            # 半开状态下失败，重新熔断
            self._status[agent_name] = CircuitBreakerStatus.OPEN
        elif self._failure_counts[agent_name] >= self.failure_threshold:
            # 达到失败阈值，开启熔断
            self._status[agent_name] = CircuitBreakerStatus.OPEN

    def _reset(self, agent_name: str):
        """重置熔断器状态

        Args:
            agent_name: Agent 名称
        """
        self._status[agent_name] = CircuitBreakerStatus.CLOSED
        self._failure_counts[agent_name] = 0
        self._half_open_calls[agent_name] = 0
        self._last_failure_time[agent_name] = 0

    def get_stats(self, agent_name: str) -> Dict[str, Any]:
        """获取熔断器统计信息

        Args:
            agent_name: Agent 名称

        Returns:
            统计信息
        """
        return {
            "status": self._status[agent_name].value,
            "failure_count": self._failure_counts[agent_name],
            "last_failure_time": self._last_failure_time[agent_name],
            "half_open_calls": self._half_open_calls[agent_name]
        }


class AgentMessage(BaseModel):
    """Agent 消息结构

    用于 Agent 之间传递的消息格式。
    """
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender: str
    receiver: str
    content: str
    message_type: MessageType = MessageType.REQUEST
    metadata: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=datetime.now)
    reply_to: Optional[str] = None


class TaskContext(BaseModel):
    """任务上下文

    描述一个完整任务的执行上下文。
    """
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    parent_task_id: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    result: Optional[str] = None
    error: Optional[str] = None
    steps: List[Dict[str, Any]] = []


class AgentCallChain:
    """Agent 调用链

    管理 Agent 之间的调用关系和执行流程。
    """

    def __init__(self):
        self.agents: Dict[str, Any] = {}
        self.call_history: List[AgentMessage] = []
        self.task_contexts: Dict[str, TaskContext] = {}

    def register_agent(self, name: str, agent: Any):
        """注册 Agent

        Args:
            name: Agent 名称
            agent: Agent 实例
        """
        self.agents[name] = agent

    def get_agent(self, name: str) -> Optional[Any]:
        """获取 Agent

        Args:
            name: Agent 名称

        Returns:
            Agent 实例
        """
        return self.agents.get(name)

    def create_task(self, parent_task_id: Optional[str] = None) -> TaskContext:
        """创建任务上下文

        Args:
            parent_task_id: 父任务 ID

        Returns:
            任务上下文
        """
        task = TaskContext(parent_task_id=parent_task_id)
        self.task_contexts[task.task_id] = task
        return task

    def update_task_status(self, task_id: str, status: TaskStatus, **kwargs):
        """更新任务状态

        Args:
            task_id: 任务 ID
            status: 新状态
            **kwargs: 其他更新字段
        """
        if task_id in self.task_contexts:
            task = self.task_contexts[task_id]
            task.status = status
            task.updated_at = datetime.now()
            for key, value in kwargs.items():
                if hasattr(task, key):
                    setattr(task, key, value)

    def add_step(self, task_id: str, step: Dict[str, Any]):
        """添加执行步骤

        Args:
            task_id: 任务 ID
            step: 步骤信息
        """
        if task_id in self.task_contexts:
            self.task_contexts[task_id].steps.append(step)

    async def send_message(
        self,
        sender: str,
        receiver: str,
        content: str,
        message_type: MessageType = MessageType.REQUEST,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentMessage:
        """发送消息

        Args:
            sender: 发送者
            receiver: 接收者
            content: 消息内容
            message_type: 消息类型
            metadata: 元数据

        Returns:
            发送的消息
        """
        message = AgentMessage(
            sender=sender,
            receiver=receiver,
            content=content,
            message_type=message_type,
            metadata=metadata or {}
        )
        self.call_history.append(message)
        return message

    async def route_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """路由消息

        Args:
            message: 消息

        Returns:
            响应消息
        """
        receiver = self.get_agent(message.receiver)
        if not receiver:
            return await self.send_message(
                sender=message.receiver,
                receiver=message.sender,
                content=f"Agent {message.receiver} 未找到",
                message_type=MessageType.ERROR,
                metadata={"original_message_id": message.message_id}
            )

        try:
            response_content = await receiver.execute(message.content)
            return await self.send_message(
                sender=message.receiver,
                receiver=message.sender,
                content=response_content,
                message_type=MessageType.RESPONSE,
                metadata={"original_message_id": message.message_id}
            )
        except Exception as e:
            return await self.send_message(
                sender=message.receiver,
                receiver=message.sender,
                content=f"执行失败: {str(e)}",
                message_type=MessageType.ERROR,
                metadata={"original_message_id": message.message_id}
            )


class AgentProtocol:
    """Agent 通信协议

    定义 Agent 之间的标准通信接口和流程。
    集成熔断机制，防止 Agent 故障导致级联失败。
    """

    def __init__(
        self,
        enable_circuit_breaker: bool = True,
        failure_threshold: int = 5,
        recovery_timeout: int = 30
    ):
        """初始化 AgentProtocol

        Args:
            enable_circuit_breaker: 是否启用熔断机制
            failure_threshold: 熔断失败阈值
            recovery_timeout: 熔断恢复时间（秒）
        """
        self.call_chain = AgentCallChain()
        self.enable_circuit_breaker = enable_circuit_breaker

        # 初始化熔断器
        if enable_circuit_breaker:
            self.circuit_breaker = CircuitBreaker(
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout
            )
        else:
            self.circuit_breaker = None

        self._init_builtin_agents()

    def _init_builtin_agents(self):
        """初始化内置 Agent"""
        # 延迟导入以避免循环导入
        try:
            from eleven_blog_tunner.agents.boss_agent import BossAgent
            from eleven_blog_tunner.agents.system_agent import SystemAgent
            from eleven_blog_tunner.agents.summary_agent import SummaryAgent
            from eleven_blog_tunner.agents.writer_agent import WriterAgent
            from eleven_blog_tunner.agents.review_agent import ReviewAgent

            self.register_agent("BossAgent", BossAgent())
            self.register_agent("SystemAgent", SystemAgent())
            self.register_agent("SummaryAgent", SummaryAgent())
            self.register_agent("WriterAgent", WriterAgent())
            self.register_agent("ReviewAgent", ReviewAgent())
        except ImportError:
            # 导入失败时跳过初始化
            pass

    def register_agent(self, name: str, agent: Any):
        """注册 Agent

        Args:
            name: Agent 名称
            agent: Agent 实例
        """
        self.call_chain.register_agent(name, agent)

    def get_agent(self, name: str) -> Optional[Any]:
        """获取 Agent

        Args:
            name: Agent 名称

        Returns:
            Agent 实例
        """
        return self.call_chain.get_agent(name)

    async def execute_task(
        self,
        task: str,
        initial_input: str,
        agent_sequence: Optional[List[str]] = None
    ) -> str:
        """执行任务

        Args:
            task: 任务描述
            initial_input: 初始输入
            agent_sequence: Agent 执行序列，默认使用标准流程

        Returns:
            任务结果

        Raises:
            CircuitBreakerOpenError: 当 Agent 处于熔断状态时抛出
        """
        if agent_sequence is None:
            agent_sequence = [
                "BossAgent",
                "SystemAgent",
                "SummaryAgent",
                "WriterAgent",
                "ReviewAgent"
            ]

        task_context = self.call_chain.create_task()
        self.call_chain.update_task_status(task_context.task_id, TaskStatus.RUNNING)

        current_input = initial_input
        writer_result = None

        for agent_name in agent_sequence:
            # 检查熔断状态
            if self.enable_circuit_breaker and not self.circuit_breaker.can_execute(agent_name):
                error_msg = f"Agent {agent_name} 当前处于熔断状态，暂时不可用"
                self.call_chain.update_task_status(
                    task_context.task_id,
                    TaskStatus.FAILED,
                    error=error_msg
                )
                raise CircuitBreakerOpenError(error_msg)

            agent = self.get_agent(agent_name)
            if not agent:
                self.call_chain.update_task_status(
                    task_context.task_id,
                    TaskStatus.FAILED,
                    error=f"Agent {agent_name} 未找到"
                )
                raise ValueError(f"Agent {agent_name} 未找到")

            self.call_chain.add_step(task_context.task_id, {
                "agent": agent_name,
                "input": current_input,
                "timestamp": datetime.now().isoformat()
            })

            try:
                # 创建 AgentContext 对象
                from eleven_blog_tunner.agents.base_agent import AgentContext
                context = AgentContext(
                    task_id=task_context.task_id,
                    user_input=current_input
                )
                current_input = await agent.execute(context)

                # 记录成功
                if self.enable_circuit_breaker:
                    self.circuit_breaker.record_success(agent_name)

                # 保存 WriterAgent 的结果
                if agent_name == "WriterAgent":
                    writer_result = current_input

            except Exception as e:
                # 记录失败
                if self.enable_circuit_breaker:
                    self.circuit_breaker.record_failure(agent_name)

                self.call_chain.update_task_status(
                    task_context.task_id,
                    TaskStatus.FAILED,
                    error=str(e)
                )
                raise

        # 对于文章生成任务，返回 WriterAgent 的结果
        final_result = writer_result if writer_result else current_input

        self.call_chain.update_task_status(
            task_context.task_id,
            TaskStatus.COMPLETED,
            result=final_result
        )

        return final_result

    async def call_agent(
        self,
        caller: str,
        callee: str,
        input_data: str
    ) -> Dict[str, Any]:
        """Agent 间直接调用

        Args:
            caller: 调用者
            callee: 被调用者
            input_data: 输入数据

        Returns:
            调用结果
        """
        # 检查熔断状态
        if self.enable_circuit_breaker and not self.circuit_breaker.can_execute(callee):
            return {
                "success": False,
                "error": f"Agent {callee} 当前处于熔断状态，暂时不可用",
                "callee": callee,
                "circuit_breaker": self.circuit_breaker.get_stats(callee)
            }

        agent = self.get_agent(callee)
        if not agent:
            return {
                "success": False,
                "error": f"Agent {callee} 未找到"
            }

        try:
            result = await agent.execute(input_data)

            # 记录成功
            if self.enable_circuit_breaker:
                self.circuit_breaker.record_success(callee)

            return {
                "success": True,
                "result": result,
                "callee": callee
            }
        except Exception as e:
            # 记录失败
            if self.enable_circuit_breaker:
                self.circuit_breaker.record_failure(callee)

            return {
                "success": False,
                "error": str(e),
                "callee": callee
            }

    def get_circuit_breaker_stats(self, agent_name: Optional[str] = None) -> Dict[str, Any]:
        """获取熔断器统计信息

        Args:
            agent_name: Agent 名称，不指定则返回所有 Agent 的统计

        Returns:
            熔断器统计信息
        """
        if not self.enable_circuit_breaker:
            return {"enabled": False}

        if agent_name:
            return {
                "enabled": True,
                "agent": agent_name,
                "stats": self.circuit_breaker.get_stats(agent_name)
            }

        # 返回所有已注册 Agent 的统计
        all_stats = {}
        for name in self.call_chain.agents.keys():
            all_stats[name] = self.circuit_breaker.get_stats(name)

        return {
            "enabled": True,
            "agents": all_stats
        }

    def reset_circuit_breaker(self, agent_name: str):
        """手动重置熔断器

        Args:
            agent_name: Agent 名称
        """
        if self.enable_circuit_breaker:
            self.circuit_breaker._reset(agent_name)

    def get_task_context(self, task_id: str) -> Optional[TaskContext]:
        """获取任务上下文

        Args:
            task_id: 任务 ID

        Returns:
            任务上下文
        """
        return self.call_chain.task_contexts.get(task_id)

    def get_call_history(self) -> List[AgentMessage]:
        """获取调用历史

        Returns:
            调用历史列表
        """
        return self.call_chain.call_history


class CircuitBreakerOpenError(Exception):
    """熔断器开启异常

    当 Agent 处于熔断状态时抛出此异常。
    """
    pass


# 全局协议实例
_global_protocol: Optional[AgentProtocol] = None


def get_protocol(
    enable_circuit_breaker: bool = True,
    failure_threshold: int = 5,
    recovery_timeout: int = 30
) -> AgentProtocol:
    """获取全局协议实例

    Args:
        enable_circuit_breaker: 是否启用熔断机制
        failure_threshold: 熔断失败阈值
        recovery_timeout: 熔断恢复时间（秒）

    Returns:
        AgentProtocol 实例
    """
    global _global_protocol
    if _global_protocol is None:
        _global_protocol = AgentProtocol(
            enable_circuit_breaker=enable_circuit_breaker,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout
        )
    return _global_protocol
