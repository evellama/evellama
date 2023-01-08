# frozen_string_literal: true

# ## Schema Information
#
# Table name: `constellations`
#
# ### Columns
#
# Name              | Type               | Attributes
# ----------------- | ------------------ | ---------------------------
# **`id`**          | `bigint`           | `not null, primary key`
# **`name`**        | `text`             | `not null`
# **`created_at`**  | `datetime`         | `not null`
# **`updated_at`**  | `datetime`         | `not null`
# **`region_id`**   | `bigint`           | `not null`
#
# ### Indexes
#
# * `constellations_region_id_idx`:
#     * **`region_id`**
#
# ### Foreign Keys
#
# * `constellations_region_id_fkey`:
#     * **`region_id => regions.id`**
#
FactoryBot.define do
  factory :constellation do
  end
end
