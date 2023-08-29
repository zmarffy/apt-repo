FROM zmarffy/pybuilder:3.11 AS downloader

WORKDIR /workspace/deps
RUN curl -Ls "$(curl -s https://api.github.com/repos/cli/cli/releases | jq -r --arg arch "$(dpkg --print-architecture)" '.[0].assets[] | select(.name | endswith("_linux_\($arch).deb")) | .browser_download_url')" -o pkg0.deb

FROM python:3.11 as base
LABEL maintainer="zmarffy@yahoo.com"

ENV GH_TOKEN=
ENV SET_UP_GITCONFIG=1
ENV GIT_USERNAME=
ENV GIT_EMAIL=

COPY --from=downloader /workspace/deps/* /workspace/

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive \
    apt-get install --no-install-recommends -y \
    reprepro \
    && rm -rf /var/lib/apt/lists/*
RUN dpkg -i /workspace/*.deb \
    && rm -rf /workspace/*.deb

COPY entrypoint.sh .

FROM zmarffy/pybuilder:3.11 AS dev_image
RUN poetry config virtualenvs.create false
WORKDIR /src
COPY . /src/

FROM zmarffy/pybuilder:3.11 AS builder
WORKDIR /workspace
COPY . /workspace/
RUN poetry build --format wheel

FROM base AS image
COPY --from=builder /workspace/dist/*.whl /workspace/
RUN pip install /workspace/*.whl \
    && rm -rf /workspace/*.whl

ENTRYPOINT [ "sh", "/entrypoint.sh", "apt-repo" ]
