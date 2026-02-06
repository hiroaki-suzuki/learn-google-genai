ARG IMAGE_SHA=sha256:1ff44933cb99713fa9659597c1a89df6375805e33c3f839e95c85eb0f8a8bd8c

# mcr.microsoft.com/devcontainers/python:dev-3.14-trixie
FROM mcr.microsoft.com/devcontainers/python@${IMAGE_SHA}     

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
  locales \ 
  && sed -i '/ja_JP.UTF-8/s/^# //g' /etc/locale.gen \
  && locale-gen ja_JP.UTF-8 \ 
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

ENV LANG=ja_JP.UTF-8 
ENV LC_ALL=ja_JP.UTF-8

ARG YAZI_VERSION=26.1.22
RUN curl -fsSL "https://github.com/sxyazi/yazi/releases/download/v${YAZI_VERSION}/yazi-aarch64-unknown-linux-musl.zip" \
  -o /tmp/yazi.zip \
  && unzip -o /tmp/yazi.zip -d /tmp/yazi \
  && mv /tmp/yazi/yazi-aarch64-unknown-linux-musl/yazi /usr/local/bin/yazi \
  && chmod +x /usr/local/bin/yazi \
  && rm -rf /tmp/yazi /tmp/yazi.zip
