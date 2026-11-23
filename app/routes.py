import os, uuid
from pathlib import Path
from urllib.parse import urlparse
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from PIL import Image
from .extensions import db
from .models import User, Category, Listing, ListingImage, Favorite

main = Blueprint("main", __name__)
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
CONDITIONS = ["Brand New", "Like New", "Gently Used", "Used", "Heavily Used"]
STATUSES = ["Available", "Reserved", "Sold"]
CATEGORIES = ["TUP Uniforms","PATHFIT Uniforms", "NSTP Uniforms", "Secondhand Wearables", "Food", "ACSO Merchandise", "Handcrafted Items", "School Supplies", "Electronics and Gadgets", "Books and Learning Materials", "Accessories", "Others"]

def seed_categories():
    for name in CATEGORIES:
        if not Category.query.filter_by(name=name).first():
            db.session.add(Category(name=name, is_active=True))
    db.session.commit()
    
def save_images(files):
    saved = []
    upload_dir = Path(current_app.config["UPLOAD_FOLDER"])
    for file in files:
        if not file or not file.filename:
            continue
        ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError("Only JPG, PNG, and WEBP images are allowed.")
        filename = f"{uuid.uuid4().hex}.{ext}"
        path = upload_dir / filename
        file.save(path)
        try:
            with Image.open(path) as img:
                img.verify()
        except Exception:
            path.unlink(missing_ok=True)
            raise ValueError("One of the uploaded files is not a valid image.")
        saved.append(filename)
    return saved

@main.route("/")
def home():
    featured = Listing.query.filter_by(status="Available", moderation_status="normal").order_by(Listing.created_at.desc()).limit(8).all()
    categories = Category.query.filter_by(is_active=True).order_by(Category.name).all()
    return render_template("home.html", featured=featured, categories=categories)

@main.route("/marketplace")
def marketplace():
    query = Listing.query.filter_by(moderation_status="normal")
    term = request.args.get("q", "").strip()
    category_id = request.args.get("category", type=int)
    condition = request.args.get("condition", "")
    status = request.args.get("status", "Available")
    min_price = request.args.get("min_price", type=float)
    max_price = request.args.get("max_price", type=float)
    sort = request.args.get("sort", "newest")

    if term:
        like = f"%{term}%"
        query = query.join(User).filter(
            db.or_(Listing.title.ilike(like), Listing.description.ilike(like),
                   User.username.ilike(like), User.full_name.ilike(like))
        )
    if category_id:
        query = query.filter(Listing.category_id == category_id)
    if condition:
        query = query.filter(Listing.condition == condition)
    if status in STATUSES:
        query = query.filter(Listing.status == status)
    else:
        query = query.filter(Listing.status != "Sold")
    if min_price is not None:
        query = query.filter(Listing.price >= min_price)
    if max_price is not None:
        query = query.filter(Listing.price <= max_price)

    if sort == "oldest":
        query = query.order_by(Listing.created_at.asc())
    elif sort == "price_low":
        query = query.order_by(Listing.price.asc())
    elif sort == "price_high":
        query = query.order_by(Listing.price.desc())
    else:
        query = query.order_by(Listing.created_at.desc())

    return render_template("marketplace.html", listings=query.all(),
        categories=Category.query.filter_by(is_active=True).order_by(Category.name).all(),
        conditions=CONDITIONS, filters=request.args)

@main.route("/listing/<int:listing_id>")
def listing_detail(listing_id):
    listing = db.get_or_404(Listing, listing_id)
    if listing.status == "Sold" and (not current_user.is_authenticated or current_user.id != listing.seller_id):
        abort(404)
    if listing.moderation_status != "normal":
        if not current_user.is_authenticated or current_user.id != listing.seller_id:
            abort(404)
    related = Listing.query.filter(Listing.category_id == listing.category_id,
        Listing.id != listing.id, Listing.status == "Available",
        Listing.moderation_status == "normal").limit(4).all()
    return render_template("listing_detail.html", listing=listing, related=related)

@main.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        program = request.form.get("program", "").strip()
        year_level = request.form.get("year_level", "").strip()
        if not all([full_name, username, email, password]):
            flash("Please complete all required fields.", "error")
        elif len(password) < 8:
            flash("Password must be at least 8 characters.", "error")
        elif User.query.filter(db.or_(User.username == username, User.email == email)).first():
            flash("That username or email is already registered.", "error")
        else:
            user = User(full_name=full_name, username=username, email=email,
                        program=program, year_level=year_level,
                        email_verified=False, eligibility_status="pending")
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash("Account created. Email verification and student eligibility approval are not yet enabled in this prototype.", "success")
            return redirect(url_for("main.login"))
    return render_template("auth.html", mode="register")

@main.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))
    if request.method == "POST":
        identity = request.form.get("identity", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter(db.or_(User.username == identity, User.email == identity.lower())).first()
        if user and user.check_password(password) and user.account_status == "active":
            login_user(user, remember=bool(request.form.get("remember")))
            flash("Welcome back!", "success")
            return redirect(request.args.get("next") or url_for("main.home"))
        flash("Invalid login details or inactive account.", "error")
    return render_template("auth.html", mode="login")

@main.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("main.home"))



def normalize_facebook_url(value):
    """Accept only Facebook profile/page URLs, not arbitrary external URLs."""
    value = (value or "").strip()
    if not value:
        return None
    if not value.startswith(("https://", "http://")):
        value = "https://" + value
    parsed = urlparse(value)
    host = (parsed.hostname or "").lower()
    allowed_hosts = {"facebook.com", "www.facebook.com", "m.facebook.com", "fb.me", "www.fb.me"}
    if parsed.scheme != "https" or host not in allowed_hosts or not parsed.path.strip("/"):
        raise ValueError("Enter a valid Facebook profile or Page link (for example, https://www.facebook.com/yourname).")
    return value


