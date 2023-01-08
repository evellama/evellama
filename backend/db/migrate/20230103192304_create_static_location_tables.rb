# frozen_string_literal: true

class CreateStaticLocationTables < ActiveRecord::Migration[7.0]
  def change
    create_table :regions do |t|
      t.text :name, null: false
      t.timestamps null: false
    end

    create_table :constellations do |t|
      t.references :region, null: false, index: { name: :constellations_region_id_idx },
                            foreign_key: { name: :constellations_region_id_fkey }

      t.text :name, null: false
      t.timestamps null: false
    end

    create_table :solar_systems do |t|
      t.references :constellation, null: false, index: { name: :solar_systems_constellation_id_idx },
                                   foreign_key: { name: :solar_systems_constellation_id_fkey }

      t.text :name, null: false
      t.timestamps null: false
    end

    create_table :corporations do |t|
      t.text :name, null: false
      t.timestamps null: false
    end

    create_table :stations do |t|
      t.references :owner, null: false, index: { name: :stations_owner_id_idx },
                           foreign_key: { name: :stations_owner_id_fkey, to_table: :corporations }
      t.references :solar_system, null: false, index: { name: :stations_solar_system_id_idx },
                                  foreign_key: { name: :stations_solar_system_id_fkey }

      t.text :name, null: false
      t.timestamps null: false
    end
  end
end
