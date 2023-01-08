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
FactoryBot.define do
  factory :solar_system do
  end
end
