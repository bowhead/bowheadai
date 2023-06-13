ARG USER_TYPE node
ARG USER_ID 1001

FROM node:lts-alpine AS base
RUN apk update && apk upgrade && apk add --no-cache bash git openssh python3 make g++

FROM base AS user-node
USER node

FROM base AS user-other
ARG USER_ID
RUN adduser -D --uid $USER_ID --shell /bin/bash api && mkdir -p /api && chown api:api /api
USER api

FROM user-${USER_TYPE} AS final
WORKDIR /api
CMD ["bash", "./start.sh"]  