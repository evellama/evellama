# frozen_string_literal: true

# ## Schema Information
#
# Table name: `market_exchange_depths`
#
# ### Columns
#
# Name               | Type               | Attributes
# ------------------ | ------------------ | ---------------------------
# **`count`**        | `integer`          | `not null`
# **`price`**        | `decimal(, )`      | `not null`
# **`side`**         | `enum`             | `not null`
# **`timestamp`**    | `datetime`         | `not null`
# **`volume`**       | `bigint`           | `not null`
# **`exchange_id`**  | `bigint`           | `not null`
# **`item_id`**      | `bigint`           | `not null`
#
# ### Indexes
#
# * `market_exchange_depths_timestamp_exchange_id_item_id_idx`:
#     * **`timestamp`**
#     * **`exchange_id`**
#     * **`item_id`**
# * `market_exchange_depths_timestamp_idx`:
#     * **`timestamp`**
#
require 'rails_helper'

RSpec.describe MarketExchangeDepth do
  pending "add some examples to (or delete) #{__FILE__}"
end
