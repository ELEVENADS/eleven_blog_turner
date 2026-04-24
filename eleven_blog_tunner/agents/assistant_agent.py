"""
Assistant Agent 模块

负责辅助文本生成，包括：
- 文本续写和补充
- 基于选中内容的风格提取
- 智能文本生成建议
- 内容改写和润色
"""
from typing import Dict, List, Optional, Any
from eleven_blog_tunner.agents.base_agent import BaseAgent, AgentContext, AgentType


class AssistantAgent(BaseAgent):
    """
    Assistant Agent

    负责辅助文本生成和编辑：
    - 根据上下文续写文本
    - 提取选中内容的风格
    - 生成内容建议
    - 改写和润色文本
    """

    def __init__(self, llm_provider: str = "openai", use_memory: bool = True):
        super().__init__(
            name="AssistantAgent",
            description="负责辅助文本生成，包括续写、风格提取、改写润色等",
            agent_type=AgentType.ASSISTANT,
            llm_provider=llm_provider,
            use_memory=use_memory
        )

    async def execute(self, context: AgentContext) -> str:
        """执行辅助任务

        Args:
            context: Agent 上下文

        Returns:
            执行结果
        """
        if not self.validate_context(context):
            return "错误: 无效的上下文"

        task_type = context.metadata.get("task_type", "continue")
        selected_text = context.metadata.get("selected_text", "")
        surrounding_context = context.metadata.get("context", "")

        if task_type == "continue":
            style_hint = context.metadata.get("style_hint", "")
            length = context.metadata.get("length", 200)
            result = await self._continue_writing(
                selected_text, surrounding_context, style_hint, length
            )
        elif task_type == "extract_style":
            result = await self._extract_selection_style(selected_text)
        elif task_type == "rewrite":
            style = context.metadata.get("style", "")
            result = await self._rewrite_content(selected_text, style)
        elif task_type == "polish":
            result = await self._polish_text(selected_text)
        elif task_type == "suggest":
            result = await self._generate_suggestions(selected_text, surrounding_context)
        elif task_type == "expand":
            target_length = context.metadata.get("target_length", 200)
            result = await self._expand_content(selected_text, target_length)
        elif task_type == "summarize":
            result = await self._summarize_selection(selected_text)
        else:
            result = "未知的任务类型"

        return result

    async def _continue_writing(
        self,
        selected_text: str,
        context: str,
        style_hint: str,
        length: int
    ) -> str:
        """续写文本

        Args:
            selected_text: 选中的文本
            context: 上下文
            style_hint: 风格提示
            length: 生成长度

        Returns:
            续写内容
        """
        try:
            messages = [
                {
                    "role": "system",
                    "content": f"你是一位专业的写作助手。请根据用户提供的文本，继续撰写约{length}字的内容，保持与原文风格一致。只输出续写的内容，不要添加解释。"
                },
                {
                    "role": "user",
                    "content": f"前文内容：\n{context}\n\n选中的文本（作为续写起点）：\n{selected_text}\n\n请继续撰写："
                }
            ]

            result = await self.call_llm(messages, temperature=0.7, max_tokens=length * 2)
            return result
        except Exception as e:
            return f"续写失败: {str(e)}"

    async def _extract_selection_style(self, text: str) -> str:
        """提取选中内容的风格

        Args:
            text: 选中的文本

        Returns:
            风格描述
        """
        try:
            if not text or len(text) < 50:
                return "选中的文本太短，无法提取风格（至少需要50字符）"

            messages = [
                {
                    "role": "system",
                    "content": "你是一位专业的写作风格分析师。请分析以下文本的写作风格特征，包括：语言风格、句式特点、词汇偏好、情感倾向、独特习惯等。用中文输出分析结果。"
                },
                {
                    "role": "user",
                    "content": f"请分析以下文本的写作风格：\n\n{text}"
                }
            ]

            result = await self.call_llm(messages, temperature=0.3, max_tokens=1000)
            return result
        except Exception as e:
            return f"风格提取失败: {str(e)}"

    async def _rewrite_content(self, text: str, style: str) -> str:
        """改写内容

        Args:
            text: 原文本
            style: 目标风格

        Returns:
            改写后的文本
        """
        try:
            messages = [
                {
                    "role": "system",
                    "content": f"你是一位专业的写作助手。请将用户提供的文本改写为{style}风格，保持原意不变。只输出改写后的内容，不要添加解释。"
                },
                {
                    "role": "user",
                    "content": f"请将以下内容改写为{style}风格：\n\n{text}"
                }
            ]

            result = await self.call_llm(messages, temperature=0.7, max_tokens=2000)
            return result
        except Exception as e:
            return f"改写失败: {str(e)}"

    async def _polish_text(self, text: str) -> str:
        """润色文本

        Args:
            text: 原文本

        Returns:
            润色后的文本
        """
        try:
            messages = [
                {
                    "role": "system",
                    "content": "你是一位专业的写作助手。请对用户提供的文本进行润色，优化用词和句式，使其更加流畅、准确。保持原意不变，只输出润色后的内容，不要添加解释。"
                },
                {
                    "role": "user",
                    "content": f"请润色以下文本：\n\n{text}"
                }
            ]

            result = await self.call_llm(messages, temperature=0.5, max_tokens=2000)
            return result
        except Exception as e:
            return f"润色失败: {str(e)}"

    async def _generate_suggestions(self, selected_text: str, context: str) -> str:
        """生成写作建议

        Args:
            selected_text: 选中的文本
            context: 上下文

        Returns:
            建议内容
        """
        try:
            messages = [
                {
                    "role": "system",
                    "content": "你是一位专业的写作顾问。请基于用户提供的文本，给出具体的写作建议，包括内容补充、结构优化、表达优化等方面。用中文输出建议。"
                },
                {
                    "role": "user",
                    "content": f"上下文：\n{context}\n\n选中的文本：\n{selected_text}\n\n请给出写作建议："
                }
            ]

            result = await self.call_llm(messages, temperature=0.5, max_tokens=1500)
            return result
        except Exception as e:
            return f"生成建议失败: {str(e)}"

    async def _expand_content(self, text: str, target_length: int) -> str:
        """扩写内容

        Args:
            text: 原文本
            target_length: 目标长度

        Returns:
            扩写后的文本
        """
        try:
            messages = [
                {
                    "role": "system",
                    "content": f"你是一位专业的写作助手。请将用户提供的文本扩写至约{target_length}字，增加细节描述、例子和解释，保持原文风格和主题。只输出扩写后的内容，不要添加解释。"
                },
                {
                    "role": "user",
                    "content": f"请扩写以下文本至约{target_length}字：\n\n{text}"
                }
            ]

            result = await self.call_llm(messages, temperature=0.7, max_tokens=target_length * 2)
            return result
        except Exception as e:
            return f"扩写失败: {str(e)}"

    async def _summarize_selection(self, text: str) -> str:
        """总结选中的内容

        Args:
            text: 原文本

        Returns:
            总结内容
        """
        try:
            messages = [
                {
                    "role": "system",
                    "content": "你是一位专业的内容总结助手。请对用户提供的文本进行总结，提炼核心要点。用中文输出总结结果。"
                },
                {
                    "role": "user",
                    "content": f"请总结以下文本的核心要点：\n\n{text}"
                }
            ]

            result = await self.call_llm(messages, temperature=0.3, max_tokens=1000)
            return result
        except Exception as e:
            return f"总结失败: {str(e)}"

    def get_system_prompt(self) -> str:
        """获取系统提示词

        Returns:
            系统提示词
        """
        return """你是 AssistantAgent，是博客写作系统的智能写作助手。

你的职责：
1. 根据上下文智能续写文本
2. 分析选中内容的写作风格
3. 提供内容改写和润色服务
4. 生成写作建议和优化方案
5. 扩写或总结选中的内容

工作原则：
1. 保持与原文风格一致
2. 内容连贯、逻辑清晰
3. 语言流畅、表达准确
4. 尊重原文意图，不偏离主题

任务类型：
- **续写**：根据上下文继续撰写内容
- **风格提取**：分析选中文本的写作风格
- **改写**：按指定风格改写内容
- **润色**：优化文本表达
- **建议**：提供写作建议
- **扩写**：扩展内容细节
- **总结**：提炼核心要点

始终保持专业的辅助态度，帮助用户提升写作质量。"""
