from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("create", views.create_listing, name="create"),
    path("listing/<int:listing_id>", views.listing_page, name="listing_page"),
    path("watchlist", views.watchlist, name="watchlist"),
    path("watchlist/toggle/<int:listing_id>", views.toggle_watchlist, name="toggle_watchlist"),
    path("categories", views.categories, name="categories"),
    path("category/<int:category_id>", views.category_listings, name="category_listings"),
    path("listing/<int:listing_id>/bid", views.place_bid, name="place_bid"),
    path("listing/<int:listing_id>/comment", views.add_comment, name="add_comment"),
    path("listing/<int:listing_id>/close", views.close_auction, name="close_auction"),
]