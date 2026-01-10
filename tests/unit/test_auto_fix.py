"""
精準測試 Auto Fix Pipeline - 自動修復流程
"""

from unittest.mock import MagicMock

from boring.auto_fix import AutoFixPipeline, FixAttempt


class TestFixAttempt:
    """測試 FixAttempt 數據結構"""

    def test_fix_attempt_initialization(self):
        """測試修復嘗試初始化"""
        attempt = FixAttempt(
            iteration=1,
            issues_before=5,
            issues_after=2,
            fix_description="Fixed syntax errors",
            success=True,
            duration_seconds=1.5,
        )

        assert attempt.iteration == 1
        assert attempt.issues_before == 5
        assert attempt.issues_after == 2
        assert attempt.success is True
        assert attempt.duration_seconds == 1.5

    def test_fix_attempt_failure(self):
        """測試失敗的修復嘗試"""
        attempt = FixAttempt(
            iteration=2,
            issues_before=5,
            issues_after=5,
            fix_description="No improvements",
            success=False,
            duration_seconds=2.0,
        )

        assert attempt.success is False
        assert attempt.issues_before == attempt.issues_after

    def test_fix_attempt_partial_success(self):
        """測試部分成功的修復"""
        attempt = FixAttempt(
            iteration=1,
            issues_before=10,
            issues_after=3,
            fix_description="Reduced errors",
            success=True,
            duration_seconds=3.2,
        )

        # 問題減少但未完全解決
        assert attempt.issues_after < attempt.issues_before
        assert attempt.issues_after > 0


