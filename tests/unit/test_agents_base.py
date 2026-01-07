"""
Unit tests for boring.agents.base module.

测试原则：
1. 测试决策结果：给定输入数据，应该得到什么输出
2. 只 mock 边界：不 mock 自己的 domain logic
3. 测试名称即规格：清楚说明输入和期望输出
"""

from boring.agents.base import (
    Agent,
    AgentContext,
    AgentMessage,
    AgentRole,
    SharedResource,
)


class TestAgentRole:
    """测试 AgentRole 枚举的行为"""

    def test_应包含所有定义的代理角色(self):
        """规格：AgentRole 应包含 ARCHITECT, CODER, REVIEWER, ORCHESTRATOR"""
        assert AgentRole.ARCHITECT is not None
        assert AgentRole.CODER is not None
        assert AgentRole.REVIEWER is not None
        assert AgentRole.ORCHESTRATOR is not None


class TestSharedResource:
    """测试 SharedResource 数据类的行为"""

    def test_当创建新资源时_版本号应为1(self):
        """规格：创建新资源 → version 应该是 1"""
        resource = SharedResource(name="test", content="data")

        assert resource.name == "test"
        assert resource.content == "data"
        assert resource.version == 1

    def test_当转换为字典时_应包含所有字段(self):
        """规格：to_dict() → 应返回包含所有字段的字典"""
        resource = SharedResource(
            name="test", content="data", version=2, last_updated_by=AgentRole.ARCHITECT
        )
        data = resource.to_dict()

        # 测试结果：应该包含所有字段
        assert data["name"] == "test"
        assert data["content"] == "data"
        assert data["version"] == 2
        assert data["last_updated_by"] == "architect"

    def test_当从字典创建时_应正确还原所有字段(self):
        """规格：from_dict(dict) → 应创建包含相同数据的 SharedResource"""
        data = {"name": "test", "content": "data", "version": 2, "last_updated_by": "architect"}
        resource = SharedResource.from_dict(data)

        # 测试结果：应该正确还原所有字段
        assert resource.name == "test"
        assert resource.content == "data"
        assert resource.version == 2
        assert resource.last_updated_by == AgentRole.ARCHITECT

    def test_当字典中没有role时_应设置为None(self):
        """规格：from_dict(dict without role) → last_updated_by 应该是 None"""
        data = {"name": "test", "content": "data"}
        resource = SharedResource.from_dict(data)

        assert resource.last_updated_by is None


class TestAgentMessage:
    """测试 AgentMessage 数据类的行为"""

    def test_当创建消息时_应保存所有字段(self):
        """规格：创建 AgentMessage → 应保存 sender, receiver, action, summary"""
        msg = AgentMessage(
            sender=AgentRole.ARCHITECT,
            receiver=AgentRole.CODER,
            action="plan_created",
            summary="Plan ready",
        )

        # 测试结果：所有字段应该正确保存
        assert msg.sender == AgentRole.ARCHITECT
        assert msg.receiver == AgentRole.CODER
        assert msg.action == "plan_created"
        assert msg.summary == "Plan ready"
        assert msg.requires_approval is False  # 默认值

    def test_当创建带artifacts的消息时_应保存artifacts(self):
        """规格：创建带 artifacts 的消息 → artifacts 应该被保存"""
        msg = AgentMessage(
            sender=AgentRole.CODER,
            receiver=AgentRole.REVIEWER,
            action="code_written",
            summary="Code done",
            artifacts={"files": ["file1.py"]},
        )

        # 测试结果：artifacts 应该被正确保存
        assert "files" in msg.artifacts
        assert msg.artifacts["files"] == ["file1.py"]

    def test_当消息需要审批时_应设置审批标志和原因(self):
        """规格：requires_approval=True → 应设置审批标志和原因"""
        msg = AgentMessage(
            sender=AgentRole.ARCHITECT,
            receiver=AgentRole.CODER,
            action="plan_created",
            summary="Plan",
            requires_approval=True,
            approval_reason="Needs review",
        )

        # 测试结果：审批相关字段应该正确设置
        assert msg.requires_approval is True
        assert msg.approval_reason == "Needs review"


