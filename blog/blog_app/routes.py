from flask import Blueprint, render_template, redirect, url_for, flash, session, request, current_app
from .models import db, User, Profile, Blog
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from functions import login_required

main = Blueprint('main', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def handle_thumbnail(thumbnail):
    """Handle thumbnail upload and return the path."""
    return handle_image_upload(thumbnail, 'thumbnail')

def handle_profile_img(profile_img):
    """Handle profile image upload and return the path."""
    return handle_image_upload(profile_img, 'profile_img')

def handle_profile_banner(profile_banner):
    """Handle profile banner upload and return the path."""
    return handle_image_upload(profile_banner, 'banner')

def handle_image_upload(image, folder_name):
    """General function to handle image uploads."""
    if image and allowed_file(image.filename):
        uploads_dir = os.path.join(current_app.root_path, current_app.config['UPLOADS_FOLDER'], folder_name)
        os.makedirs(uploads_dir, exist_ok=True)

        filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{secure_filename(image.filename)}"
        image_path = os.path.join(uploads_dir, filename)
        image.save(image_path)
        return os.path.join(current_app.config['UPLOADS_FOLDER'], folder_name, filename)
    return None

@main.route("/")
def index():
    blogs = Blog.query.all()
    user_id = session.get("user_id")
    profile = Profile.query.filter_by(user_id=user_id).first() if user_id else None
    user = User.query.filter_by(id=user_id).first() if user_id else None

    return render_template("index.html", blogs=blogs, profile=profile, user=user)

@main.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if not (username and email and password):
            flash("Username, email, and password are required.")
            return redirect(url_for('main.login'))

        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password) or user.email != email:
            flash("Invalid username, email, and/or password.")
            return redirect(url_for('main.login'))

        session['user_id'] = user.id
        user.last_login = datetime.utcnow()
        db.session.commit()
        flash(f"Welcome back, {username}!")
        return redirect(url_for('main.index'))
    
    return render_template("login.html")

@main.route("/register", methods=["GET", "POST"])
def register():
    if request.method == 'POST':
        f_name = request.form.get('first_name')
        l_name = request.form.get('last_name')
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirmation = request.form.get('confirm_password')

        if not all([f_name, l_name, username, email, password, confirmation]):
            flash("All fields are required.")
            return redirect(url_for('main.register'))

        if password != confirmation:
            flash("Passwords do not match.")
            return redirect(url_for('main.register'))

        if User.query.filter_by(username=username).first():
            flash("Username is already taken.")
            return redirect(url_for('main.register'))

        if User.query.filter_by(email=email).first():
            flash("Email is already registered.")
            return redirect(url_for('main.register'))

        try:
            new_user = User(username=username, email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()

            default_profile_img = "/static/uploads/default.jpg"
            new_profile = Profile(user_id=new_user.id, first_name=f_name, last_name=l_name, profile_img=default_profile_img)
            db.session.add(new_profile)
            db.session.commit()

            session['user_id'] = new_user.id
            flash(f"Welcome, {username}!")
            return redirect(url_for('main.index'))
        except Exception as e:
            db.session.rollback()
            flash("An error occurred during registration. Please try again.")
            return redirect(url_for('main.register'))

    return render_template("register.html")

@main.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('main.index'))

@main.route("/create_blog", methods=["GET", "POST"])
@login_required
def create_blog():
    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")
        thumbnail = request.files.get("thumbnail")

        if not all([title, content]):
            flash("Title and content are required.")
            return redirect(url_for("main.create_blog"))

        user_id = session.get("user_id")
        if not user_id:
            flash("You must be logged in to create a blog.")
            return redirect(url_for("main.login"))

        thumbnail_path = handle_thumbnail(thumbnail)
        if not thumbnail_path:
            flash("Invalid thumbnail format. Please upload a PNG, JPG, JPEG, or GIF image.")
            return redirect(url_for("main.create_blog"))

        try:
            new_blog = Blog(
                user_id=user_id,
                title=title,
                content=content,
                thumbnail_url=thumbnail_path,
                created_at=datetime.utcnow(),
            )

            db.session.add(new_blog)
            db.session.commit()
            flash("Blog post created successfully!")
            return redirect(url_for("main.index"))

        except Exception as e:
            db.session.rollback()
            flash("An error occurred while creating the blog. Please try again.")
            return redirect(url_for("main.create_blog"))

    return render_template("/BlogHtml/blog_create.html")


