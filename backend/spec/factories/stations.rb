# frozen_string_literal: true

# ## Schema Information
#
# Table name: `stations`
#
# ### Columns
#
# Name                   | Type               | Attributes
# ---------------------- | ------------------ | ---------------------------
# **`id`**               | `bigint`           | `not null, primary key`
# **`name`**             | `text`             | `not null`
# **`created_at`**       | `datetime`         | `not null`
# **`updated_at`**       | `datetime`         | `not null`
# **`owner_id`**         | `bigint`           | `not null`
# **`solar_system_id`**  | `bigint`           | `not null`
#
# ### Indexes
#
# * `stations_owner_id_idx`:
#     * **`owner_id`**
# * `stations_solar_system_id_idx`:
#     * **`solar_system_id`**
#
# ### Foreign Keys
#
# * `stations_owner_id_fkey`:
#     * **`owner_id => corporations.id`**
# * `stations_solar_system_id_fkey`:
#     * **`solar_system_id => solar_systems.id`**
#
FactoryBot.define do
  factory :station do
  end
end
