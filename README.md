# api-management-utils
Scripts and utilities used across API managment platform and services 


##Python upgrade to 3.13
Utils Repo has been updated to python 3.13

We are continuing to support python 3.8/9(which are currently out of support) until January 26th 2026
After the deadline your pipelines will fail if you are using python version 3.8/9

##Python upgrade related changes
Projects using Python versions older than 3.13 and extending their pipeline with the utils repository must update their pipelines to ensure compatibility with the latest changes.
For detailed guidance, please refer to the APIM FAQ page:
https://nhsd-confluence.digital.nhs.uk/spaces/APM/pages/1226682275/Pipeline+Queries

Note: Projects running Python version 3.13 or later do not need any pipeline modifications.



## Scripts
* `template.py` - cli for basic jinja templating
* `test_pull_request_deployments.py` - cli for testing utils against other repositories
    * Environment Variables:
        * `AZURE_TOKEN` - Azure Devops token.
        * `NOTIFY_COMMIT_SHA` - Git Commit SHA that you want to report to.
        * `UTILS_PR_NUMBER` - The utils pull request number e.g. '123'
