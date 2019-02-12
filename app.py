from flask import Flask,render_template 
from flask_sqlalchemy import SQLAlchemy #导入扩展类
from flask import request, url_for,redirect,flash
from werkzeug.security import generate_password_hash,check_password_hash
from flask_login import LoginManager
from flask_login import UserMixin
from flask_login import login_user
from flask_login import login_required,logout_user
from flask_login import login_required,current_user
import os
import sys
import click

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////' + os.path.join(app.root_path, 'data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 关闭对模型修改的监控
app.config['SECRET_KEY'] = 'dev'
db = SQLAlchemy(app) #初始化扩展，传入程序实例app,写入配置语句一般放到扩展类实例化语句之前
login_manager = LoginManager(app) #实例化扩展类
login_manager.login_view = 'login'
class User(db.Model,UserMixin): #表名将会是user(自动生成，小写处理)
    id = db.Column(db.Integer,primary_key=True) #主键
    name = db.Column(db.String(20)) #名字
    username =  db.Column(db.String(20))#用户名
    password_hash = db.Column(db.String(128)) #密码散列值

    def set_password(self,password): #用来设置密码的方法，接受密码作为参数
        self.password_hash = generate_password_hash(password) #将生成的密码保持到对应字段

    def validate_password(self,password): #用于验证密码的方法，接受密码作为参数
        return check_password_hash(self.password_hash,password) #返回布尔值               

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
        if not current_user.is_authenticated:
            return redirect(url_for('index'))
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
@login_required
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
@login_required
def delete(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    db.session.delete(movie)
    db.session.commit()
    flash('Item deleted.')
    return redirect(url_for('index'))

@app.cli.command()   #注册为命令
@click.option('--drop', is_flag=True, help='Create after drop.') #设置选项
def initdb(drop):
    """Initialize the database."""
    if drop:
        db.drop_all()
    db.create_all()
    click.echo('Initialized database.')

@app.cli.command()
@click.option('--username',prompt=True,help='The username used to login.')
@click.option('--password',prompt=True,hide_input=True,confirmation_prompt=True,help="The password used to login.")
def admin(username,password):
    """Create user."""
    db.create_all()

    user = User.query.first()
    if user is not None:
        click.echo('Updating user...')
        user.username = username
        user.set_password(password)
    else:
        click.echo('Creating user...')
        user = User(username=username, name='Admin')
        user.set_password(password)
        db.session.add(user)

    db.session.commit()
    click.echo('Done.')

@login_manager.user_loader
def load_user(user_id): #创建用户加载回调函数，接受用户ID作为参数
    user = User.query.get(int(user_id))
    return user

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash('Invalid input.')
            return redirect(url_for('login'))

        user = User.query.first()
        if username == user.username and user.validate_password(password):
            login_user(user)
            flash('login success.')
            return redirect(url_for('index'))

        flash('Invalid username or password.')
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Goodbye.')
    return redirect(url_for('index'))

@app.route('/settings',methods=['GET','POST'])
@login_required
def settings():
    if request.method == 'POST':
        name = request.form['name']
        if not name or len(name) > 20:
            flash('Invalid input.')
            return redirect(url_for('settings'))

        current_user.name = name
        db.session.commit()
        flash('Settings updated.')
        return redirect(url_for('index'))
    return render_template('settings.html')