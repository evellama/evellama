# frozen_string_literal: true

class CreateAhoyVisitsAndEvents < ActiveRecord::Migration[7.0]
  def change
    create_table :ahoy_visits do |t| # rubocop:disable Rails/CreateTableWithTimestamps
      t.text :browser
      t.text :device_type
      t.text :ip
      t.text :landing_page
      t.text :os
      t.text :referrer
      t.text :referring_domain
      t.datetime :started_at
      t.text :user_agent
      t.text :utm_campaign
      t.text :utm_content
      t.text :utm_medium
      t.text :utm_source
      t.text :utm_term
      t.text :visit_token, index: { name: :ahoy_visits_visit_token_key, unique: true }
      t.text :visitor_token
    end

    create_table :ahoy_events do |t| # rubocop:disable Rails/CreateTableWithTimestamps
      t.references :visit, index: { name: :ahoy_events_visit_id_idx }
      t.references :user, index: { name: :ahoy_events_user_id_idx }

      t.text :name
      t.jsonb :properties, index: { name: :ahoy_events_properties_idx, using: :gin, opclass: :jsonb_path_ops }
      t.datetime :time

      t.index %i[name time], name: :ahoy_events_name_time_idx
    end
  end
end
