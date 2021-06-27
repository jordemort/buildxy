FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install --no-install-recommends --yes \
      apt-transport-https \
      ca-certificates \
      curl \
      dumb-init \
      git \
      gnupg \
      lsb-release \
      python3 && \
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg && \
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list  && \
    apt-get update && \
    apt-get install --no-install-recommends --yes docker-ce-cli && \
    apt-get clean && \
    curl -LO https://storage.googleapis.com/container-diff/latest/container-diff-linux-amd64 && \
    chmod +x container-diff-linux-amd64 && \
    mv container-diff-linux-amd64 /usr/local/bin/container-diff

COPY buildxy.py /usr/local/bin/buildxy

ENTRYPOINT [ "/usr/bin/dumb-init", "/usr/local/bin/buildxy" ]
