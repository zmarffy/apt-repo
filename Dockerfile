FROM python:3.11 as base
LABEL maintainer="zmarffy@yahoo.com"

ENV GH_TOKEN=

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive \
    apt-get install --no-install-recommends -y \
    reprepro \
    && rm -rf /var/lib/apt/lists/*

FROM zmarffy/pybuilder:3.11 AS builder
WORKDIR /workspace
COPY . /workspace/
RUN poetry build --format wheel

FROM base AS image
COPY --from=builder /workspace/dist/*.whl /workspace/
RUN pip install /workspace/*.whl \
    && rm -rf /workspace/*.whl

WORKDIR /workspace

ENTRYPOINT [ "sh", "apt-repo" ]
