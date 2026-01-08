# Copyright 2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
Agent Protocol Module - V10.24

Structured inter-agent communication protocol.
Enables better collaboration between ArchitectAgent, CoderAgent, and ReviewerAgent.

Features:
1. Typed message passing between agents
2. Shared context management
3. Consensus mechanism for multi-agent decisions
4. Agent performance tracking
"""

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Types of inter-agent messages."""

    REQUEST = "request"
    RESPONSE = "response"
    BROADCAST = "broadcast"
    VOTE = "vote"
    CONSENSUS = "consensus"
    HANDOFF = "handoff"
    STATUS = "status"


class AgentRole(Enum):
    """Agent roles in the system."""

    ARCHITECT = "architect"
    CODER = "coder"
    REVIEWER = "reviewer"
    ORCHESTRATOR = "orchestrator"


@dataclass
class AgentMessage:
    """A message between agents."""

    message_id: str
    sender: AgentRole
    recipient: AgentRole  # or "all" for broadcast
    message_type: MessageType
    content: dict
    priority: int = 5  # 1=highest, 10=lowest
    requires_response: bool = False
    response_to: Optional[str] = None  # message_id being responded to
    created_at: str = ""
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.message_id:
            self.message_id = str(uuid.uuid4())[:8]
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


@dataclass
class SharedContext:
    """Shared context between all agents."""

    task_id: str
    task_description: str
    current_phase: str  # "planning", "coding", "review", "complete"
    files_modified: list[str] = field(default_factory=list)
    decisions: list[dict] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    agent_notes: dict[str, list[str]] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""


@dataclass
class VoteResult:
    """Result of a multi-agent vote."""

    topic: str
    options: list[str]
    votes: dict[str, str]  # agent -> vote
    winner: str
    confidence: float
    consensus_reached: bool


@dataclass
class AgentPerformance:
    """Performance metrics for an agent."""

    agent_role: AgentRole
    tasks_completed: int
    tasks_failed: int
    avg_response_time_ms: float
    success_rate: float
    last_active: str


