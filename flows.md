# Flows to check:

## GitHub OAuth flow:

## GitHub App installation flow:
- User sets up GitHub App - creates the app, sets webhook secret, saves private key etc.
- User installs GitHub App into repository
- The 'installation' webhook payload is received by the app. The GitHub service handler manages the 'handle installation' event
  - TODO: make sure service handlers handle installation events, and call the service connection thing to create the new service connection.
- The app saves the installation as a 'service connection' so that next time we receive a webhook from that service, we can do stuff with it.
- We need to confirm with the user that the installation has been registered properly.

## Slack App installation flow:
- The user sets up Slack App - creates the app, sets webhook secret, saves private key etc.
- The user installs the Slack app into their Slack workspace.
- The 'installation' webhook payload is received by the app. The Slack service handler manages the 'handle installation' event
- The app saves the installation as a 'service connection' so that next time we receive a webhook from that service, we can do stuff with it.
- The user needs to connect the Slack 'service connection' to the GitHub 'service connection' (and specify repositories?) so that when we receive a Slack message, we can do something in the GitHub repository.
  - Maybe by default, all of the user's app installations talk to each other...
  - Think about different use cases here.
    - Workplace - one Slack workspace, one GitHub organization.
    - Individual side projects - one GitHub user's personal repositories.

This same thing ^ could apply to a Linear App integration installation.

## New GitHub issue flow (request to make some changes):
- User has already installed the GitHub app etc.
- User creates a new issue with a prompt for Aider. Because the issue is in the repo where the app is installed, it's easy to match the webhook payload to where we will clone the repo etc.
- The app receives the webhook payload. (API -> webhook router)
- The app turns the service payload into a standardised event. (GitHub API in GitHub service handler)
- The app adds the standardised event to the Celery background task queue.
- The app responds to the user's issue with a comment, saying it has been added to the queue. (GitHub API)
- In the Celery background task queue job:
  - The app uses the standardised event to pick the correct 'command' and args. (command selector module)
  - The app prepares the execution environment - sets up a Docker container with command dependencies, mounted volume with the repo working folder. (environment manager module)
  - The app executes the command in the Docker container. (environment manager)
  - The app uses Git to work out what changes have been made to the working directory. (result processor)
  - Commit + create PR
    - The app generates a meaningful commit message for the changes, with the original request, Aider command output, change diffs in the context. (result pocessor)
    - The app creates the commit, creates a new branch, and then pushes the branch to the Git repository remote. (pr creator module)
    - The app uses the GitHub API to create a new PR on that branch. (GitHub API)
    - The app updates the issue comment with a link to the new PR. (GitHub API)

## New Slack message flow (request asking question, no changes required):
- User has already installed the GitHub App and the Slack App. When installing the GitHub App, selected two repos (repo A, repo B). When installing the Slack App, connected to repo A.
- User uses the Slack app - sends a message asking a question about the code (how does this connect to this other thing).
- The app receives the webhook payload. (APi -> webhook router)
- The app turns the service payload into a standardised event. (Slack service handler)
- The app adds the standardised event to the Celery background task queue.
- The app responds to the user's Slack message, saying it has been added to the queue. (Slack API, in Slack service handler)
- In the Celery background task queue job:
  - The app uses the standardised event to pick the correct 'command' and args. (command selector module)
  - The app prepares the execution environment - sets up a Docker container with command dependencies, mounted volume with the repo working folder. (environment manager module)
  - The app executes the command in the Docker container. (environment manager)
  - The app uses Git to work out if / what changes have been made to the working directory. (result processor)
  - The command should not have made any changes to the repo, so we don't need to create a commit, branch, PR.
  - The app responds to the user's request in Slack (Slack API in Slack service handler).


