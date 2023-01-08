# frozen_string_literal: true

# Specify which environments to use Hypershield
Hypershield.enabled = Rails.env.production?

# Specify the schema to use and columns to show and hide
Hypershield.schemas = {
  hypershield: {
    # columns to hide
    # matches table.column
    hide: %w[encrypted password token secret],
    # overrides hide
    # matches table.column
    show: []
  }
}

# Log SQL statements
Hypershield.log_sql = false
