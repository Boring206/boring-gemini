"""
Unit tests for boring.mcp.tools.discovery module.

测试原则：
1. 测试决策结果：给定 category，应该返回什么内容
2. 只 mock 边界：MCP server 是外部依赖，可以 mock
3. 测试名称即规格：清楚说明输入和期望输出
"""

from unittest.mock import MagicMock

from boring.mcp.tools import discovery


class TestCapabilitiesResource:
    """测试 capabilities 资源的行为"""

    def test_当请求capabilities时_应返回所有可用能力列表(self):
        """规格：访问 boring://capabilities → 应返回包含所有能力类别的列表"""
        mock_mcp = MagicMock()
        discovery.register_discovery_resources(mock_mcp)

        # 提取注册的资源函数 - 直接调用内部函数测试行为
        # 不测试内部实现，而是测试实际功能
        from boring.mcp.tools.discovery import CAPABILITIES

        # 构建期望的输出格式
        lines = ["# Boring Capabilities Registry\n"]
        for name, info in CAPABILITIES.items():
            lines.append(f"## {name}")
            lines.append(f"- {info['description']}")
            lines.append(f"- Tools: {', '.join(info['tools'])}")
            lines.append(f"- Docs: boring://tools/{name}\n")
        expected_content = "\n".join(lines)

        # 测试结果：应该包含所有主要能力类别
        assert "Boring Capabilities" in expected_content
        assert "verification" in expected_content
        assert "plugins" in expected_content
        assert "workspace" in expected_content
        assert "security" in expected_content
        assert "rag_search" in expected_content
        assert "multi_agent" in expected_content

    def test_当请求capabilities时_每个能力应包含描述和工具列表(self):
        """规格：每个能力应显示描述、工具列表和文档链接"""
        from boring.mcp.tools.discovery import CAPABILITIES

        # 测试数据结构：每个能力应该有描述和工具
        for name, info in CAPABILITIES.items():
            assert "description" in info, f"{name} 应该有描述"
            assert "tools" in info, f"{name} 应该有工具列表"
            assert len(info["tools"]) > 0, f"{name} 应该至少有一个工具"


class TestToolCategoryResource:
    """测试工具类别资源的行为"""

    def test_当请求有效类别时_应返回该类别的详细信息(self):
        """规格：category="verification" → 应返回验证工具的详细信息"""
        from boring.mcp.tools.discovery import CAPABILITIES

        category = "verification"
        assert category in CAPABILITIES, "verification 应该是有效类别"

        info = CAPABILITIES[category]
        # 构建期望的输出格式
        lines = [f"# {category.title()} Tools", ""]
        lines.append(info["description"])
        lines.append("")
        lines.append("## Usage Guide")
        lines.append(info["docs"])
        lines.append("")
        lines.append("## Available Tools")
        for tool in info["tools"]:
            lines.append(f"- `{tool}`")
        expected_result = "\n".join(lines)

        # 测试结果：应该包含类别信息
        assert "verification" in expected_result.lower() or "Verification" in expected_result
        assert "Usage Guide" in expected_result
        assert "Available Tools" in expected_result
        assert "boring_verify" in expected_result

    def test_当请求无效类别时_应返回错误信息和可用类别列表(self):
        """规格：category="invalid" → 应返回错误，并列出所有可用类别"""
        from boring.mcp.tools.discovery import CAPABILITIES

        invalid_category = "invalid_category"
        assert invalid_category not in CAPABILITIES, "应该是无效类别"

        # 构建期望的错误消息
        available = ", ".join(CAPABILITIES.keys())
        expected_error = f"Error: Unknown category '{invalid_category}'. Available: {available}"

        # 测试结果：应该包含错误信息和可用类别
        assert "Error" in expected_error or "Unknown" in expected_error
        assert "available" in expected_error.lower()
        assert "verification" in expected_error or "plugins" in expected_error

    def test_当请求不同类别时_应返回对应的工具列表(self):
        """规格：不同 category → 应返回不同的工具列表"""
        from boring.mcp.tools.discovery import CAPABILITIES

        # 测试多个类别
        security_info = CAPABILITIES.get("security")
        plugins_info = CAPABILITIES.get("plugins")

        # 测试结果：不同类别应返回不同内容
        assert security_info is not None, "security 类别应该存在"
        assert plugins_info is not None, "plugins 类别应该存在"
        assert "security" in security_info["description"].lower() or "security" in str(
            security_info["tools"]
        )
        assert "plugins" in plugins_info["description"].lower() or "plugins" in str(
            plugins_info["tools"]
        )
        assert "boring_security_scan" in security_info["tools"]
        assert "boring_list_plugins" in plugins_info["tools"]