@main.route('/blog')
def view_blog():
    blogs = Blog.query.all()
    user_id = session.get("user_id")
    profile = Profile.query.filter_by(user_id=user_id).first() if user_id else None
    user = User.query.filter_by(id=user_id).first() if user_id else None

    # For each blog, get the author's profile and user information
    for blog in blogs:
        blog.author_profile = Profile.query.filter_by(user_id=blog.user_id).first()
        blog.author_user = User.query.filter_by(id=blog.user_id).first()

    return render_template("BlogHtml/blog_view.html", blogs=blogs, profile=profile, user=user)


@main.route("/blog/<int:post_id>")
def blog_details(post_id):
    blog = Blog.query.get(post_id)
    if not blog:
        flash("Blog post not found.")
        return redirect(url_for("main.index"))

    # Fetch the author's profile and user information
    blog.author_profile = Profile.query.filter_by(user_id=blog.user_id).first()
    blog.author_user = User.query.filter_by(id=blog.user_id).first()

    # Fetch the current user's information
    user_id = session.get('user_id')
    current_user_profile = Profile.query.filter_by(user_id=user_id).first() if user_id else None
    current_user = User.query.filter_by(id=user_id).first() if user_id else None

    # Ensure paths are correctly formatted and relative to 'static'
    blog_thumbnail_url = os.path.join('uploads', 'thumbnail', os.path.basename(blog.thumbnail_url)).replace('\\', '/')
    author_profile_image_url = os.path.join('uploads', 'profile_img', os.path.basename(blog.author_profile.profile_img)).replace('\\', '/') if blog.author_profile and blog.author_profile.profile_img else 'uploads/default.jpg'
    current_user_profile_image_url = os.path.join('uploads', 'profile_img', os.path.basename(current_user_profile.profile_img)).replace('\\', '/') if current_user_profile and current_user_profile.profile_img else 'uploads/default.jpg'

    return render_template("BlogHtml/blog_details.html", 
                           blog=blog, 
                           current_user_profile=current_user_profile, 
                           current_user=current_user,
                           blog_thumbnail_url=blog_thumbnail_url, 
                           author_profile_image_url=author_profile_image_url,
                           current_user_profile_image_url=current_user_profile_image_url)

@main.route("/update_blog/<int:post_id>", methods=["GET", "POST"])
@login_required
def update_blog(post_id):
    blog_to_update = Blog.query.get(post_id)
    if blog_to_update is None:
        flash("Blog post not found.")
        return redirect(url_for("main.index"))

    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")
        thumbnail = request.files.get("thumbnail")

        if not all([title, content]):
            flash("Title and content are required.")
            return redirect(url_for("main.update_blog", post_id=post_id))

        if thumbnail:
            # Debugging: Log the old thumbnail path
            old_thumbnail_path = blog_to_update.thumbnail_url
            print(f"Old Thumbnail Path: {old_thumbnail_path}")

            # Ensure the path is absolute
            if old_thumbnail_path:
                abs_path = os.path.abspath(os.path.join(current_app.root_path, old_thumbnail_path))
                print(f"Absolute Path: {abs_path}")

                # Check if the file exists and delete it
                if os.path.exists(abs_path):
                    try:
                        os.remove(abs_path)
                        print(f"Deleted old thumbnail: {abs_path}")
                    except Exception as e:
                        print(f"Error deleting old thumbnail: {e}")
                        flash("Could not delete old thumbnail. Please try again.")
                        return redirect(url_for("main.update_blog", post_id=post_id))
                else:
                    print("File does not exist!")

            # Upload the new thumbnail
            thumbnail_path = handle_thumbnail(thumbnail)
            if not thumbnail_path:
                flash("Invalid thumbnail format. Please upload a PNG, JPG, JPEG, or GIF image.")
                return redirect(url_for("main.update_blog", post_id=post_id))
        else:
            thumbnail_path = blog_to_update.thumbnail_url  # Retain old thumbnail

        try:
            blog_to_update.title = title
            blog_to_update.content = content
            blog_to_update.thumbnail_url = thumbnail_path
            blog_to_update.updated_at = datetime.utcnow()

            db.session.commit()
            flash("Blog post updated successfully!")
            return redirect(url_for("main.index"))
        except Exception as e:
            db.session.rollback()
            print(f"Database Error: {e}")
            flash("An error occurred while updating the blog. Please try again.")
            return redirect(url_for("main.update_blog", post_id=post_id))

    return render_template("/BlogHtml/blog_update.html", blog=blog_to_update)




