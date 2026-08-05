ARG VARIANT="3.13-bookworm"
FROM mcr.microsoft.com/devcontainers/python:${VARIANT}

USER root

# Keep the image small while ensuring Git hooks and setup scripts have the
# command-line tools they need. Python is supplied by the devcontainers base image.
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        bash-completion \
        git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER vscode