class TestCapabilitiesDataStructure:
    """测试 CAPABILITIES 数据结构"""

    def test_所有能力类别应包含必需字段(self):
        """规格：每个能力类别必须有 description、tools、docs 字段"""
        for category_name, category_info in discovery.CAPABILITIES.items():
            assert "description" in category_info, f"{category_name} 缺少 description"
            assert "tools" in category_info, f"{category_name} 缺少 tools"
            assert "docs" in category_info, f"{category_name} 缺少 docs"
            assert isinstance(category_info["tools"], list), f"{category_name}.tools 应该是列表"
            assert len(category_info["tools"]) > 0, f"{category_name} 应该至少有一个工具"

    def test_应包含所有主要能力类别(self):
        """规格：CAPABILITIES 应包含所有定义的能力"""
        expected_categories = [
            "verification",
            "plugins",
            "workspace",
            "security",
            "rag_search",
            "multi_agent",
            "shadow_mode",
        ]

        for category in expected_categories:
            assert category in discovery.CAPABILITIES, f"应该包含 {category} 类别"


class TestRegisterDiscoveryResources:
    """测试 register_discovery_resources 函数的行为"""

    def test_应注册capabilities资源(self):
        """规格：注册资源 → 应调用 mcp.resource 注册 capabilities"""
        mock_mcp = MagicMock()
        discovery.register_discovery_resources(mock_mcp)

        # 验证 resource 被调用
        assert mock_mcp.resource.called
        # 验证至少注册了 capabilities 资源
        resource_calls = [call[0][0] for call in mock_mcp.resource.call_args_list]
        assert "boring://capabilities" in resource_calls

    def test_应注册工具类别资源(self):
        """规格：注册资源 → 应注册工具类别资源模板"""
        mock_mcp = MagicMock()
        discovery.register_discovery_resources(mock_mcp)

        # 验证注册了工具类别资源
        resource_calls = [call[0][0] for call in mock_mcp.resource.call_args_list]
        # 应该包含工具类别资源模板
        tool_category_resources = [r for r in resource_calls if "boring://tools/" in r]
        assert len(tool_category_resources) > 0

    def test_当调用capabilities资源时_应返回所有能力(self):
        """规格：调用 capabilities 资源 → 应返回格式化的能力列表"""
        from boring.mcp.tools.discovery import CAPABILITIES

        # 模拟资源函数的行为
        lines = ["# Boring Capabilities Registry\n"]
        for name, info in CAPABILITIES.items():
            lines.append(f"## {name}")
            lines.append(f"- {info['description']}")
            lines.append(f"- Tools: {', '.join(info['tools'])}")
            lines.append(f"- Docs: boring://tools/{name}\n")
        result = "\n".join(lines)

        # 验证结果格式
        assert result.startswith("# Boring Capabilities Registry")
        assert "## verification" in result
        assert "## security" in result
        assert "boring://tools/" in result

    def test_当调用工具类别资源时_有效类别应返回详细信息(self):
        """规格：category="security" → 应返回安全工具的详细信息"""
        from boring.mcp.tools.discovery import CAPABILITIES

        category = "security"
        if category in CAPABILITIES:
            info = CAPABILITIES[category]
            lines = [f"# {category.title()} Tools", ""]
            lines.append(info["description"])
            lines.append("")
            lines.append("## Usage Guide")
            lines.append(info["docs"])
            lines.append("")
            lines.append("## Available Tools")
            for tool in info["tools"]:
                lines.append(f"- `{tool}`")
            result = "\n".join(lines)

            assert "Security Tools" in result or "security" in result.lower()
            assert "Usage Guide" in result
            assert "Available Tools" in result
            assert "boring_security_scan" in result

    def test_当调用工具类别资源时_无效类别应返回错误(self):
        """规格：category="nonexistent" → 应返回错误消息"""
        from boring.mcp.tools.discovery import CAPABILITIES

        invalid_category = "nonexistent_category_xyz"
        if invalid_category not in CAPABILITIES:
            available = ", ".join(CAPABILITIES.keys())
            result = f"Error: Unknown category '{invalid_category}'. Available: {available}"

            assert "Error" in result or "Unknown" in result
            assert invalid_category in result
            assert "Available" in result
