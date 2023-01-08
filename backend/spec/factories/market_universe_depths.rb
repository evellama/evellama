# frozen_string_literal: true

# ## Schema Information
#
# Table name: `market_universe_depths`
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
#
# ### Indexes
#
# * `market_universe_depths_timestamp_idx`:
#     * **`timestamp`**
# * `market_universe_depths_timestamp_item_id_idx`:
#     * **`timestamp`**
#     * **`item_id`**
#
FactoryBot.define do
  factory :market_universe_depth do
  end
end
