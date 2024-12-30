import os

class Config:
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:Read@localhost/blog_project'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'your_secret_key_here'

    # Define the uploads folders relative to the project directory
    UPLOADS_FOLDER = os.path.join('static', 'uploads')
    THUMBNAILS_FOLDER = os.path.join(UPLOADS_FOLDER, 'thumbnails')
    PROFILE_IMAGES_FOLDER = os.path.join(UPLOADS_FOLDER, 'profile_img')
    BANNER_IMAGES_FOLDER = os.path.join(UPLOADS_FOLDER, 'banner')

    # Ensure the folders exist when the app starts
    @classmethod
    def init_app(cls):
        os.makedirs(cls.THUMBNAILS_FOLDER, exist_ok=True)
        os.makedirs(cls.PROFILE_IMAGES_FOLDER, exist_ok=True)
        os.makedirs(cls.BANNER_IMAGES_FOLDER, exist_ok=True)
