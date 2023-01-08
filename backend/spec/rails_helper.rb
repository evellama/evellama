# frozen_string_literal: true

require 'spec_helper'
ENV['RAILS_ENV'] ||= 'test'
require_relative '../config/environment'

require 'rspec/rails'
require 'shoulda-matchers'
require 'webmock/rspec'

Shoulda::Matchers.configure do |config|
  config.integrate do |with|
    with.test_framework :rspec
    with.library :rails
  end
end

WebMock.disable_net_connect!(allow_localhost: true)

begin
  ActiveRecord::Migration.maintain_test_schema!
rescue ActiveRecord::PendingMigrationError => e
  puts e.to_s.strip
  exit 1
end

Dir["#{__dir__}/support/shared_contexts/**/*.rb"].each { |f| require f }

FactoryBot.definition_file_paths = [Bundler.root.join('spec/factories')]
FactoryBot.find_definitions

RSpec.configure do |config|
  config.include ActiveSupport::Testing::TimeHelpers
  config.include FactoryBot::Syntax::Methods

  config.use_transactional_fixtures = true

  config.filter_rails_from_backtrace!
  config.infer_spec_type_from_file_location!

  config.before do
    WebMock.reset!

    FileUtils.rm_rf(ActiveStorage::Blob.service.root)
  end
end
