"""Pipeline package initialization and exports."""

from app.pipeline.dispatcher import dispatch_campaign
from app.pipeline.models import PipelineResult
from app.pipeline.orchestrator import PipelineOrchestrator

__all__ = [
    "dispatch_campaign",
    "PipelineResult",
    "PipelineOrchestrator",
]
