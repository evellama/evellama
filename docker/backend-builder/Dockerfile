FROM ruby:3.1-alpine

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

COPY ./backend/package.json ./backend/yarn.lock /app/
RUN yarn install --frozen-lockfile

COPY ./backend/Gemfile* /app/
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
