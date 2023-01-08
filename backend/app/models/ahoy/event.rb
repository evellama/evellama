# frozen_string_literal: true

# ## Schema Information
#
# Table name: `ahoy_events`
#
# ### Columns
#
# Name              | Type               | Attributes
# ----------------- | ------------------ | ---------------------------
# **`id`**          | `bigint`           | `not null, primary key`
# **`name`**        | `text`             |
# **`properties`**  | `jsonb`            |
# **`time`**        | `datetime`         |
# **`user_id`**     | `bigint`           |
# **`visit_id`**    | `bigint`           |
#
# ### Indexes
#
# * `ahoy_events_name_time_idx`:
#     * **`name`**
#     * **`time`**
# * `ahoy_events_properties_idx` (_using_ gin):
#     * **`properties`**
# * `ahoy_events_user_id_idx`:
#     * **`user_id`**
# * `ahoy_events_visit_id_idx`:
#     * **`visit_id`**
#
module Ahoy
  class Event < ApplicationRecord
    include Ahoy::QueryMethods

    self.table_name = 'ahoy_events'

    belongs_to :visit
    belongs_to :user, optional: true
  end
end
