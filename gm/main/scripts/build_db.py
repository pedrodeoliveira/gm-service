from gm.main.models.model import db
from gm.main.app import create_app

app = create_app()

if __name__ == '__main__':
    app.create_all(app=app)
