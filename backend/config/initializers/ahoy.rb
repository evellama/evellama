# frozen_string_literal: true

module Ahoy
  class Store < Ahoy::DatabaseStore
    def authenticate(data)
      # disables automatic linking of visits and users
    end
  end
end

# set to true for JavaScript tracking
Ahoy.api = false

# set to true for geocoding (and add the geocoder gem to your Gemfile)
# we recommend configuring local geocoding as well
# see https://github.com/ankane/ahoy#geocoding
Ahoy.geocode = false

Ahoy.mask_ips = true
Ahoy.cookies = false
