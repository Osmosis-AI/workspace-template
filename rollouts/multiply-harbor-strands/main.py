"""Harbor-backed Strands multiply rollout server."""

from __future__ import annotations

import logging
import os
from pathlib import Path

import uvicorn
from harbor.models.environment_type import EnvironmentType
from harbor.models.trial.config import EnvironmentConfig as HarborEnvironmentConfig
from harbor.trial.queue import TrialQueue
from multiply_rollout.grader import MultiplyGrader, multiply_grader_config
from multiply_rollout.workflow import MultiplyWorkflow, multiply_workflow_config
from osmosis_ai.rollout.backend.harbor import HarborBackend
from osmosis_ai.rollout.server import create_rollout_server

logger = logging.getLogger(__name__)
ROLLOUT_DIR = Path(__file__).resolve().parent
# Platform rollout servers export managed sandbox credentials, OpenSandbox
# first; local `osmosis eval run` without any uses the host Docker runtime.
if os.environ.get("OPENSANDBOX_API_KEY"):
    ENVIRONMENT_TYPE = EnvironmentType.OPENSANDBOX
elif os.environ.get("DAYTONA_API_KEY"):
    ENVIRONMENT_TYPE = EnvironmentType.DAYTONA
else:
    ENVIRONMENT_TYPE = EnvironmentType.DOCKER
CONCURRENT_TRIALS = 8


def main() -> None:
    orchestrator = TrialQueue(n_concurrent=CONCURRENT_TRIALS)
    backend = HarborBackend(
        orchestrator=orchestrator,
        tasks_dir=ROLLOUT_DIR / "multiply_harbor_task",
        task_mode="template",
        agent=MultiplyWorkflow,
        workflow_config=multiply_workflow_config,
        grader=MultiplyGrader,
        grader_config=multiply_grader_config,
        code_dir=ROLLOUT_DIR,
        environment_config=HarborEnvironmentConfig(type=ENVIRONMENT_TYPE),
        cleanup_successful_trials=True,
    )

    app = create_rollout_server(
        backend=backend,
        lifespan=backend.prewarm_lifespan(),
    )
    port = int(os.environ.get("_OSMOSIS_ROLLOUT_PORT", "8000"))
    logger.info(
        "Harbor rollout server starting on http://0.0.0.0:%d (environment=%s)",
        port,
        ENVIRONMENT_TYPE.value,
    )
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