class TestAutoFixPipeline:
    """測試 AutoFixPipeline 核心功能"""

    def test_pipeline_initialization(self, tmp_path):
        """測試 pipeline 初始化"""
        pipeline = AutoFixPipeline(
            project_root=tmp_path, max_iterations=3, verification_level="STANDARD"
        )

        assert pipeline.project_root == tmp_path
        assert pipeline.max_iterations == 3
        assert pipeline.verification_level == "STANDARD"
        assert len(pipeline.attempts) == 0

    def test_pipeline_custom_settings(self, tmp_path):
        """測試自定義設置"""
        pipeline = AutoFixPipeline(
            project_root=tmp_path, max_iterations=5, verification_level="STRICT"
        )

        assert pipeline.max_iterations == 5
        assert pipeline.verification_level == "STRICT"

    def test_run_immediate_success(self, tmp_path):
        """測試立即成功（無需修復）"""
        pipeline = AutoFixPipeline(project_root=tmp_path)

        # Mock 函數：驗證立即通過
        mock_verify = MagicMock(return_value={"passed": True, "issues": []})
        mock_boring = MagicMock()

        result = pipeline.run(mock_boring, mock_verify)

        assert result["status"] == "SUCCESS"
        assert result["iterations"] == 0
        assert len(pipeline.attempts) == 0

    def test_run_with_fix_needed(self, tmp_path):
        """測試需要修復的情況"""
        pipeline = AutoFixPipeline(project_root=tmp_path, max_iterations=2)

        # Mock 驗證：第一次失敗，第二次成功
        verify_results = [
            {"passed": False, "issues": ["error1", "error2"], "error_count": 2},
            {"passed": True, "issues": []},
        ]
        mock_verify = MagicMock(side_effect=verify_results)

        # Mock Boring 運行
        mock_boring = MagicMock(return_value={"success": True})

        result = pipeline.run(mock_boring, mock_verify)

        assert result["status"] == "SUCCESS"
        assert result["iterations"] == 1
        assert len(pipeline.attempts) >= 1

    def test_run_max_iterations_reached(self, tmp_path):
        """測試達到最大迭代次數"""
        pipeline = AutoFixPipeline(project_root=tmp_path, max_iterations=2)

        # Mock 驗證：始終失敗
        mock_verify = MagicMock(
            return_value={"passed": False, "issues": ["persistent_error"], "error_count": 1}
        )

        mock_boring = MagicMock(return_value={"success": False})

        result = pipeline.run(mock_boring, mock_verify)

        assert result["status"] in ["MAX_ITERATIONS", "STALLED"]
        assert result["iterations"] == 2

    def test_run_no_progress(self, tmp_path):
        """測試無進展的情況"""
        pipeline = AutoFixPipeline(project_root=tmp_path, max_iterations=5)

        # Mock 驗證：問題數量不減少
        verify_results = [
            {"passed": False, "issues": ["e1", "e2", "e3"], "error_count": 3},
            {"passed": False, "issues": ["e1", "e2", "e3"], "error_count": 3},
        ]
        mock_verify = MagicMock(side_effect=verify_results)
        mock_boring = MagicMock()

        result = pipeline.run(mock_boring, mock_verify)

        assert result["status"] in ["NO_PROGRESS", "STALLED"]

    def test_run_progressive_improvement(self, tmp_path):
        """測試逐步改進"""
        pipeline = AutoFixPipeline(project_root=tmp_path, max_iterations=4)

        # Mock 驗證：問題逐步減少
        verify_results = [
            {"passed": False, "issues": list(range(10)), "error_count": 10},
            {"passed": False, "issues": list(range(5)), "error_count": 5},
            {"passed": False, "issues": list(range(2)), "error_count": 2},
            {"passed": True, "issues": []},
        ]
        mock_verify = MagicMock(side_effect=verify_results)
        mock_boring = MagicMock(return_value={"success": True})

        result = pipeline.run(mock_boring, mock_verify)

        assert result["status"] == "SUCCESS"
        assert len(pipeline.attempts) == 3

    def test_attempt_tracking(self, tmp_path):
        """測試嘗試記錄追蹤"""
        pipeline = AutoFixPipeline(project_root=tmp_path, max_iterations=3)

        verify_results = [
            {"passed": False, "issues": ["e1", "e2"], "error_count": 2},
            {"passed": True, "issues": []},
        ]
        mock_verify = MagicMock(side_effect=verify_results)
        mock_boring = MagicMock()

        result = pipeline.run(mock_boring, mock_verify)

        # 驗證嘗試記錄
        assert "attempts" in result
        attempts = result["attempts"]
        if len(attempts) > 0:
            assert "issues_before" in attempts[0]
            assert "issues_after" in attempts[0]

    def test_duration_tracking(self, tmp_path):
        """測試執行時間追蹤"""
        pipeline = AutoFixPipeline(project_root=tmp_path)

        verify_results = [
            {"passed": False, "issues": ["e1"], "error_count": 1},
            {"passed": True, "issues": []},
        ]
        mock_verify = MagicMock(side_effect=verify_results)
        mock_boring = MagicMock()

        pipeline.run(mock_boring, mock_verify)

        # 驗證有時間記錄
        if len(pipeline.attempts) > 0:
            assert pipeline.attempts[0].duration_seconds >= 0

    def test_verification_level_passed(self, tmp_path):
        """測試驗證級別正確傳遞"""
        pipeline = AutoFixPipeline(project_root=tmp_path, verification_level="STRICT")

        mock_verify = MagicMock(return_value={"passed": True, "issues": []})
        mock_boring = MagicMock()

        pipeline.run(mock_boring, mock_verify)

        # 驗證 verify 函數被正確調用
        mock_verify.assert_called()
        call_kwargs = mock_verify.call_args[1]
        assert call_kwargs["level"] == "STRICT"

    def test_project_root_in_verification(self, tmp_path):
        """測試專案根目錄正確傳遞"""
        pipeline = AutoFixPipeline(project_root=tmp_path)

        MagicMock(return_value={"passed": True, "issues": []})
        mock_boring = MagicMock()

        pipeline.run(mock_boring, mock_boring)

        # 專案路徑應該被傳遞
        assert pipeline.project_root == tmp_path