@main.route("/delete_blog/<int:post_id>", methods=['GET', 'POST'])
@login_required
def delete_blog(post_id):
    blog = Blog.query.get(post_id)
    if request.method == 'POST':
        if blog:
            db.session.delete(blog)
            db.session.commit()
            flash("Blog deleted successfully.")
        else:
            flash("Blog not found.")
        return redirect(url_for("main.view_blog"))

    return render_template("BlogHtml/blog_delete_confirm.html", blog=blog) if blog else redirect(url_for("main.view_blog", error="Blog not found."))

@main.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user_id = session['user_id']
    blogs = Blog.query.filter_by(user_id=user_id).all()
    profile = Profile.query.filter_by(user_id=user_id).first()
    user = User.query.filter_by(id=user_id).first()

    return render_template("profile.html", blogs=blogs, profile=profile, user=user)

@main.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    user_id = session['user_id']
    profile = Profile.query.filter_by(user_id=user_id).first()
    user = User.query.filter_by(id=user_id).first()

    if request.method == "POST":
        f_name = request.form.get("first_name")
        l_name = request.form.get("last_name")
        bio = request.form.get("bio")
        email = request.form.get("email")
        profile_img = request.files.get("profile_img")
        profile_banner = request.files.get("profile_banner")

        # Handle profile image
        if profile_img:
            if profile.profile_img:
                old_img_path = os.path.join(current_app.root_path, profile.profile_img)
                if os.path.exists(old_img_path):
                    try:
                        os.remove(old_img_path)
                        print(f"Deleted old profile image: {old_img_path}")
                    except Exception as e:
                        print(f"Error deleting old profile image: {e}")

            profile_img_path = handle_profile_img(profile_img)
            if profile_img_path:
                profile.profile_img = profile_img_path

        # Handle profile banner
        if profile_banner:
            if profile.profile_banner:
                old_banner_path = os.path.join(current_app.root_path, profile.profile_banner)
                if os.path.exists(old_banner_path):
                    try:
                        os.remove(old_banner_path)
                        print(f"Deleted old profile banner: {old_banner_path}")
                    except Exception as e:
                        print(f"Error deleting old profile banner: {e}")

            profile_banner_path = handle_profile_banner(profile_banner)
            if profile_banner_path:
                profile.profile_banner = profile_banner_path

        # Update other fields
        if all([f_name, l_name, bio, email]):
            profile.first_name = f_name
            profile.last_name = l_name
            profile.bio = bio
            user.email = email

            try:
                db.session.commit()
                flash("Profile updated successfully.")
                return redirect(url_for("main.profile"))
            except Exception as e:
                db.session.rollback()
                print(f"Database error: {e}")
                flash("An error occurred while updating your profile. Please try again.")

    return render_template("profile_edit.html", profile=profile, user=user)


