# frozen_string_literal: true

require 'sidekiq/web'

Rails.application.routes.draw do
  mount PgHero::Engine => '/pghero'
  mount Sidekiq::Web => '/sidekiq'

  namespace :api do
    namespace :markets do
      resources :regions, only: %i[index show] do
        get :depths, to: 'regions/depths#index'
      end
    end
  end
end
