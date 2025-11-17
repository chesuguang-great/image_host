# app.py - Flask主应用
from dotenv import load_dotenv
from flask import Flask
from api.upload import upload_bp
from api.delete import delete_bp
# from api.cleanup import cleanup_bp

load_dotenv()

app = Flask(__name__)
app.register_blueprint(upload_bp, url_prefix='/api')
app.register_blueprint(delete_bp, url_prefix='/api')
# app.register_blueprint(cleanup_bp, url_prefix='/api')

if __name__ == '__main__':
    app.run()