@main.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        program = request.form.get("program", "").strip()
        year_level = request.form.get("year_level", "").strip()
        bio = request.form.get("bio", "").strip()
        try:
            facebook_url = normalize_facebook_url(request.form.get("facebook_url"))
            if not full_name:
                raise ValueError("Your name cannot be empty.")
            if len(full_name) > 120 or len(program) > 100 or len(year_level) > 30 or len(bio) > 500:
                raise ValueError("Please keep your name, program, year level, and bio within the indicated limits.")

            old_photo = current_user.profile_photo
            photo = request.files.get("profile_photo")
            uploaded = save_images([photo]) if photo and photo.filename else []
            current_user.full_name = full_name
            current_user.program = program or None
            current_user.year_level = year_level or None
            current_user.bio = bio or None
            current_user.facebook_url = facebook_url
            if uploaded:
                current_user.profile_photo = uploaded[0]
            db.session.commit()

            if uploaded and old_photo:
                old_path = Path(current_app.config["UPLOAD_FOLDER"]) / old_photo
                old_path.unlink(missing_ok=True)
            flash("Your profile has been updated.", "success")
            return redirect(url_for("main.profile"))
        except ValueError as exc:
            db.session.rollback()
            flash(str(exc), "error")

    return render_template("profile.html", profile_user=current_user, editable=True)


@main.route("/user/<username>")
def public_profile(username):
    profile_user = User.query.filter_by(username=username).first_or_404()
    return render_template("profile.html", profile_user=profile_user, editable=False)


@main.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    if request.method == "POST":
        try:
            title = request.form.get("title", "").strip()
            description = request.form.get("description", "").strip()
            category_id = request.form.get("category_id", type=int)
            price = request.form.get("price", type=float)
            quantity = request.form.get("quantity", 1, type=int)
            condition = request.form.get("condition", "")
            category = db.session.get(Category, category_id) if category_id else None
            if not title or not description or not category or price is None or price < 0 or quantity < 1 or condition not in CONDITIONS:
                raise ValueError("Please complete the required fields with valid values.")
            uploaded = save_images(request.files.getlist("photos"))
            if not uploaded:
                raise ValueError("Please upload at least one product photo.")
            if len(uploaded) > 5:
                for name in uploaded:
                    (Path(current_app.config["UPLOAD_FOLDER"]) / name).unlink(missing_ok=True)
                raise ValueError("You can upload a maximum of five photos.")
            listing = Listing(seller_id=current_user.id, category_id=category.id,
                title=title, description=description, price=price, quantity=quantity,
                negotiable=bool(request.form.get("negotiable")), condition=condition,
                size=request.form.get("size", "").strip(), fit=request.form.get("fit", "").strip(),
                program=request.form.get("program", "").strip(), item_type=request.form.get("item_type", "").strip(),
                meeting_location=request.form.get("meeting_location", "").strip())
            db.session.add(listing)
            db.session.flush()
            for i, filename in enumerate(uploaded):
                db.session.add(ListingImage(listing_id=listing.id, filename=filename, position=i))
            db.session.commit()
            flash("Your listing has been published.", "success")
            return redirect(url_for("main.listing_detail", listing_id=listing.id))
        except ValueError as exc:
            flash(str(exc), "error")
    return render_template("sell.html", categories=Category.query.filter_by(is_active=True).order_by(Category.name).all(), conditions=CONDITIONS)

@main.route("/my-listings")
@login_required
def my_listings():
    listings = Listing.query.filter_by(seller_id=current_user.id).order_by(Listing.created_at.desc()).all()
    return render_template("my_listings.html", listings=listings)

@main.route("/listing/<int:listing_id>/status", methods=["POST"])
@login_required
def update_status(listing_id):
    listing = db.get_or_404(Listing, listing_id)
    if listing.seller_id != current_user.id:
        abort(403)
    status = request.form.get("status")
    if status not in STATUSES:
        abort(400)
    listing.status = status
    db.session.commit()
    flash("Listing status updated.", "success")
    return redirect(url_for("main.my_listings"))

@main.route("/listing/<int:listing_id>/delete", methods=["POST"])
@login_required
def delete_listing(listing_id):
    listing = db.get_or_404(Listing, listing_id)
    if listing.seller_id != current_user.id:
        abort(403)
    for image in listing.images:
        (Path(current_app.config["UPLOAD_FOLDER"]) / image.filename).unlink(missing_ok=True)
    db.session.delete(listing)
    db.session.commit()
    flash("Listing deleted.", "success")
    return redirect(url_for("main.my_listings"))

@main.route("/listing/<int:listing_id>/favorite", methods=["POST"])
@login_required
def toggle_favorite(listing_id):
    listing = db.get_or_404(Listing, listing_id)
    if listing.seller_id == current_user.id:
        flash("You cannot favorite your own listing.", "error")
    else:
        favorite = Favorite.query.filter_by(user_id=current_user.id, listing_id=listing.id).first()
        if favorite:
            db.session.delete(favorite)
            flash("Removed from favorites.", "success")
        else:
            db.session.add(Favorite(user_id=current_user.id, listing_id=listing.id))
            flash("Added to favorites.", "success")
        db.session.commit()
    return redirect(request.referrer or url_for("main.marketplace"))

@main.route("/favorites")
@login_required
def favorites():
    saved = [f.listing for f in current_user.favorites if f.listing.status != "Sold"]
    return render_template("favorites.html", listings=saved)
