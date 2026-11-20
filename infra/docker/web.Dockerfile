FROM node:24-slim AS build
RUN corepack enable
WORKDIR /src
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml tsconfig.base.json ./
COPY apps/panel/package.json apps/panel/
RUN pnpm install --frozen-lockfile --filter @clarity-compass/panel
COPY apps/panel apps/panel
RUN pnpm --filter @clarity-compass/panel build

FROM nginx:1.27-alpine
COPY infra/nginx/default.conf /etc/nginx/conf.d/default.conf
COPY --from=build /src/apps/panel/dist /usr/share/nginx/html
