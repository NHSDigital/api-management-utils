import os
import sys
from multiprocessing import Process
from trigger_pipelines import AzureDevOps


PULL_REQUEST_PIPELINES = {
    "identity-service": {
        "build": 27,
        "pr": 54,
        "branch": "refs/heads/master"
    },
    "canary-api": {
        "build": 222,
        "pr": 223,
        "branch": "refs/heads/main"
    },
    "personal-demographics-service": {
        "build": 140,
        "pr": 144,
        "branch": "refs/heads/master"
    },
}


def trigger_pipelines(pipeline_ids: dict, service: str):
    azure_dev_ops = AzureDevOps()
    build_status = azure_dev_ops.run_pipeline(
        service=service,
        pipeline_type="build",
        pipeline_id=pipeline_ids["build"],
        pipeline_branch=pipeline_ids["branch"]
    )
    if build_status != "succeeded":
        sys.exit(1)
        return
    azure_dev_ops.run_pipeline(
        service=service,
        pipeline_type="pr",
        pipeline_id=pipeline_ids["pr"],
        pipeline_branch=pipeline_ids["branch"]
    )


def main():
    jobs = []
    for service, pipeline_ids in PULL_REQUEST_PIPELINES.items():
        process = Process(
            target=trigger_pipelines,
            args=(pipeline_ids, service,)
        )
        process.start()
        jobs.append(process)
    for process in jobs:
        process.join()
    # check return code of jobs and fail if there is a problem
    for process in jobs:
        if process.exitcode != 0:
            print("A job failed")
            # uncomment this line once authentication to azure is working
            # so the job fails if there is a problem with deployment actions
            # sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
