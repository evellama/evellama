# frozen_string_literal: true

# ## Schema Information
#
# Table name: `corporations`
#
# ### Columns
#
# Name              | Type               | Attributes
# ----------------- | ------------------ | ---------------------------
# **`id`**          | `bigint`           | `not null, primary key`
# **`name`**        | `text`             | `not null`
# **`created_at`**  | `datetime`         | `not null`
# **`updated_at`**  | `datetime`         | `not null`
#
require 'rails_helper'

RSpec.describe Corporation do
  pending "add some examples to (or delete) #{__FILE__}"
end
