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
class Corporation < ApplicationRecord
  belongs_to :alliance, optional: true

  has_many :stations, foreign_key: :owner_id, dependent: :restrict_with_exception
  has_many :structures, foreign_key: :owner_id, dependent: :restrict_with_exception
end
