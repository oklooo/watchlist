#创建程序实例，初始化扩展的代码放到包构造文件里
import os
import sys

from flask import Flask 
from flask_sqlalchemy import SQLAlchemy 
from flask_login import LoginManager



app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY','dev')
#更新这里的路径，把app.root_path添加到os.path.dirname()中
#以便把文件定位到项目根目录
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////' + os.path.join(os.path.dirname(app.root_path),os.getenv('DATABASE_FILE','data.db'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] =False 

db = SQLAlchemy(app)
login_manager = LoginManager(app)

@login_manager.user_loader
def load_user(user_id):
    from watchlist.models import User 
    user = User.query.get(int(user_id))
    return user

login_manager.login_view = 'login'

@app.context_processor
def injecet_user():
    from watchlist.models import User
    user = User.query.first()
    return dict(user=user)



from watchlist import views,errors,commands

