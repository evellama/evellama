# frozen_string_literal: true

class CreateNotableJobs < ActiveRecord::Migration[7.0]
  def change
    create_table :notable_jobs do |t|
      t.text :note_type
      t.text :note
      t.text :job
      t.text :job_id
      t.text :queue
      t.float :runtime
      t.float :queued_time
      t.datetime :created_at
    end
  end
end
