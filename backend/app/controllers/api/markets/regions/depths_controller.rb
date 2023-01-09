# frozen_string_literal: true

module API
  module Markets
    module Regions
      class DepthsController < ApplicationController
        def index # rubocop:disable Metrics/AbcSize, Metrics/MethodLength
          type_ids = index_params[:type_ids]
          start_ts = index_params[:start] ? DateTime.parse(index_params[:start]) : 1.day.ago
          end_ts = index_params[:end] ? DateTime.parse(index_params[:end]) : Time.zone.now

          @depths = MarketRegionDepthSnapshot.select(:type_id, :buy_levels, :sell_levels, :timestamp)
                                             .where(
                                               region_id: params[:region_id],
                                               timestamp: start_ts..end_ts,
                                               type_id: type_ids
                                             )
                                             .order(:type_id, :timestamp)

          render json: @depths.group_by(&:type_id)
        end

        private

        def index_params
          params.permit(:region_id, :type_ids, :start, :end)
        end
      end
    end
  end
end
