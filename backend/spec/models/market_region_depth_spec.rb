# frozen_string_literal: true

# ## Schema Information
#
# Table name: `market_region_depths`
#
# ### Columns
#
# Name             | Type               | Attributes
# ---------------- | ------------------ | ---------------------------
# **`count`**      | `integer`          | `not null`
# **`price`**      | `decimal(, )`      | `not null`
# **`side`**       | `enum`             | `not null`
# **`timestamp`**  | `datetime`         | `not null`
# **`volume`**     | `bigint`           | `not null`
# **`item_id`**    | `bigint`           | `not null`
# **`region_id`**  | `bigint`           | `not null`
#
# ### Indexes
#
# * `market_region_depths_timestamp_idx`:
#     * **`timestamp`**
# * `market_region_depths_timestamp_region_id_item_id_idx`:
#     * **`timestamp`**
#     * **`region_id`**
#     * **`item_id`**
#
require 'rails_helper'

RSpec.describe MarketRegionDepth do
  pending "add some examples to (or delete) #{__FILE__}"
end
