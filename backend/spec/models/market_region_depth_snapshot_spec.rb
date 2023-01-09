# frozen_string_literal: true

# ## Schema Information
#
# Table name: `market_region_depth_snapshots`
#
# ### Columns
#
# Name               | Type               | Attributes
# ------------------ | ------------------ | ---------------------------
# **`buy_levels`**   | `jsonb`            | `not null`
# **`sell_levels`**  | `jsonb`            | `not null`
# **`timestamp`**    | `datetime`         | `not null`
# **`region_id`**    | `bigint`           | `not null`
# **`type_id`**      | `bigint`           | `not null`
#
# ### Indexes
#
# * `market_region_depth_snapshots_key` (_unique_):
#     * **`timestamp`**
#     * **`region_id`**
#     * **`type_id`**
# * `market_region_depth_snapshots_region_id_timestamp_idx`:
#     * **`region_id`**
#     * **`timestamp DESC`**
# * `market_region_depth_snapshots_timestamp_idx`:
#     * **`timestamp`**
#
require 'rails_helper'

RSpec.describe MarketRegionDepthSnapshot do
  pending "add some examples to (or delete) #{__FILE__}"
end
