from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass


class Category(models.Model):
    name = models.CharField(max_length=64)

    def __str__(self):
        return self.name


class Listing(models.Model):
    title = models.CharField(max_length=64)
    description = models.TextField()
    starting_bid = models.DecimalField(max_digits=10, decimal_places=2)
    image_url = models.URLField(max_length=1000, blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, blank=True, null=True, related_name="category_listings")
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_listings")
    active = models.BooleanField(default=True)
    watchlist = models.ManyToManyField(User, blank=True, related_name="watchlist_listings")

    def __str__(self):
        return self.title


class Bid(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="bids")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bids")
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.user.username} bid {self.amount} on {self.listing.title}"


class Comment(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    text = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user.username} on {self.listing.title}"