from flask import Flask,render_template 
from flask_sqlalchemy import SQLAlchemy #导入扩展类
from flask import request, url_for,redirect,flash
import os
import sys
import click

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////' + os.path.join(app.root_path, 'data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 关闭对模型修改的监控
app.config['SECRET_KEY'] = 'dev'
db = SQLAlchemy(app) #初始化扩展，传入程序实例app,写入配置语句一般放到扩展类实例化语句之前

class User(db.Model): #表名将会是user(自动生成，小写处理)
    id = db.Column(db.Integer,primary_key=True) #主键
    name = db.Column(db.String(20)) #名字

class Movie(db.Model): #表名将会是movie
    id = db.Column(db.Integer,primary_key=True) #主键
    title = db.Column(db.String(60)) #电影标题
    year = db.Column(db.String(4))  #电影年份



@app.cli.command()
def forge():
    """Generate fake data."""

    db.create_all()
    #全局的两个变量移动到这个函数内
    name = 'Grey Li'
    movies = [
    {'title':'My Neighbor Totoro', 'year':'1988'},
    {'title':'Dead Poets Society', 'year':'1989'},
    {'title':'A Perfect World', 'year':'1993'},
    {'title':'Leon', 'year':'1994'},
    {'title':'Mahjong', 'year':'1996'},
    {'title':'Swallowtail Butterflty', 'year':'1996'},
    {'title':'King of Comedy', 'year':'1999'},
    {'title':'Devils on the Doorstep','year':'1999'},
    {'title':'WALL-E','year':'2008'},
    {'title':'The Pork of Music','year':'2012'},
    ]

    user = User(name=name)
    db.session.add(user)
    for m in movies:
        movie = Movie(title=m['title'],year=m['year'])
        db.session.add(movie)

    db.session.commit()
    click.echo('Done.')


@app.context_processor #模板上下文处理函数
def inject_user(): 
    user = User.query.first()
    return dict(user=user) #需要返回字典，等同于return{'user':user}

@app.route('/', methods=['GET','POST'])
def index():
    if request.method == "POST":
        title = request.form.get('title')
        year = request.form.get('year')
        #验证数据
        if not title or not year or len(year) > 4 or len(title) > 60:
            flash('Invalid input.') #显示错误提示
            return redirect(url_for('index'))
        #保存表单数据到数据库
        movie = Movie(title=title,year=year)
        db.session.add(movie)
        db.session.commit()
        flash('Item created.')
        return redirect(url_for('index'))

    user = User.query.first() # 读取用户记录
    movies = Movie.query.all() # 读取所有电影记录
    return render_template('index.html',movies=movies)

@app.errorhandler(404)
def page_not_found(e):
    user = User.query.first()
    return render_template('404.html'),404  #返回模板和状态码

@app.route('/movie/edit/<int:movie_id>',methods=['GET','POST'])
def edit(movie_id):
    movie = Movie.query.get_or_404(movie_id)

    if request.method == 'POST':
        title = request.form['title']
        year = request.form['year']

        if not title or not year or len(year) > 4 or len(title) > 60:
            flash('Invalid input.')
            return redirect(url_for('edit', movie_id=movie_id))

        movie.title = title
        movie.year = year
        db.session.commit()
        flash('Item updated.')
        return redirect(url_for('index'))
    return render_template('edit.html', movie = movie)

@app.route('/movie/delete/<int:movie_id>',methods=['POST'])
def delete(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    db.session.delete(movie)
    db.session.commit()
    flash('Item deleted.')
    return redirect(url_for('index'))