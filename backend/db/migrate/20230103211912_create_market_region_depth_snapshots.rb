# frozen_string_literal: true

class CreateMarketRegionDepthSnapshots < ActiveRecord::Migration[7.0]
  def change
    create_table :market_region_depth_snapshots, id: false, primary_key: %i[timestamp region_id type_id] do |t| # rubocop:disable Rails/CreateTableWithTimestamps
      t.references :region, null: false, index: false
      t.references :type, null: false, index: false

      t.jsonb :buy_levels, null: false
      t.jsonb :sell_levels, null: false
      t.timestamp :timestamp, null: false

      t.index %i[timestamp region_id type_id], unique: true, name: :market_region_depth_snapshots_key
    end

    reversible do |dir|
      dir.up do
        safety_assured do
          execute <<~SQL.squish
            SELECT create_hypertable('market_region_depth_snapshots', 'timestamp', 'region_id', 68, chunk_time_interval => INTERVAL '1 day');
          SQL

          execute <<~SQL.squish
            SELECT add_retention_policy('market_region_depth_snapshots', INTERVAL '5 weeks')
          SQL
        end
      end

      dir.down do # rubocop:disable Lint/EmptyBlock
      end
    end
  end
end
