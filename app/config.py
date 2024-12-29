import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    EXPLAIN_TEMPLATE_LOADING = False
    TEMPLATES_AUTO_RELOAD = True
