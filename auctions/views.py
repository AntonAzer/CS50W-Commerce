from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.db.models import Max
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse

from .models import User, Category, Listing, Bid, Comment

def index(request):
    # Fetch all active auction listings
    listings = Listing.objects.filter(active=True)
    
    # Attach current price dynamically to each listing
    for listing in listings:
        highest_bid = listing.bids.aggregate(Max('amount'))['amount__max']
        listing.current_price = highest_bid if highest_bid else listing.starting_bid

    return render(request, "auctions/index.html", {
        "listings": listings
    })

@login_required
def create_listing(request):
    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        starting_bid_raw = request.POST.get("starting_bid")
        image_url = request.POST.get("image_url") or None
        category_id = request.POST.get("category")

        # Fallback to 0.0 if parsing fails, ensuring the DB gets a numeric format
        try:
            starting_bid = float(starting_bid_raw)
        except (ValueError, TypeError):
            starting_bid = 0.0

        # Safe category lookup
        category = None
        if category_id and category_id.isdigit():
            category = get_object_or_404(Category, pk=category_id)

        # Create and save new listing with explicit active status
        listing = Listing.objects.create(
            title=title,
            description=description,
            starting_bid=starting_bid,
            image_url=image_url,
            category=category,
            creator=request.user,
            active=True  # Force-pass True in case your model lacks a default=True statement
        )
        return HttpResponseRedirect(reverse("listing_page", args=[listing.id]))
    
    else:
        categories = Category.objects.all()
        return render(request, "auctions/create.html", {
            "categories": categories
        })
def listing_page(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)
    
    # Calculate current highest bid
    highest_bid_obj = listing.bids.order_by('-amount').first()
    current_price = highest_bid_obj.amount if highest_bid_obj else listing.starting_bid
    
    # Watchlist check
    is_on_watchlist = False
    if request.user.is_authenticated:
        if listing.watchlist.filter(id=request.user.id).exists():
            is_on_watchlist = True

    # Determine auction status messages
    winner = None
    if not listing.active and highest_bid_obj:
        winner = highest_bid_obj.user

    comments = listing.comments.all().order_by('-date')

    return render(request, "auctions/listing.html", {
        "listing": listing,
        "current_price": current_price,
        "is_on_watchlist": is_on_watchlist,
        "comments": comments,
        "winner": winner,
        "highest_bidder": highest_bid_obj.user if highest_bid_obj else None
    })

@login_required
def toggle_watchlist(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)
    if listing.watchlist.filter(id=request.user.id).exists():
        listing.watchlist.remove(request.user)
    else:
        listing.watchlist.add(request.user)
    return HttpResponseRedirect(reverse("listing_page", args=[listing_id]))

@login_required
def watchlist(request):
    listings = request.user.watchlist_listings.all()
    for listing in listings:
        highest_bid = listing.bids.aggregate(Max('amount'))['amount__max']
        listing.current_price = highest_bid if highest_bid else listing.starting_bid
        
    return render(request, "auctions/watchlist.html", {
        "listings": listings
    })

def categories(request):
    categories = Category.objects.all()
    return render(request, "auctions/categories.html", {
        "categories": categories
    })

def category_listings(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    listings = category.category_listings.filter(active=True)
    
    for listing in listings:
        highest_bid = listing.bids.aggregate(Max('amount'))['amount__max']
        listing.current_price = highest_bid if highest_bid else listing.starting_bid

    return render(request, "auctions/category_listings.html", {
        "category": category,
        "listings": listings
    })

@login_required
def place_bid(request, listing_id):
    if request.method == "POST":
        listing = get_object_or_404(Listing, pk=listing_id)
        bid_amount = float(request.POST.get("bid_amount", 0))
        
        highest_bid_obj = listing.bids.order_by('-amount').first()
        min_required_bid = float(highest_bid_obj.amount) if highest_bid_obj else float(listing.starting_bid)

        # Validation rules
        if highest_bid_obj and bid_amount <= min_required_bid:
            error_message = f"Bid must be higher than the current price of ${min_required_bid:.2f}."
        elif not highest_bid_obj and bid_amount < min_required_bid:
            error_message = f"Bid must be at least the starting price of ${min_required_bid:.2f}."
        else:
            Bid.objects.create(listing=listing, user=request.user, amount=bid_amount)
            return HttpResponseRedirect(reverse("listing_page", args=[listing_id]))

        # Re-render listing page with error contexts if validation fails
        comments = listing.comments.all().order_by('-date')
        return render(request, "auctions/listing.html", {
            "listing": listing,
            "current_price": min_required_bid,
            "is_on_watchlist": listing.watchlist.filter(id=request.user.id).exists(),
            "comments": comments,
            "error": error_message
        })

@login_required
def add_comment(request, listing_id):
    if request.method == "POST":
        listing = get_object_or_404(Listing, pk=listing_id)
        comment_text = request.POST.get("comment")
        
        if comment_text:
            Comment.objects.create(listing=listing, user=request.user, text=comment_text)
            
    return HttpResponseRedirect(reverse("listing_page", args=[listing_id]))

@login_required
def close_auction(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)
    if listing.creator == request.user:
        listing.active = False
        listing.save()
    return HttpResponseRedirect(reverse("listing_page", args=[listing_id]))


# --- Distribution Code Left Intact ---

def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")

def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))

def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]

        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")