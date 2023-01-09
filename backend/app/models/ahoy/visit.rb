# frozen_string_literal: true

# ## Schema Information
#
# Table name: `ahoy_visits`
#
# ### Columns
#
# Name                    | Type               | Attributes
# ----------------------- | ------------------ | ---------------------------
# **`id`**                | `bigint`           | `not null, primary key`
# **`browser`**           | `text`             |
# **`device_type`**       | `text`             |
# **`ip`**                | `text`             |
# **`landing_page`**      | `text`             |
# **`os`**                | `text`             |
# **`referrer`**          | `text`             |
# **`referring_domain`**  | `text`             |
# **`started_at`**        | `datetime`         |
# **`user_agent`**        | `text`             |
# **`utm_campaign`**      | `text`             |
# **`utm_content`**       | `text`             |
# **`utm_medium`**        | `text`             |
# **`utm_source`**        | `text`             |
# **`utm_term`**          | `text`             |
# **`visit_token`**       | `text`             |
# **`visitor_token`**     | `text`             |
#
# ### Indexes
#
# * `ahoy_visits_visit_token_key` (_unique_):
#     * **`visit_token`**
#
module Ahoy
  class Visit < ApplicationRecord
    self.table_name = 'ahoy_visits'

    has_many :events, class_name: 'Ahoy::Event', dependent: :destroy_all
    belongs_to :user, optional: true
  end
end
