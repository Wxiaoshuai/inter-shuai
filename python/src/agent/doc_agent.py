"""Document processing agent with validation."""

from typing import TypedDict
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from src.core.llm import get_llm


class DocumentAgentState(TypedDict):
    """State for document processing agent."""
    messages: list
    current_step: str
    iterations: int
    result: str
    data_content: str


class DocumentAgent:
    """Document processing agent with direct tool calling and validation."""

    def __init__(self, file_id: str, file_path: str, file_type: str, requirements: str):
        self.agent_id = f"doc_agent_{file_id}"
        self.file_path = file_path
        self.file_type = file_type
        self.requirements = requirements

    def run(self, tools: list) -> dict:
        """Run the document processing agent with validation."""
        llm = get_llm()
        llm_with_tools = llm.bind_tools(tools)

        prompt = self._build_initial_message()
        messages = [HumanMessage(content=prompt)]

        # Step 1: Read file and analyze
        response = llm_with_tools.invoke(messages)
        messages.append(response)

        raw_content = ""
        if hasattr(response, 'tool_calls') and response.tool_calls:
            tool_call = response.tool_calls[0]
            tool_name = tool_call.get("name")
            tool_args = tool_call.get("args", {})
            tool_id = tool_call.get("id")

            for t in tools:
                if t.name == tool_name:
                    result = t.invoke(tool_args)
                    raw_content = str(result)
                    messages.append(
                        ToolMessage(content=raw_content, tool_call_id=tool_id, name=tool_name)
                    )
                    break

        # Step 2: Generate analysis results
        analysis_prompt = f"""你已经读取了文件数据。现在根据用户需求进行深入分析：

用户需求：{self.requirements}

请执行以下操作：
1. 根据需求分析数据
2. 如需要生成图表，使用 generate_chart 工具生成（chart_type 可选: heatmap, bar, line, pie, scatter, histogram）
3. 整理分析结果

请开始分析。"""

        messages.append(HumanMessage(content=analysis_prompt))
        response = llm_with_tools.invoke(messages)
        messages.append(response)

        # Collect generated content (including chart URLs if any)
        analysis_content = response.content if hasattr(response, 'content') else ""

        # Step 3: Check for chart images in the tool calls and add them to response
        print(f"[doc_agent] Step 3: response has tool_calls: {hasattr(response, 'tool_calls') and response.tool_calls}")
        if hasattr(response, 'tool_calls') and response.tool_calls:
            for tool_call in response.tool_calls:
                tool_name = tool_call.get("name")
                tool_args = tool_call.get("args", {})
                tool_id = tool_call.get("id")
                print(f"[doc_agent] tool_call: name={tool_name}, args={tool_args}, id={tool_id}")

                if tool_name == "generate_chart":
                    for t in tools:
                        if t.name == "generate_chart":
                            # print(f"[doc_agent] Invoking generate_chart with args: {tool_args}")
                            chart_result = t.invoke(tool_args)
                            print(f"[doc_agent] generate_chart returned: {chart_result}")
                            if not chart_result.startswith("Error"):
                                # Add chart image to content using markdown image syntax
                                chart_markdown = f"\n\n![Chart]({chart_result})"
                                print(f"[doc_agent] Adding chart markdown: {chart_markdown}")
                                analysis_content += chart_markdown
                                messages.append(
                                    ToolMessage(content=chart_result, tool_call_id=tool_id, name=tool_name)
                                )
                            break

        print(f"[doc_agent] Final analysis_content: {analysis_content[:200]}...")

        # Step 4: Validate the output
        validation_prompt = f"""请检查以下分析结果是否合格：

{analysis_content[:500]}...

检查标准：
1. 是否有实际的数据内容（不是空回复或"数据读取成功"等客套话）
2. 如有图表需求，是否已生成图表（通过 generate_chart 工具返回的 base64 图片）
3. 内容是否针对用户需求进行了实际分析

如果结果不合格，返回"INVALID: 原因"
如果结果合格，返回"VALID" """

        messages.append(HumanMessage(content=validation_prompt))
        validation_response = llm_with_tools.invoke(messages)

        is_valid = True
        review_feedback = ""

        if hasattr(validation_response, 'content'):
            content = validation_response.content.strip()
            if content.startswith("INVALID"):
                is_valid = False
                review_feedback = content[8:].strip()

        if not is_valid:
            # Return message asking user if they want to continue
            return {
                "status": "needs_confirmation",
                "message": f"分析结果可能不完整：{review_feedback}。您是否希望我继续尝试另一种分析方式？",
                "data_content": analysis_content,
                "needs_continue": True
            }

        # Step 5: Clean up and format the output for display
        cleanup_prompt = f"""请整理以下分析结果，使其更适合展示给用户：

{analysis_content}

要求：
1. 移除不必要的客套话（如"很好！数据已经读取成功"）
2. 确保数据呈现清晰，如果有图表保留图片链接
3. 返回整理后的内容"""

        messages.append(HumanMessage(content=cleanup_prompt))
        cleanup_response = llm_with_tools.invoke(messages)

        final_content = cleanup_response.content if hasattr(cleanup_response, 'content') else analysis_content

        return {
            "status": "success",
            "data_content": final_content,
            "iterations": 2,
            "needs_continue": False
        }

    def _build_initial_message(self) -> str:
        """Build the initial prompt for the agent."""
        if self.file_type == 'excel':
            task = f"""你是一个专业的文档处理助手。请分析用户上传的Excel文件：

1. 首先使用 read_excel_file 工具读取文件：{self.file_path}
2. 理解文件内容和结构
3. 根据用户需求分析数据：{self.requirements}
4. 将分析结果以清晰的格式返回给用户

请开始处理。"""
        else:
            task = f"""你是一个专业的文档处理助手。请分析用户上传的Word文档：

1. 首先使用 read_word_file 工具读取文件：{self.file_path}
2. 理解文档内容和结构
3. 根据用户需求分析或处理文档：{self.requirements}
4. 将分析结果以清晰的格式返回给用户

请开始处理。"""

        return task