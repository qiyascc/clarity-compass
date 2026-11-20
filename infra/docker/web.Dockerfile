FROM node:24-slim AS build
RUN corepack enable
WORKDIR /src
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml tsconfig.base.json ./
COPY apps/panel/package.json apps/panel/
COPY apps/extension/package.json apps/extension/
RUN pnpm install --frozen-lockfile --filter @clarity-compass/panel --filter @clarity-compass/extension
COPY apps/panel apps/panel
COPY apps/extension apps/extension
RUN pnpm --filter @clarity-compass/panel build && pnpm --filter @clarity-compass/extension build

FROM alpine:3.22 AS package
RUN apk add --no-cache zip
COPY --from=build /src/apps/extension/dist /extension
RUN cd /extension && zip -qr /clarity-compass-extension.zip . -x '*.map'

FROM nginx:1.27-alpine
COPY infra/nginx/default.conf /etc/nginx/conf.d/default.conf
COPY --from=build /src/apps/panel/dist /usr/share/nginx/html
COPY --from=package /clarity-compass-extension.zip /usr/share/nginx/html/downloads/
