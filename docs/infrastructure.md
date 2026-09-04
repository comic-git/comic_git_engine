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
- move `latest` and the affected moving minor branch/tag back to the known-good release when an immediate rollback is necessary
- publish a new patch release for the correction
- direct exactly pinned users to another exact release; never move an exact version branch or tag

One important wrinkle:

- reusable-workflow and engine revisions are independent selectors
- `v1` is frozen at the 1.0 workflow contract, while 1.1 consumers normally follow the moving `v1.1` workflow tag

That means rollback needs to account for both selectors. Moving workflow tags and engine branches can be repointed, but exact references remain immutable. Major tags are changed only through a deliberate manual operation, never through normal release automation.

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
