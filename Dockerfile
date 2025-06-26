FROM ubuntu:24.04

ARG VERSION=2.325.0

RUN apt-get update && \
    apt-get install -y curl tar sudo git libicu70 zstd vim jq && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /runner

RUN curl -o actions-runner-linux-x64-${VERSION}.tar.gz -L https://github.com/actions/runner/releases/download/v${VERSION}/actions-runner-linux-x64-${VERSION}.tar.gz && \
    tar xzf actions-runner-linux-x64-${VERSION}.tar.gz && \
    rm actions-runner-linux-x64-${VERSION}.tar.gz

COPY start.sh /runner/start.sh
RUN chmod +x /runner/start.sh
