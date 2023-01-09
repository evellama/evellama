# Builder stage
FROM ruby:3.1-alpine as builder

RUN apk add --no-cache \
      build-base \
      curl-dev \
      file \
      git \
      libc6-compat \
      nodejs \
      postgresql-dev \
      tzdata \
      yarn

WORKDIR /app

COPY ./package.json ./yarn.lock /app/
RUN yarn install --frozen-lockfile

COPY ./Gemfile* /app/
RUN gem install bundler -v 2.4.1 && gem cleanup bundler
RUN bundle config --local frozen 1 && \
    bundle install -j4 --retry 3

ONBUILD COPY Gemfile* /app/
ONBUILD RUN bundle config --local without 'development test' && \
            bundle install -j4 --retry 3 && \
            bundle clean --force && \
            rm -rf /usr/local/bundle/cache/*.gem && \
            find /usr/local/bundle/gems/ -name "*.c" -delete && \
            find /usr/local/bundle/gems/ -name "*.o" -delete

ONBUILD COPY . /app

ONBUILD RUN bin/rails assets:precompile RAILS_ENV=production SECRET_KEY_BASE=dummy

ONBUILD RUN rm -rf node_modules tmp/cache vendor/bundle test spec app/javascript app/packs


# Base stage
FROM ruby:3.1-alpine AS base

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


# Production stage
FROM builder
FROM base

COPY --from=builder /etc/alpine-release /tmp/dummy

USER app

CMD ["bundle", "exec", "rails", "console"]
