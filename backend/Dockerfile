FROM ghcr.io/evellama/evellama-backend-builder:edge AS builder
FROM ghcr.io/evellama/evellama-backend-base:edge AS base

COPY --from=builder /etc/alpine-release /tmp/dummy

USER app

CMD ["bundle", "exec", "rails", "console"]