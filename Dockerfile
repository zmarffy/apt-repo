FROM python:3.11 as base
LABEL maintainer="zmarffy@yahoo.com"

ENV GH_TOKEN=
ENV SET_UP_GITCONFIG=1
ENV GIT_USERNAME=
ENV GIT_EMAIL=

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive \
    apt-get install --no-install-recommends -y \
    reprepro \
    && rm -rf /var/lib/apt/lists/*

COPY entrypoint.sh .

FROM base AS dev_image
RUN pip install --no-cache poetry
RUN poetry self add \
    "poetry-dynamic-versioning[plugin]" \
    "poethepoet[poetry_plugin]"
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
