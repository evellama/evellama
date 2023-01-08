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
class Constellation < ApplicationRecord
  belongs_to :region

  has_many :solar_systems, dependent: :restrict_with_exception

  validates :name, presence: true
end
