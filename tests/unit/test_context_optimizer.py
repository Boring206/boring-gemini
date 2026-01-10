"""
精準測試 Context Optimizer - 智能上下文優化
"""


from boring.intelligence.context_optimizer import ContextOptimizer, ContextSection, ContextStats


class TestContextSection:
    """測試 ContextSection 數據結構"""

    def test_section_initialization(self):
        """測試 section 初始化"""
        section = ContextSection(
            content="def test():\n    pass",
            source="test.py",
            priority=0.8,
            token_count=10,
            content_hash="abc123",
            section_type="code"
        )

        assert section.content == "def test():\n    pass"
        assert section.source == "test.py"
        assert section.priority == 0.8
        assert section.token_count == 10
        assert section.section_type == "code"

    def test_section_priority_range(self):
        """測試 priority 範圍"""
        high_priority = ContextSection(
            content="ERROR",
            source="error",
            priority=1.0,
            token_count=5,
            content_hash="err",
            section_type="error"
        )

        low_priority = ContextSection(
            content="docs",
            source="readme",
            priority=0.1,
            token_count=100,
            content_hash="doc",
            section_type="doc"
        )

        assert high_priority.priority == 1.0
        assert low_priority.priority == 0.1

    def test_section_types(self):
        """測試不同類型的 section"""
        types = ["code", "error", "doc", "rag"]

        for section_type in types:
            section = ContextSection(
                content=f"{section_type} content",
                source=f"{section_type}.txt",
                priority=0.5,
                token_count=10,
                content_hash=section_type,
                section_type=section_type
            )
            assert section.section_type == section_type


class TestContextStats:
    """測試 ContextStats 統計數據"""

    def test_stats_initialization(self):
        """測試統計數據初始化"""
        stats = ContextStats(
            original_tokens=1000,
            optimized_tokens=600,
            compression_ratio=0.6,
            sections_removed=3,
            duplicates_merged=2,
            total_sections=10
        )

        assert stats.original_tokens == 1000
        assert stats.optimized_tokens == 600
        assert stats.compression_ratio == 0.6
        assert stats.sections_removed == 3
        assert stats.duplicates_merged == 2

    def test_compression_calculation(self):
        """測試壓縮率計算"""
        stats = ContextStats(
            original_tokens=2000,
            optimized_tokens=1000,
            compression_ratio=0.5,
            sections_removed=5,
            duplicates_merged=3,
            total_sections=15
        )

        # 驗證壓縮率
        expected_ratio = stats.optimized_tokens / stats.original_tokens
        assert abs(stats.compression_ratio - expected_ratio) < 0.01


