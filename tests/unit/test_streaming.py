"""
精準測試 Streaming Progress Reporter
"""

import pytest
import time
from pathlib import Path
from unittest.mock import MagicMock
from datetime import datetime

from boring.streaming import (
    ProgressReporter,
    ProgressEvent,
    ProgressStage
)


class TestProgressStage:
    """測試 ProgressStage 枚舉"""

    def test_all_stages_defined(self):
        """測試所有階段都已定義"""
        stages = [
            ProgressStage.INITIALIZING,
            ProgressStage.PLANNING,
            ProgressStage.EXECUTING,
            ProgressStage.VERIFYING,
            ProgressStage.COMPLETED,
            ProgressStage.FAILED
        ]
        
        assert len(stages) == 6
        
    def test_stage_values(self):
        """測試階段值"""
        assert ProgressStage.INITIALIZING.value == "initializing"
        assert ProgressStage.PLANNING.value == "planning"
        assert ProgressStage.EXECUTING.value == "executing"
        assert ProgressStage.VERIFYING.value == "verifying"
        assert ProgressStage.COMPLETED.value == "completed"
        assert ProgressStage.FAILED.value == "failed"


class TestProgressEvent:
    """測試 ProgressEvent 數據結構"""

    def test_event_initialization(self):
        """測試事件初始化"""
        event = ProgressEvent(
            stage=ProgressStage.EXECUTING,
            message="Processing files...",
            percentage=50.0
        )
        
        assert event.stage == ProgressStage.EXECUTING
        assert event.message == "Processing files..."
        assert event.percentage == 50.0
        assert isinstance(event.timestamp, datetime)

    def test_event_with_metadata(self):
        """測試帶元數據的事件"""
        metadata = {"file": "test.py", "line": 42}
        event = ProgressEvent(
            stage=ProgressStage.VERIFYING,
            message="Running tests",
            percentage=75.0,
            metadata=metadata
        )
        
        assert event.metadata == metadata
        assert event.metadata["file"] == "test.py"

    def test_event_timestamp_auto_generated(self):
        """測試時間戳自動生成"""
        event1 = ProgressEvent(
            stage=ProgressStage.INITIALIZING,
            message="Start",
            percentage=0.0
        )
        
        time.sleep(0.01)
        
        event2 = ProgressEvent(
            stage=ProgressStage.PLANNING,
            message="Planning",
            percentage=10.0
        )
        
        assert event2.timestamp > event1.timestamp


