from watchlist import app
from watchlist.models import User
from flask import Flask,render_template 

@app.errorhandler(404)
def page_not_found(e):
    user = User.query.first()
    return render_template('errors/404.html'),404  #返回模板和状态码