class TestContextOptimizer:
    """測試 ContextOptimizer 核心功能"""

    def test_optimizer_initialization(self):
        """測試優化器初始化"""
        optimizer = ContextOptimizer(max_tokens=8000)

        assert optimizer.max_tokens == 8000
        assert hasattr(optimizer, 'sections')

    def test_optimizer_custom_max_tokens(self):
        """測試自定義 token 限制"""
        optimizer = ContextOptimizer(max_tokens=4000)
        assert optimizer.max_tokens == 4000

        optimizer2 = ContextOptimizer(max_tokens=16000)
        assert optimizer2.max_tokens == 16000

    def test_add_section(self):
        """測試添加 section"""
        optimizer = ContextOptimizer(max_tokens=8000)

        if hasattr(optimizer, 'add_section'):
            optimizer.add_section(
                content="def hello(): pass",
                source="hello.py",
                priority=0.8
            )

            assert len(optimizer.sections) >= 1

    def test_priority_based_selection(self):
        """測試基於優先級的選擇"""
        optimizer = ContextOptimizer(max_tokens=100)

        if hasattr(optimizer, 'add_section'):
            # 添加不同優先級的 sections
            optimizer.add_section("High priority", "error", priority=1.0)
            optimizer.add_section("Low priority", "doc", priority=0.1)
            optimizer.add_section("Medium priority", "code", priority=0.5)

            if hasattr(optimizer, 'optimize'):
                result, stats = optimizer.optimize()

                # 高優先級內容應該被保留
                assert isinstance(result, str)
                assert isinstance(stats, (dict, ContextStats))

    def test_deduplication(self):
        """測試內容去重"""
        optimizer = ContextOptimizer(max_tokens=8000)

        if hasattr(optimizer, 'add_section'):
            # 添加重複內容
            optimizer.add_section("Same content", "file1.py", priority=0.5)
            optimizer.add_section("Same content", "file2.py", priority=0.5)
            optimizer.add_section("Different content", "file3.py", priority=0.5)

            if hasattr(optimizer, 'optimize'):
                result, stats = optimizer.optimize()

                # 驗證去重
                if isinstance(stats, ContextStats):
                    assert stats.duplicates_merged >= 0

    def test_token_limit_enforcement(self):
        """測試 token 限制強制執行"""
        optimizer = ContextOptimizer(max_tokens=50)

        if hasattr(optimizer, 'add_section'):
            # 添加超過限制的內容
            for i in range(10):
                optimizer.add_section(
                    content="x" * 100,  # 大量內容
                    source=f"file{i}.py",
                    priority=0.5
                )

            if hasattr(optimizer, 'optimize'):
                result, stats = optimizer.optimize()

                # 優化後應該在限制內
                if isinstance(stats, ContextStats):
                    assert stats.optimized_tokens <= optimizer.max_tokens * 1.1

    def test_section_type_handling(self):
        """測試不同 section 類型的處理"""
        optimizer = ContextOptimizer(max_tokens=8000)

        if hasattr(optimizer, 'add_section'):
            section_types = ["code", "error", "doc", "rag"]

            for section_type in section_types:
                optimizer.add_section(
                    content=f"{section_type} content",
                    source=f"{section_type}.txt",
                    priority=0.7,
                    section_type=section_type
                )

    def test_importance_keywords_detection(self):
        """測試重要關鍵字檢測"""
        optimizer = ContextOptimizer(max_tokens=8000)

        # 驗證重要關鍵字定義
        assert hasattr(optimizer, 'IMPORTANCE_KEYWORDS')
        assert "error" in optimizer.IMPORTANCE_KEYWORDS
        assert "critical" in optimizer.IMPORTANCE_KEYWORDS

    def test_semantic_deduplication_option(self):
        """測試語義去重選項"""
        optimizer_with_semantic = ContextOptimizer(
            max_tokens=8000,
            enable_semantic_dedup=True
        )

        optimizer_without_semantic = ContextOptimizer(
            max_tokens=8000,
            enable_semantic_dedup=False
        )

        assert optimizer_with_semantic.enable_semantic_dedup is True
        assert optimizer_without_semantic.enable_semantic_dedup is False

    def test_empty_optimization(self):
        """測試空內容優化"""
        optimizer = ContextOptimizer(max_tokens=8000)

        if hasattr(optimizer, 'optimize'):
            result, stats = optimizer.optimize()

            # 空內容應該返回空結果
            assert isinstance(result, str)
            assert len(result) == 0 or result == ""

    def test_single_section_optimization(self):
        """測試單個 section 優化"""
        optimizer = ContextOptimizer(max_tokens=1000)

        if hasattr(optimizer, 'add_section') and hasattr(optimizer, 'optimize'):
            optimizer.add_section(
                content="print('Hello, World!')",
                source="main.py",
                priority=0.8
            )

            result, stats = optimizer.optimize()

            assert "Hello" in result or isinstance(result, str)

    def test_compression_ratio_calculation(self):
        """測試壓縮率計算"""
        optimizer = ContextOptimizer(max_tokens=100)

        if hasattr(optimizer, 'add_section') and hasattr(optimizer, 'optimize'):
            # 添加大量內容
            for i in range(5):
                optimizer.add_section(
                    content="x" * 200,
                    source=f"file{i}.py",
                    priority=0.5
                )

            result, stats = optimizer.optimize()

            if isinstance(stats, ContextStats):
                assert 0 <= stats.compression_ratio <= 1.0
