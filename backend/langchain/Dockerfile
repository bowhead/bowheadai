FROM node:lts-alpine

RUN apk update && apk upgrade && apk add --no-cache bash git openssh python3 make g++

USER node
WORKDIR /api

CMD ["bash", "./start.sh"]