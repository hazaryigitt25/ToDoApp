from flask import Flask,flash,render_template,session,redirect,url_for,request
from flask_sqlalchemy import SQLAlchemy
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps

#Login required
# User Login Decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged in" in session:
            return f(*args, **kwargs)
        else:
            flash("You Have To Log In Idiot!","danger")
            return redirect(url_for("login"))
    return decorated_function

#Creating Forms
class RegisterForm(Form):
    username = StringField("User Name",validators=[validators.length(max=15,min=3,message="User name should be 3-15 digits.")])
    password = PasswordField("Password",validators=[
        validators.length(min=5,message="Password must be at least 5 digits."),
        validators.EqualTo(fieldname="confirm",message="Passwords does not match"),
        validators.DataRequired(message="You must have password")
    ])
    confirm = PasswordField("Confirm Your Password")
    
class LoginForm(Form):
    username = StringField("Username")
    password = PasswordField("Password")
    
class todoform(Form):
    title = StringField("ToDo Title",validators=[validators.length(max=15)])
    content = StringField("Subtitles(separete with ',')",validators=[validators.DataRequired(message="You must have contents")])
    

# Creating Frame
app = Flask(__name__)
app.secret_key = 'super secret key'

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///C:/Users/Admin/vscode/TodoApp3/todo.db"

db = SQLAlchemy(app)
app.app_context().push()

# Creating Website
@app.route("/deletetitle/<string:id>")
@login_required
def deletetitle(id):
    title = TodoTitle.query.filter_by(id=id).first()
    db.session.delete(title)
    db.session.commit()
    todos = TodoList.query.filter_by(title_id=id).all()
    for todo in todos:
        db.session.delete(todo)
    db.session.commit()
    return redirect(url_for("dashboard"))

@app.route("/delete/<string:id>")
@login_required
def delete(id):
    todo = TodoList.query.filter_by(id=id).first()
    title = TodoTitle.query.filter_by(id=todo.title_id).first()
    db.session.delete(todo)
    db.session.commit()
    todos = TodoList.query.filter_by(title_id=todo.title_id).all()
    comp = list()
    for i in todos:
        comp.append(i.complete)
    if all(comp):
        title = TodoTitle.query.filter_by(id=todo.title_id).first()
        title.complete = True
        db.session.commit()
    else:
        title = TodoTitle.query.filter_by(id=todo.title_id).first()
        title.complete = False
        db.session.commit()
    return redirect(url_for("todo",id=title.id))

@app.route("/complete/<string:id>")
@login_required
def complete(id):
    todo = TodoList.query.filter_by(id=id).first()
    todo.complete = not todo.complete
    db.session.commit()
    todos = TodoList.query.filter_by(title_id=todo.title_id).all()
    comp = list()
    for i in todos:
        comp.append(i.complete)
    if all(comp):
        title = TodoTitle.query.filter_by(id=todo.title_id).first()
        title.complete = True
        db.session.commit()
    else:
        title = TodoTitle.query.filter_by(id=todo.title_id).first()
        title.complete = False
        db.session.commit()
    return redirect(url_for("todo",id=title.id))

@app.route("/todo/<string:id>")
@login_required
def todo(id):
    title = TodoTitle.query.filter_by(id=id).first()
    contents = TodoList.query.filter_by(title_id=id).all()
    print(contents)
    return render_template("todo.html",contents=contents,title=title.title)

@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash("You have successfully logged out","info")
    return redirect(url_for("index"))

@app.route("/create",methods=["GET","POST"])
@login_required
def create():
    form = todoform(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data
        contents = content.split(",")
        newtitle = TodoTitle(title=title,complete=False,user=session["user"])
        db.session.add(newtitle)
        db.session.commit()
        title_id = TodoTitle.query.filter_by(user=session["user"],title=title).first()
        for content in contents:
            newcontent = TodoList(user=session["user"],title_id=title_id.id,complete=False,content=content)
            db.session.add(newcontent)
            db.session.commit()
        return redirect(url_for("dashboard"))
    return render_template("create.html",form=form)

@app.route("/login",methods=["GET","POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST":
        name = form.username.data
        password = form.password.data
        control = User.query.filter_by(name=name).first()
        if control is None:
            flash("User Could Not Found","danger")
            return redirect(url_for("login"))
        if sha256_crypt.verify(password,control.password):
            session["logged in"] = True
            session["user"] = name
            flash("You have successfully logged in","success")
            return redirect(url_for("dashboard"))
        else:
            flash("Password is wrong","danger")
            return redirect(url_for("login"))
    return render_template("login.html",form=form)

@app.route("/dashboard")
@login_required
def dashboard():
    titles = TodoTitle.query.filter_by(user=session["user"])
    
    return render_template("dashboard.html",titles=titles)
 
@app.route("/register",methods=["GET","POST"])
def register():
    form = RegisterForm(request.form)
    if request.method == "POST" and form.validate():
        name = form.username.data
        control = User.query.filter_by(name=name).first()
        if control is not None:
            flash("Username has taken","danger")
            return redirect(url_for("register"))
        newuser = User(name = name)
        password = sha256_crypt.encrypt(form.password.data)
        newuser.password = password
        db.session.add(newuser)
        db.session.commit()
        session["logged in"] = True
        session["user"] = name
        flash("You have been registered successfully","success")
        return redirect(url_for("dashboard"))
    return render_template("register.html",form=form)

@app.route("/learn")
def learn():
    return render_template("learn.html")

@app.route("/")
def index():
    return render_template("index.html")

# Creating Data Base
class TodoTitle(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    user = db.Column(db.String(80))
    title = db.Column(db.String(80))
    complete = db.Column(db.Boolean)
    
class TodoList(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    user = db.Column(db.String(80))
    title_id = db.Column(db.Integer)
    content = db.Column(db.String(80))
    complete = db.Column(db.Boolean)
    
class User(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(80))
    password = db.Column(db.String(300))

if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)


