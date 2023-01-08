FROM ruby:3.1-alpine

RUN apk add --no-cache \
      libc6-compat \
      libcurl \
      postgresql-client \
      tzdata \
      file \
      yarn

ENV RAILS_ENV production
ENV RAILS_LOG_TO_STDOUT true
ENV RAILS_SERVE_STATIC_FILES true

WORKDIR /app

EXPOSE 3000

ONBUILD RUN addgroup -g 1000 -S app && \
            adduser -u 1000 -S app -G app

ONBUILD COPY --from=builder --chown=app:app /usr/local/bundle/ /usr/local/bundle/
ONBUILD COPY --from=builder --chown=app:app /app /app