class TestAgentContext:
    """测试 AgentContext 类的行为"""

    def test_当创建context时_应初始化所有默认值(self, tmp_path):
        """规格：创建 AgentContext → 应设置 project_root, task_description, current_phase="planning" """
        context = AgentContext(project_root=tmp_path, task_description="Task")

        # 测试结果：应该正确初始化
        assert context.project_root == tmp_path
        assert context.task_description == "Task"
        assert context.current_phase == "planning"

    def test_当获取不存在的资源时_应返回None(self, tmp_path):
        """规格：get_resource("nonexistent") → 应返回 None"""
        context = AgentContext(project_root=tmp_path, task_description="Task")

        result = context.get_resource("nonexistent")

        assert result is None

    def test_当设置新资源时_应能获取该资源(self, tmp_path):
        """规格：set_resource("test", "data") → get_resource("test") 应返回 "data" """
        context = AgentContext(project_root=tmp_path, task_description="Task")
        context.set_resource("test", "data", AgentRole.ARCHITECT)

        result = context.get_resource("test")

        assert result == "data"

    def test_当更新已存在的资源时_版本号应递增(self, tmp_path):
        """规格：更新已存在的资源 → version 应递增，last_updated_by 应更新"""
        context = AgentContext(project_root=tmp_path, task_description="Task")
        context.set_resource("test", "data1", AgentRole.ARCHITECT)
        context.set_resource("test", "data2", AgentRole.CODER)

        # 测试结果：应该返回最新值
        result = context.get_resource("test")
        assert result == "data2"

        # 测试结果：版本应该递增，更新者应该改变
        resource = context.resources["test"]
        assert resource.version == 2
        assert resource.last_updated_by == AgentRole.CODER

    def test_当添加消息时_应保存到消息历史(self, tmp_path):
        """规格：add_message(msg) → messages 列表应包含该消息"""
        context = AgentContext(project_root=tmp_path, task_description="Task")
        msg = AgentMessage(
            sender=AgentRole.ARCHITECT,
            receiver=AgentRole.CODER,
            action="plan_created",
            summary="Plan",
        )
        context.add_message(msg)

        # 测试结果：消息应该被保存
        assert len(context.messages) == 1
        assert context.messages[0] == msg

    def test_当获取最新消息时_应返回最后添加的消息(self, tmp_path):
        """规格：添加多条消息后 → get_latest_message_from(role) 应返回最后一条"""
        context = AgentContext(project_root=tmp_path, task_description="Task")

        msg1 = AgentMessage(
            sender=AgentRole.ARCHITECT, receiver=AgentRole.CODER, action="plan1", summary="Plan 1"
        )
        msg2 = AgentMessage(
            sender=AgentRole.ARCHITECT, receiver=AgentRole.CODER, action="plan2", summary="Plan 2"
        )
        context.add_message(msg1)
        context.add_message(msg2)

        latest = context.get_latest_message_from(AgentRole.ARCHITECT)

        # 测试结果：应该返回最后添加的消息
        assert latest == msg2
        assert latest.action == "plan2"

    def test_当没有消息时_应返回None(self, tmp_path):
        """规格：get_latest_message_from(role) 当没有消息时 → 应返回 None"""
        context = AgentContext(project_root=tmp_path, task_description="Task")

        latest = context.get_latest_message_from(AgentRole.ARCHITECT)

        assert latest is None

    def test_当获取当前计划时_应返回implementation_plan资源(self, tmp_path):
        """规格：get_current_plan() → 应返回 "implementation_plan" 资源的内容"""
        context = AgentContext(project_root=tmp_path, task_description="Task")
        context.set_resource("implementation_plan", "Test plan", AgentRole.ARCHITECT)

        plan = context.get_current_plan()

        assert plan == "Test plan"

    def test_当获取修改的文件列表时_应返回modified_files资源(self, tmp_path):
        """规格：get_modified_files() → 应返回 "modified_files" 资源的内容"""
        context = AgentContext(project_root=tmp_path, task_description="Task")
        context.set_resource("modified_files", ["file1.py", "file2.py"], AgentRole.CODER)

        files = context.get_modified_files()

        assert files == ["file1.py", "file2.py"]


class TestAgent:
    """测试 Agent 基类的行为"""

    def test_Agent应该是抽象基类(self):
        """规格：Agent 应该继承自 ABC，不能直接实例化"""
        from abc import ABC

        assert issubclass(Agent, ABC), "Agent 应该是抽象基类"

    def test_当创建具体Agent实现时_應保存role和llm_client(self):
        """规格：创建 Agent 子类实例 → 应保存 role 和 llm_client"""
        from unittest.mock import MagicMock

        mock_client = MagicMock()

        # 创建具体实现
        class TestAgent(Agent):
            @property
            def system_prompt(self):
                return "Test prompt"

            async def execute(self, context):
                pass

        agent = TestAgent(mock_client, AgentRole.ARCHITECT)

        # 测试结果：应该正确保存属性
        assert agent.role == AgentRole.ARCHITECT
        assert agent.client == mock_client
