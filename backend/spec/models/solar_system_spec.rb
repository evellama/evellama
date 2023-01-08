# frozen_string_literal: true

# ## Schema Information
#
# Table name: `solar_systems`
#
# ### Columns
#
# Name                    | Type               | Attributes
# ----------------------- | ------------------ | ---------------------------
# **`id`**                | `bigint`           | `not null, primary key`
# **`name`**              | `text`             | `not null`
# **`created_at`**        | `datetime`         | `not null`
# **`updated_at`**        | `datetime`         | `not null`
# **`constellation_id`**  | `bigint`           | `not null`
#
# ### Indexes
#
# * `solar_systems_constellation_id_idx`:
#     * **`constellation_id`**
#
# ### Foreign Keys
#
# * `solar_systems_constellation_id_fkey`:
#     * **`constellation_id => constellations.id`**
#
require 'rails_helper'

RSpec.describe SolarSystem do
  pending "add some examples to (or delete) #{__FILE__}"
end
