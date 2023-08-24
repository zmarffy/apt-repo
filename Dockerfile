FROM zmarffy/pybuilder:lite-3.11 AS builder

COPY . /workspace/
WORKDIR /workspace
RUN poetry build

FROM python:3.11

COPY --from=builder /workspace/dist/*.whl /workspace/
RUN pip install /workspace/*.whl

ENV GH_TOKEN=
ENV GIT_USERNAME=
ENV GIT_EMAIL=

COPY entrypoint.sh .

RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
RUN echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive \
    apt-get install --no-install-recommends -y \
    reprepro \
    gh \
    && rm -rf /var/lib/apt/lists/*

ENTRYPOINT [ "sh", "/entrypoint.sh", "apt-repo" ]
