# frozen_string_literal: true

class CreateNotableRequests < ActiveRecord::Migration[7.0]
  def change
    create_table :notable_requests do |t|
      t.references :user, polymorphic: true, index: false

      t.text :note_type
      t.text :note
      t.text :action
      t.integer :status
      t.text :url
      t.text :request_id
      t.text :ip
      t.text :user_agent
      t.text :referrer
      t.text :params
      t.float :request_time
      t.datetime :created_at

      t.index %i[user_id user_type], name: :notable_requests_user_idx
    end
  end
end
