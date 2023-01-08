# This file is auto-generated from the current state of the database. Instead
# of editing this file, please use the migrations feature of Active Record to
# incrementally modify your database, and then regenerate this schema definition.
#
# This file is the source Rails uses to define your schema when running `bin/rails
# db:schema:load`. When creating a new database, `bin/rails db:schema:load` tends to
# be faster and is potentially less error prone than running all of your
# migrations from scratch. Old migrations may fail to apply correctly if those
# migrations use external dependencies or application code.
#
# It's strongly recommended that you check this file into your version control system.

ActiveRecord::Schema[7.0].define(version: 2023_01_03_211912) do
  # These are extensions that must be enabled in order to support this database
  enable_extension "plpgsql"
  enable_extension "timescaledb"
  enable_extension "timescaledb_toolkit"

  # Custom types defined in this database.
  # Note that some types may not work with other database engines. Be careful if changing database.
  create_enum "esi_status", ["pending", "syncing", "sync_failed", "synced"]
  create_enum "market_order_side", ["buy", "sell"]

  create_table "ahoy_events", force: :cascade do |t|
    t.bigint "visit_id"
    t.bigint "user_id"
    t.text "name"
    t.jsonb "properties"
    t.datetime "time"
    t.index ["name", "time"], name: "ahoy_events_name_time_idx"
    t.index ["properties"], name: "ahoy_events_properties_idx", opclass: :jsonb_path_ops, using: :gin
    t.index ["user_id"], name: "ahoy_events_user_id_idx"
    t.index ["visit_id"], name: "ahoy_events_visit_id_idx"
  end

  create_table "ahoy_visits", force: :cascade do |t|
    t.text "browser"
    t.text "device_type"
    t.text "ip"
    t.text "landing_page"
    t.text "os"
    t.text "referrer"
    t.text "referring_domain"
    t.datetime "started_at"
    t.text "user_agent"
    t.text "utm_campaign"
    t.text "utm_content"
    t.text "utm_medium"
    t.text "utm_source"
    t.text "utm_term"
    t.text "visit_token"
    t.text "visitor_token"
    t.index ["visit_token"], name: "ahoy_visits_visit_token_key", unique: true
  end

  create_table "constellations", force: :cascade do |t|
    t.bigint "region_id", null: false
    t.text "name", null: false
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["region_id"], name: "constellations_region_id_idx"
  end

  create_table "corporations", force: :cascade do |t|
    t.text "name", null: false
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
  end

  create_table "market_region_depth_snapshots", id: false, force: :cascade do |t|
    t.bigint "region_id", null: false
    t.bigint "type_id", null: false
    t.jsonb "buy_levels", null: false
    t.jsonb "sell_levels", null: false
    t.datetime "timestamp", precision: nil, null: false
    t.index ["region_id", "timestamp"], name: "market_region_depth_snapshots_region_id_timestamp_idx", order: { timestamp: :desc }
    t.index ["timestamp", "region_id", "type_id"], name: "market_region_depth_snapshots_key", unique: true
    t.index ["timestamp"], name: "market_region_depth_snapshots_timestamp_idx", order: :desc
  end

  create_table "notable_jobs", force: :cascade do |t|
    t.text "note_type"
    t.text "note"
    t.text "job"
    t.text "job_id"
    t.text "queue"
    t.float "runtime"
    t.float "queued_time"
    t.datetime "created_at"
  end

  create_table "notable_requests", force: :cascade do |t|
    t.string "user_type"
    t.bigint "user_id"
    t.text "note_type"
    t.text "note"
    t.text "action"
    t.integer "status"
    t.text "url"
    t.text "request_id"
    t.text "ip"
    t.text "user_agent"
    t.text "referrer"
    t.text "params"
    t.float "request_time"
    t.datetime "created_at"
    t.index ["user_id", "user_type"], name: "notable_requests_user_idx"
  end

  create_table "regions", force: :cascade do |t|
    t.text "name", null: false
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
  end

  create_table "solar_systems", force: :cascade do |t|
    t.bigint "constellation_id", null: false
    t.text "name", null: false
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["constellation_id"], name: "solar_systems_constellation_id_idx"
  end

  create_table "stations", force: :cascade do |t|
    t.bigint "owner_id", null: false
    t.bigint "solar_system_id", null: false
    t.text "name", null: false
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["owner_id"], name: "stations_owner_id_idx"
    t.index ["solar_system_id"], name: "stations_solar_system_id_idx"
  end

  add_foreign_key "constellations", "regions", name: "constellations_region_id_fkey"
  add_foreign_key "solar_systems", "constellations", name: "solar_systems_constellation_id_fkey"
  add_foreign_key "stations", "corporations", column: "owner_id", name: "stations_owner_id_fkey"
  add_foreign_key "stations", "solar_systems", name: "stations_solar_system_id_fkey"
  create_hypertable "market_region_depth_snapshots", time_column: "timestamp", chunk_time_interval: "1 day", partition_column: "region_id", number_partitions: 68

  create_retention_policy "market_region_depth_snapshots", interval: "P35D"
end