class AgentProtocol:
    """
    Protocol for structured agent communication.

    Enables:
    - Type-safe message passing
    - Shared context management
    - Consensus voting
    - Performance tracking
    """

    def __init__(self, project_root: Path):
        """
        Initialize agent protocol.

        Args:
            project_root: Project root for persistence
        """
        self.project_root = Path(project_root)
        self.data_dir = self.project_root / ".boring_memory" / "agent_protocol"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self._message_queue: list[AgentMessage] = []
        self._shared_context: Optional[SharedContext] = None
        self._performance: dict[AgentRole, AgentPerformance] = {}
        self._votes: dict[str, dict] = {}  # topic -> votes

    # =========================================================================
    # Message Passing
    # =========================================================================

    def send_message(
        self,
        sender: AgentRole,
        recipient: AgentRole,
        message_type: MessageType,
        content: dict,
        priority: int = 5,
        requires_response: bool = False,
    ) -> str:
        """
        Send a message from one agent to another.

        Args:
            sender: Sending agent
            recipient: Receiving agent (or AgentRole.ORCHESTRATOR for broadcast)
            message_type: Type of message
            content: Message content
            priority: Message priority (1=highest)
            requires_response: Whether response is expected

        Returns:
            message_id for tracking
        """
        message = AgentMessage(
            message_id="",
            sender=sender,
            recipient=recipient,
            message_type=message_type,
            content=content,
            priority=priority,
            requires_response=requires_response,
        )

        self._message_queue.append(message)
        logger.debug(f"Message sent: {sender.value} -> {recipient.value}: {message_type.value}")

        return message.message_id

    def get_messages(
        self,
        recipient: AgentRole,
        message_type: Optional[MessageType] = None,
        unread_only: bool = True,
    ) -> list[AgentMessage]:
        """
        Get messages for an agent.

        Args:
            recipient: Agent to get messages for
            message_type: Filter by type (optional)
            unread_only: Only return unread messages

        Returns:
            List of messages
        """
        messages = [
            m
            for m in self._message_queue
            if m.recipient == recipient or m.message_type == MessageType.BROADCAST
        ]

        if message_type:
            messages = [m for m in messages if m.message_type == message_type]

        # Sort by priority
        messages.sort(key=lambda m: m.priority)

        return messages

    def respond_to_message(self, original_message_id: str, sender: AgentRole, content: dict) -> str:
        """
        Respond to a message.

        Args:
            original_message_id: ID of message being responded to
            sender: Responding agent
            content: Response content

        Returns:
            response message_id
        """
        # Find original message
        original = next(
            (m for m in self._message_queue if m.message_id == original_message_id), None
        )

        if not original:
            logger.warning(f"Original message not found: {original_message_id}")
            return ""

        response = AgentMessage(
            message_id="",
            sender=sender,
            recipient=original.sender,
            message_type=MessageType.RESPONSE,
            content=content,
            response_to=original_message_id,
        )

        self._message_queue.append(response)
        return response.message_id

    # =========================================================================
    # Shared Context
    # =========================================================================

    def create_shared_context(self, task_id: str, task_description: str) -> SharedContext:
        """
        Create a new shared context for a task.

        Args:
            task_id: Unique task identifier
            task_description: Description of the task

        Returns:
            New SharedContext
        """
        self._shared_context = SharedContext(
            task_id=task_id,
            task_description=task_description,
            current_phase="planning",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )

        self._save_context()
        return self._shared_context

    def get_shared_context(self) -> Optional[SharedContext]:
        """Get current shared context."""
        if self._shared_context is None:
            self._load_context()
        return self._shared_context

    def update_context(self, agent: AgentRole, updates: dict):
        """
        Update shared context.

        Args:
            agent: Agent making the update
            updates: Dictionary of updates
        """
        if self._shared_context is None:
            return

        if "phase" in updates:
            self._shared_context.current_phase = updates["phase"]

        if "files" in updates:
            self._shared_context.files_modified.extend(updates["files"])

        if "decision" in updates:
            self._shared_context.decisions.append(
                {
                    "agent": agent.value,
                    "decision": updates["decision"],
                    "timestamp": datetime.now().isoformat(),
                }
            )

        if "blocker" in updates:
            self._shared_context.blockers.append(updates["blocker"])

        if "note" in updates:
            if agent.value not in self._shared_context.agent_notes:
                self._shared_context.agent_notes[agent.value] = []
            self._shared_context.agent_notes[agent.value].append(updates["note"])

        self._shared_context.updated_at = datetime.now().isoformat()
        self._save_context()

    def _save_context(self):
        """Save context to disk."""
        if self._shared_context is None:
            return

        context_file = self.data_dir / "shared_context.json"
        try:
            with open(context_file, "w") as f:
                json.dump(
                    {
                        "task_id": self._shared_context.task_id,
                        "task_description": self._shared_context.task_description,
                        "current_phase": self._shared_context.current_phase,
                        "files_modified": self._shared_context.files_modified,
                        "decisions": self._shared_context.decisions,
                        "blockers": self._shared_context.blockers,
                        "agent_notes": self._shared_context.agent_notes,
                        "created_at": self._shared_context.created_at,
                        "updated_at": self._shared_context.updated_at,
                    },
                    f,
                    indent=2,
                )
        except Exception as e:
            logger.warning(f"Failed to save context: {e}")

    def _load_context(self):
        """Load context from disk."""
        context_file = self.data_dir / "shared_context.json"
        if not context_file.exists():
            return

        try:
            with open(context_file) as f:
                data = json.load(f)
                self._shared_context = SharedContext(**data)
        except Exception as e:
            logger.warning(f"Failed to load context: {e}")

    # =========================================================================
    # Consensus Mechanism
    # =========================================================================

    def start_vote(self, topic: str, options: list[str], required_voters: list[AgentRole]) -> str:
        """
        Start a vote on a topic.

        Args:
            topic: Topic to vote on
            options: Available options
            required_voters: Agents that must vote

        Returns:
            vote_id for tracking
        """
        vote_id = str(uuid.uuid4())[:8]

        self._votes[vote_id] = {
            "topic": topic,
            "options": options,
            "required_voters": [v.value for v in required_voters],
            "votes": {},
            "started_at": datetime.now().isoformat(),
            "status": "open",
        }

        # Broadcast vote request to all required voters
        for voter in required_voters:
            self.send_message(
                sender=AgentRole.ORCHESTRATOR,
                recipient=voter,
                message_type=MessageType.VOTE,
                content={"vote_id": vote_id, "topic": topic, "options": options},
                priority=2,
                requires_response=True,
            )

        return vote_id

    def cast_vote(self, vote_id: str, agent: AgentRole, choice: str) -> bool:
        """
        Cast a vote.

        Args:
            vote_id: ID of the vote
            agent: Voting agent
            choice: Selected option

        Returns:
            True if vote was recorded
        """
        if vote_id not in self._votes:
            return False

        vote = self._votes[vote_id]

        if vote["status"] != "open":
            return False

        if choice not in vote["options"]:
            return False

        vote["votes"][agent.value] = choice
        logger.debug(f"Vote recorded: {agent.value} -> {choice}")

        return True

    def get_vote_result(self, vote_id: str) -> Optional[VoteResult]:
        """
        Get result of a vote.

        Args:
            vote_id: ID of the vote

        Returns:
            VoteResult if voting is complete
        """
        if vote_id not in self._votes:
            return None

        vote = self._votes[vote_id]

        # Check if all required voters have voted
        all_voted = all(v in vote["votes"] for v in vote["required_voters"])

        if not all_voted:
            return None

        # Count votes
        vote_counts: dict[str, int] = {}
        for choice in vote["votes"].values():
            vote_counts[choice] = vote_counts.get(choice, 0) + 1

        # Find winner
        winner = max(vote_counts.items(), key=lambda x: x[1])
        total_votes = len(vote["votes"])

        # Calculate confidence (proportion of votes for winner)
        confidence = winner[1] / total_votes if total_votes > 0 else 0

        # Consensus if majority (>50%) voted the same
        consensus = confidence > 0.5

        vote["status"] = "closed"
        vote["winner"] = winner[0]

        return VoteResult(
            topic=vote["topic"],
            options=vote["options"],
            votes=vote["votes"],
            winner=winner[0],
            confidence=confidence,
            consensus_reached=consensus,
        )

    # =========================================================================
    # Performance Tracking
    # =========================================================================

    def record_task_completion(self, agent: AgentRole, success: bool, response_time_ms: float):
        """
        Record task completion for performance tracking.

        Args:
            agent: Agent that completed the task
            success: Whether task was successful
            response_time_ms: Time taken in milliseconds
        """
        if agent not in self._performance:
            self._performance[agent] = AgentPerformance(
                agent_role=agent,
                tasks_completed=0,
                tasks_failed=0,
                avg_response_time_ms=0,
                success_rate=0,
                last_active=datetime.now().isoformat(),
            )

        perf = self._performance[agent]
        total_tasks = perf.tasks_completed + perf.tasks_failed

        if success:
            perf.tasks_completed += 1
        else:
            perf.tasks_failed += 1

        # Update rolling average
        new_total = total_tasks + 1
        perf.avg_response_time_ms = (
            perf.avg_response_time_ms * total_tasks + response_time_ms
        ) / new_total

        perf.success_rate = perf.tasks_completed / new_total
        perf.last_active = datetime.now().isoformat()

    def get_agent_performance(self, agent: AgentRole) -> Optional[AgentPerformance]:
        """Get performance metrics for an agent."""
        return self._performance.get(agent)

    def get_all_performance(self) -> dict[AgentRole, AgentPerformance]:
        """Get performance metrics for all agents."""
        return self._performance.copy()


