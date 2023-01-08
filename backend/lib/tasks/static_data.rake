# frozen_string_literal: true

namespace :static_data do
  namespace :sde do
    desc 'Download the latest Static Data Export'
    task download: :environment do
      require 'down'
      require 'down/http'
      require 'http'

      checksum = HTTP.get('https://eve-static-data-export.s3-eu-west-1.amazonaws.com/tranquility/checksum').to_s.strip
      checksum_path = Rails.root.join('tmp/sde-checksum.txt')

      if File.exist?(checksum_path) && File.read(checksum_path) == checksum && !ENV['FORCE']
        puts "Static Data Export with checksum #{checksum} already downloaded"
        exit(0)
      end

      zip_path = Rails.root.join('tmp/sde.zip')
      Down::Http.download(
        'https://eve-static-data-export.s3-eu-west-1.amazonaws.com/tranquility/sde.zip',
        destination: zip_path
      )

      sde_path = Rails.root.join('tmp/sde')
      FileUtils.rm_rf(sde_path)

      cmd = TTY::Command.new(output: Rails.logger)
      Dir.chdir(Rails.root.join('tmp')) do
        cmd.run!('/usr/bin/env unzip -qq', zip_path, only_output_on_error: true)
      end

      puts "Downloaded Static Data Export with checksum #{checksum} and unzipped to #{sde_path}"
    end

    desc 'Import the Static Data Export'
    task import: %w[import:setup import:regions import:constellations import:solar_systems import:corporations
                    import:stations]

    namespace :import do
      task setup: :environment do
        @names = YAML.load_file(Rails.root.join('tmp/sde/bsd/invNames.yaml')).each_with_object({}) do |i, h|
          h[i['itemID']] = i['itemName']
        end
      end

      desc 'Import regions from the Static Data Export'
      task regions: :setup do
        glob = Rails.root.join('tmp/sde/fsd/universe/**/region.staticdata')
        records = Dir[glob].each_with_object([]) do |path, records|
          data = YAML.load_file(path)
          records << {
            id: data['regionID'],
            name: @names[data['regionID']]
          }
        end
        Region.upsert_all(records)
      end

      desc 'Import constellations from the Static Data Export'
      task constellations: :setup do
        regions_glob = Rails.root.join('tmp/sde/fsd/universe/**/region.staticdata')
        region_ids = Dir[regions_glob].each_with_object({}) do |path, region_ids|
          data = YAML.load_file(path)
          region_ids[File.dirname(path)] = data['regionID']
        end

        constellations_glob = Rails.root.join('tmp/sde/fsd/universe/**/constellation.staticdata')
        records = Dir[constellations_glob].each_with_object([]) do |path, records|
          data = YAML.load_file(path)
          region_id = region_ids[File.dirname(path, 2)]
          records << ({
            id: data['constellationID'],
            name: @names[data['constellationID']],
            region_id:
          })
        end
        Constellation.upsert_all(records)
      end

      desc 'Import solar systems from the Static Data Export'
      task solar_systems: :setup do
        constellations_glob = Rails.root.join('tmp/sde/fsd/universe/**/constellation.staticdata')
        constellation_ids = Dir[constellations_glob].each_with_object({}) do |path, constellation_ids|
          data = YAML.load_file(path)
          constellation_ids[File.dirname(path)] = data['constellationID']
        end

        systems_glob = Rails.root.join('tmp/sde/fsd/universe/**/solarsystem.staticdata')
        records = Dir[systems_glob].each_with_object([]) do |path, records|
          data = YAML.load_file(path)
          constellation_id = constellation_ids[File.dirname(path, 2)]
          records << ({
            id: data['solarSystemID'],
            name: @names[data['solarSystemID']],
            constellation_id:
          })
        end
        SolarSystem.upsert_all(records)
      end

      desc 'Import corporations from the Static Data Export'
      task corporations: :setup do
        data = YAML.load_file(Rails.root.join('tmp/sde/fsd/npcCorporations.yaml'))
        records = data.each_with_object([]) do |(corporation_id, corporation), records|
          records << {
            id: corporation_id,
            name: corporation['nameID']['en']
          }
        end
        Corporation.upsert_all(records)
      end

      desc 'Import stations from the Static Data Export'
      task stations: :setup do
        data = YAML.load_file(Rails.root.join('tmp/sde/bsd/staStations.yaml'))
        records = data.each_with_object([]) do |station, records|
          records << {
            id: station['stationID'],
            name: station['stationName'],
            owner_id: station['corporationID'],
            solar_system_id: station['solarSystemID']
          }
        end
        Station.upsert_all(records)
      end
    end
  end
end
