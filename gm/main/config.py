import os


class Development(object):
    """
    Development environment configuration
    """
    DEBUG = True
    TESTING = False
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI',
                                        'postgresql://gm_db_usr:gm_db_pwd@localhost/gm_db')


class Production(object):
    """
    Production environment configurations
    """
    DEBUG = False
    TESTING = False
    # switch off recommended in production mode
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')


# this variable will be imported by the app when initializing
app_config = {
    'development': Development,
    'production': Production,
}