class AgentHandoff:
    """
    Manages handoffs between specialized agents.

    Supports:
    - Architect -> Coder: Plan complete, ready for implementation
    - Coder -> Reviewer: Implementation complete, ready for review
    - Reviewer -> Coder: Review feedback, needs changes
    - Reviewer -> Orchestrator: Review passed, task complete
    """

    @staticmethod
    def create_handoff(
        from_agent: AgentRole, to_agent: AgentRole, handoff_type: str, payload: dict, summary: str
    ) -> AgentMessage:
        """
        Create a handoff message.

        Args:
            from_agent: Sending agent
            to_agent: Receiving agent
            handoff_type: Type of handoff
            payload: Data being handed off
            summary: Brief summary of handoff

        Returns:
            AgentMessage for the handoff
        """
        return AgentMessage(
            message_id="",
            sender=from_agent,
            recipient=to_agent,
            message_type=MessageType.HANDOFF,
            content={"type": handoff_type, "summary": summary, "payload": payload},
            priority=1,  # Handoffs are high priority
            requires_response=True,
        )

    @staticmethod
    def architect_to_coder(plan: dict, files_to_modify: list[str]) -> AgentMessage:
        """Create handoff from Architect to Coder."""
        return AgentHandoff.create_handoff(
            from_agent=AgentRole.ARCHITECT,
            to_agent=AgentRole.CODER,
            handoff_type="plan_to_implement",
            payload={"plan": plan, "files": files_to_modify},
            summary=f"Implementation plan ready with {len(files_to_modify)} files to modify",
        )

    @staticmethod
    def coder_to_reviewer(changes: list[dict], test_results: Optional[dict] = None) -> AgentMessage:
        """Create handoff from Coder to Reviewer."""
        return AgentHandoff.create_handoff(
            from_agent=AgentRole.CODER,
            to_agent=AgentRole.REVIEWER,
            handoff_type="code_for_review",
            payload={"changes": changes, "test_results": test_results},
            summary=f"Code ready for review with {len(changes)} changes",
        )

    @staticmethod
    def reviewer_feedback(
        approved: bool, feedback: list[str], changes_required: list[dict]
    ) -> AgentMessage:
        """Create review feedback message."""
        if approved:
            return AgentHandoff.create_handoff(
                from_agent=AgentRole.REVIEWER,
                to_agent=AgentRole.ORCHESTRATOR,
                handoff_type="review_approved",
                payload={"approved": True, "feedback": feedback},
                summary="Code review passed",
            )
        else:
            return AgentHandoff.create_handoff(
                from_agent=AgentRole.REVIEWER,
                to_agent=AgentRole.CODER,
                handoff_type="review_changes_requested",
                payload={
                    "approved": False,
                    "feedback": feedback,
                    "changes_required": changes_required,
                },
                summary=f"Review requires {len(changes_required)} changes",
            )


# Singleton instance
_agent_protocol: Optional[AgentProtocol] = None


def get_agent_protocol(project_root: Path) -> AgentProtocol:
    """Get or create agent protocol singleton."""
    global _agent_protocol
    if _agent_protocol is None:
        _agent_protocol = AgentProtocol(project_root)
    return _agent_protocol
