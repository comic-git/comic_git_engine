<!-- ai-agent-toolkit:managed version="1.0.0" -->
<!-- Audience: AI agents working on infrastructure or deployment, and developers.
     Purpose: Cloud setup, services, environments, and how the system is deployed.
     An AI agent making infrastructure changes should read this before touching any config. -->

# Infrastructure

This repo does not run a server application or own a traditional cloud stack. Its "infrastructure" is mostly the hosted automation and static-site deployment path around the engine.

## Environments

| Environment | Purpose                                                                                               | URL / access                                                               |
|-------------|-------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------|
| Development | Local development and manual testing, usually through a host `comic_git` repo such as `comic_git_dev` | Local filesystem plus optional `http://localhost:8000` via `dev_server.py` |
| Production  | End-user static site deployments built by host repos                                                  | Usually GitHub Pages; optionally Neocities                                 |

There is no formal staging environment for `comic_git_engine`.

`comic_git` can act as a rough reference for default-output readiness, but it should not be treated as a safe staging tier because users may create fresh repos from it at any time.

## Cloud Services

| Service        | Purpose                                                                                                |
|----------------|--------------------------------------------------------------------------------------------------------|
| GitHub Actions | Builds host repos with the reusable `build_site.yaml` workflow and runs this repo's release automation |
| GitHub Pages   | Primary deployment target for end-user static sites                                                    |
| Neocities      | Optional alternate deployment target for end-user static sites                                         |

## Deployment

- Deployment is triggered by: a host `comic_git` repo calling [`.github/workflows/build_site.yaml`](../.github/workflows/build_site.yaml)
- Deploy pipeline: [`.github/workflows/build_site.yaml`](../.github/workflows/build_site.yaml)
- Rollback procedure: manual

Rollback is currently a version-pointer problem, not an infrastructure rollback problem.

Typical engine rollback flow:

- identify the last known good engine version branch
- move the `latest` branch and the current major/minor branch back to that known good commit
- remove or stop pointing users at the bad version branch/tag as needed

One important wrinkle:

- the reusable workflow integration surface is also tracked through the `v1` tag for host repos that reference `uses: comic-git/comic_git_engine/.github/workflows/build_site.yaml@v1`

That means workflow-level rollback needs to account for both version branches and the reusable-workflow tag users may be pinned to.

## Infrastructure as Code

- IaC location: none
- How to apply changes: infrastructure changes are made by editing GitHub workflow files and release/version references, not by applying Terraform or similar IaC

## Networking

There is no service-to-service network topology owned by this repo.

Relevant network touchpoints are:

- GitHub Actions runners downloading dependencies and invoking the build
- optional HTTP fetches such as webring JSON endpoints during site generation
- static artifact deployment to GitHub Pages or Neocities through workflow steps

## Secrets Management

Secrets are provided through GitHub Actions by the calling host repo or this repo's release workflow.

Common examples:

- `SECRETS` input for build-time secret injection into the engine environment
- `NEOCITIES_API_TOKEN` for Neocities deployment
- standard GitHub token usage for release automation

Do not store secrets in this repo. Reference them through workflow inputs and GitHub Actions secrets.
