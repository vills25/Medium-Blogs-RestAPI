# Medium-Blogs-RestAPI

This Repo will represents you a RestAPIs for Medium Blog platform.


### File Structure of Medium Blog Website (Backend API)

MEDIUM-BLOGS-RESTAPI/

├── 📁 logs/                                  # Application log files

├── 📁 media/                               # User-uploaded media storage

│   ├── 📁 article_images/          # Images for articles/blogs

│   └── 📁 profiles/                        # User profile pictures

│

├── 📁 medium_blog_api_app/         # Main Django application

│   │

│   ├── 📁 articles_blogs/                  # Articles & Blogs management

│   │   ├── 📄 articles_view.py             # Article CRUD operations (create, update, delete, search)

│   │   ├── 📄 clap_and_comments.py         # Claps & comments functionality

│   │   ├── 📄 publications_and_topics.py   # Publications & topics management

│   │   └── 📄 readinglist.py               # Reading list operations

│   │

│   ├── 📁 authentication/                  # Authentication system

│   │   └── 📄 custom_jwt_auth.py        # Custom JWT authentication implementation

│   │

│   ├── 📁 middleware/                      # Custom middleware

│   │   └── 📄 logging_middleware.py      # Request/response logging middleware

│   │

│   ├── 📁 migrations/                      # Database migration files

│   │

│   └── 📁 user/                            # User management app

│       ├── 📄 user_view.py    **	** # User profile & authentication views

│       ├── 📄 __init__.py               # Package initialization

│       ├── 📄 admin.py                   # Django admin configuration

│       ├── 📄 apps.py                     # App configuration

│       ├── 📄 models.py                 # User models & database schema

│       ├── 📄 serializers.py            # Data serialization for APIs

│       ├── 📄 tests.py                     # Test cases

│       ├── 📄 urls.py                       # URL routing for user endpoints

│       ├── 📄 utils.py                      # Utility functions & helpers

│       └── 📄 views.py                    # Business logic for user operations

│

├── 📁 medium_blog_api_project/         # Django project configuration

│   ├── 📄 __init__.py                   # Package initialization

│   ├── 📄 asgi.py                           # ASGI configuration for async support

│   ├── 📄 logging_config.py        # Logging configuration

│   ├── 📄 settings.py                     # Project settings & configuration

│   ├── 📄 urls.py                            # Main URL routing

│   └── 📄 wsgi.py                         # WSGI configuration for deployment

│

├── 📁 myvenv/                       # Python virtual environment

├── 📄 .gitignore                      # Git ignore rules

├── 📄 LICENSE                        # Project license

├── 📄 manage.py                    # Django management script

├── 📄 README.md                   # Project documentation

├── 📄 requirements.txt            # Python dependencies

└── 📄 test.py                              # Test scripts

**