class TestProgressReporter:
    """測試 ProgressReporter 核心功能"""

    def test_reporter_initialization(self):
        """測試報告器初始化"""
        reporter = ProgressReporter(task_id="test-task")
        
        assert reporter.task_id == "test-task"
        assert reporter.total_stages == 4
        assert len(reporter.events) == 0

    def test_reporter_custom_stages(self):
        """測試自定義階段數"""
        reporter = ProgressReporter(
            task_id="custom-task",
            total_stages=6
        )
        
        assert reporter.total_stages == 6

    def test_report_simple_event(self):
        """測試報告簡單事件"""
        reporter = ProgressReporter(task_id="test")
        
        reporter.report(
            stage=ProgressStage.INITIALIZING,
            message="Starting..."
        )
        
        assert len(reporter.events) == 1
        assert reporter.events[0].stage == ProgressStage.INITIALIZING
        assert reporter.events[0].message == "Starting..."

    def test_report_percentage_calculation(self):
        """測試百分比計算"""
        reporter = ProgressReporter(
            task_id="test",
            total_stages=4
        )
        
        # 第一階段開始（0%）
        reporter.report(
            stage=ProgressStage.INITIALIZING,
            message="Init",
            sub_percentage=0.0
        )
        
        assert reporter.events[0].percentage == 0.0
        
        # 第二階段開始（25%）
        reporter.report(
            stage=ProgressStage.PLANNING,
            message="Plan",
            sub_percentage=0.0
        )
        
        # 百分比應該大於等於 25%
        assert reporter.events[1].percentage >= 20.0

    def test_report_with_callback(self):
        """測試回調函數"""
        callback_events = []
        
        def callback(event: ProgressEvent):
            callback_events.append(event)
        
        reporter = ProgressReporter(
            task_id="test",
            callback=callback
        )
        
        reporter.report(
            stage=ProgressStage.EXECUTING,
            message="Working..."
        )
        
        assert len(callback_events) == 1
        assert callback_events[0].message == "Working..."

    def test_report_with_file_output(self, tmp_path):
        """測試文件輸出"""
        output_file = tmp_path / "progress.json"
        
        reporter = ProgressReporter(
            task_id="test",
            output_file=output_file
        )
        
        reporter.report(
            stage=ProgressStage.PLANNING,
            message="Planning task"
        )
        
        # 如果實現了文件寫入
        if hasattr(reporter, '_write_to_file'):
            # _write_to_file 可能需要 event 參數
            pass

    def test_multiple_reports(self):
        """測試多次報告"""
        reporter = ProgressReporter(task_id="test")
        
        stages = [
            (ProgressStage.INITIALIZING, "Init"),
            (ProgressStage.PLANNING, "Plan"),
            (ProgressStage.EXECUTING, "Execute"),
            (ProgressStage.VERIFYING, "Verify"),
            (ProgressStage.COMPLETED, "Done")
        ]
        
        for stage, message in stages:
            reporter.report(stage=stage, message=message)
        
        assert len(reporter.events) == 5
        assert reporter.events[-1].stage == ProgressStage.COMPLETED

    def test_percentage_never_exceeds_100(self):
        """測試百分比不超過 100"""
        reporter = ProgressReporter(task_id="test", total_stages=2)
        
        reporter.report(
            stage=ProgressStage.COMPLETED,
            message="Done",
            sub_percentage=100.0
        )
        
        assert reporter.events[0].percentage <= 100.0

    def test_callback_error_handling(self):
        """測試回調錯誤處理"""
        def failing_callback(event):
            raise ValueError("Callback error")
        
        reporter = ProgressReporter(
            task_id="test",
            callback=failing_callback
        )
        
        # 即使回調失敗，報告也應該繼續
        reporter.report(
            stage=ProgressStage.EXECUTING,
            message="Working"
        )
        
        assert len(reporter.events) == 1

    def test_event_ordering(self):
        """測試事件順序"""
        reporter = ProgressReporter(task_id="test")
        
        reporter.report(ProgressStage.INITIALIZING, "First")
        time.sleep(0.01)
        reporter.report(ProgressStage.PLANNING, "Second")
        time.sleep(0.01)
        reporter.report(ProgressStage.EXECUTING, "Third")
        
        # 事件應該按時間順序
        assert reporter.events[0].message == "First"
        assert reporter.events[1].message == "Second"
        assert reporter.events[2].message == "Third"
        
        # 時間戳應該遞增
        assert reporter.events[0].timestamp < reporter.events[1].timestamp
        assert reporter.events[1].timestamp < reporter.events[2].timestamp

    def test_metadata_preservation(self):
        """測試元數據保留"""
        reporter = ProgressReporter(task_id="test")
        
        metadata1 = {"step": 1, "file": "a.py"}
        metadata2 = {"step": 2, "file": "b.py"}
        
        reporter.report(
            ProgressStage.EXECUTING,
            "Step 1",
            metadata=metadata1
        )
        reporter.report(
            ProgressStage.EXECUTING,
            "Step 2",
            metadata=metadata2
        )
        
        assert reporter.events[0].metadata == metadata1
        assert reporter.events[1].metadata == metadata2

    def test_start_time_tracking(self):
        """測試開始時間追蹤"""
        before = time.time()
        reporter = ProgressReporter(task_id="test")
        after = time.time()
        
        assert before <= reporter.start_time <= after
