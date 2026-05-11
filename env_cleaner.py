"""
env_cleaner.py

A tool for cleaning up apigee-envs

Usage:
  env_cleaner.py <apigee_org> <apigee_env> --access-token=<access_token> [--specs] [--proxies] [--products] [--sandbox-only] [--dry-run] [--min-age=<min_age>] [--undeploy-only] [--respect-prs]
  env_cleaner.py (-h | --help)

Options:
  -h --help                      Show this screen
  --access-token=<access_token>  Apigee access token to authorise requests
  --specs                        Prune specs
  --proxies                      Prune proxies
  --products                     Prune products
  --sandbox-only                 Only delete sandbox proxies
  --dry-run                      Print a listing of what will be deleted, but don't delete it.
  --undeploy-only                Don't delete any proxies, just undeploy them
  --min-age=<min_age>            (NOT IMPLEMENTED) Minimum age in seconds
  --respect-prs                  Don't undeploy if there's a PR open for it
"""

import re
import requests
from typing import Optional, Set
from docopt import docopt
from apigee_client import ApigeeClient

SPEC_MATCHER = re.compile("(personal-demographics|identity-service|hello-world)-.+")
PROXY_MATCHER = re.compile(
    "(personal-demographics|identity-service|hello-world)-internal-dev-.+"
)
PRODUCT_MATCHER = PROXY_MATCHER
SANDBOX_MATCHER = re.compile(".+-sandbox$")
SANDBOX_ANTIMATCHER = re.compile(".+-internal-qa-sandbox")

# Map of repository names to service names
REPO_NAMES = {
    "personal-demographics-service-api": "personal-demographics",
    "identity-service-api": "identity-service",
    "hello-world-api": "hello-world",
    "electronic-prescription-service-api": "electronic-prescriptions",
}


def canonicalize(name: str) -> str:
    return name.replace(" ", "-").replace("/", "-")


class GithubClient:
    def get_open_prs(self, env: str) -> Set[str]:
        """Returns names of open pull requests"""
        canonical_prs = set()
        for repo_name in REPO_NAMES.keys():
            prs = requests.get(
                f"https://api.github.com/repos/NHSDigital/{repo_name}/pulls"
            ).json()
            for pr in prs:
                branch = pr["head"]["ref"]
                service_name = REPO_NAMES[repo_name]
                canonical_name = canonicalize(f"{service_name}-{env}-{branch}")
                canonical_prs.add(canonical_name)
                canonical_prs.add(canonical_name + "-sandbox")

        return canonical_prs


def clean_specs(client: ApigeeClient, dry_run: bool = False):
    specs = client.list_specs()
    spec_names = [spec["name"] for spec in specs["contents"]]

    # Use the spec matcher to find specs that look like something we'd want to clean
    pr_specs = [spec for spec in spec_names if SPEC_MATCHER.match(spec)]

    for spec in pr_specs:
        print(f"DELETE SPEC {spec}")
        if not dry_run:
            client.delete_spec(spec)
            print(f"DELETED SPEC {spec}")


def clean_proxies(
    client: ApigeeClient,
    github_client: GithubClient,
    env: str,
    dry_run: bool = False,
    sandboxes_only: bool = False,
    undeploy_only: bool = False,
    respect_prs: bool = False,
):

    open_prs = set()
    if respect_prs:
        # Get open PRs, if there are any
        open_prs = github_client.get_open_prs(env)

    proxies = client.list_proxies()
    pr_proxies = [proxy for proxy in proxies if PROXY_MATCHER.match(proxy)]
    proxy_deployments = client.list_env_proxy_deployments(env)[
        "aPIProxy"
    ]  # This is not a typo, it's actually spelled like that in the response

    deployed_proxy_revisions = set()
    for deployment in proxy_deployments:
        for revision in deployment["revision"]:
            if revision["state"] == "deployed":
                deployed_proxy_revisions.add((deployment["name"], revision["name"]))

    if sandboxes_only:
        pr_proxies = [
            proxy
            for proxy in pr_proxies
            if SANDBOX_MATCHER.match(proxy) and not SANDBOX_ANTIMATCHER.match(proxy)
        ]

    if respect_prs:
        pr_proxies = [proxy for proxy in pr_proxies if proxy not in open_prs]

    for proxy in pr_proxies:
        proxy_info = client.get_proxy(proxy)
        for revision in proxy_info["revision"]:
            if (proxy, revision) in deployed_proxy_revisions:
                print(f"UNDEPLOY {proxy} REVISION {revision}")
                if not dry_run:
                    try:
                        client.undeploy_proxy_revision(env, proxy, revision)
                    except requests.exceptions.HTTPError:
                        print(
                            f"ERROR UNDEPLOYING {proxy} REVISION {revision}: may already be undeployed"
                        )

        if not undeploy_only:
            print(f"DELETE PROXY {proxy}")
            if not dry_run:
                client.delete_proxy(proxy)


def clean_products(client: ApigeeClient, dry_run: bool = False):
    products = client.list_products()
    pr_products = [product for product in products if PRODUCT_MATCHER.match(product)]

    for product in pr_products:
        print(f"DELETE PRODUCT {product}")
        if not dry_run:
            client.delete_product(product)


def clean_env(
    client: ApigeeClient,
    github_client: GithubClient,
    env: str,
    should_clean_specs: bool = False,
    should_clean_proxies: bool = False,
    should_clean_products: bool = False,
    sandboxes_only: bool = False,
    dry_run: bool = False,
    undeploy_only: bool = False,
    respect_prs: bool = False,
):
    if should_clean_specs:
        clean_specs(client, dry_run)

    if should_clean_proxies:
        clean_proxies(
            client,
            github_client,
            env,
            dry_run,
            sandboxes_only,
            undeploy_only,
            respect_prs,
        )

    if should_clean_products:
        clean_products(client, dry_run)


if __name__ == "__main__":
    args = docopt(__doc__)
    client = ApigeeClient(args["<apigee_org>"], access_token=args["--access-token"])
    github_client = GithubClient()
    clean_env(
        client,
        github_client,
        args["<apigee_env>"],
        should_clean_specs=args["--specs"],
        should_clean_proxies=args["--proxies"],
        should_clean_products=args["--products"],
        sandboxes_only=args["--sandbox-only"],
        dry_run=args["--dry-run"],
        undeploy_only=args["--undeploy-only"],
        respect_prs=args["--respect-prs"],
    )
