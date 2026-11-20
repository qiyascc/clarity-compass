FROM golang:1.26 AS build
ARG SMOKESCREEN_REF=530ed8cba3e66d0041b23be5e494b871a3702ca7
RUN CGO_ENABLED=0 GOBIN=/out go install github.com/stripe/smokescreen/v2@${SMOKESCREEN_REF}

FROM gcr.io/distroless/static:nonroot
COPY --from=build /out/smokescreen /smokescreen
COPY infra/smokescreen/config.yaml /etc/smokescreen/config.yaml
USER 65532:65532
EXPOSE 4750
ENTRYPOINT ["/smokescreen", "--config-file", "/etc/smokescreen/config.yaml"]
