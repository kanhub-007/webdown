"""Shared helper for launching background markdown-generation jobs.

Extracted from the three "start job" use cases that all follow the identical
pattern: generate UUID, create job, submit to background processor.
"""

import uuid
from collections.abc import Callable
from typing import Any

from webdown.core.application.dto.job_result import JobResult
from webdown.core.domain.interfaces.background_processor import BackgroundProcessor
from webdown.core.domain.interfaces.markdown_job_repository import MarkdownJobRepository


def launch_background_job(
    job_repository: MarkdownJobRepository,
    background_processor: BackgroundProcessor,
    generation_func: Callable[..., Any],
    total_pages: int,
    *args: Any,
    **kwargs: Any,
) -> JobResult:
    """Create and schedule a background markdown generation job.

    Args:
        job_repository: Repository for persisting job progress.
        background_processor: Processor that will execute the work.
        generation_func: The generation use case's ``execute`` method.
        total_pages: Estimated page count for the job.
        *args: Positional args forwarded to ``generation_func``.
        **kwargs: Keyword args forwarded to ``generation_func``.

    Returns:
        JobResult with the generated job_id.
    """
    job_id = str(uuid.uuid4())
    job_repository.create_job(job_id, total_pages)
    background_processor.submit(generation_func, job_id, *args, **kwargs)
    return JobResult(job_id=job_id)
