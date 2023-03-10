import toml
from datetime import datetime

from flask import Flask, redirect, render_template, request, url_for
from flask_login import (LoginManager, UserMixin, current_user, login_required,
                         login_user, logout_user)
from flask_sqlalchemy import SQLAlchemy

LOG_TRANSACTIONS = True
config = toml.load("config.toml")
PRICE_PER_COFFEE = config["price_per_coffee"]
FOAM_SYSTEM_INTERVAL = config["foam_system_interval"]
FOAM_SYSTEM_REWARD = config["foam_system_reward"]
DEEP_CLEANING_INTERVAL = config["deep_cleaning_interval"]
DEEP_CLEANING_REWARD = config["deep_cleaning_reward"]

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.sqlite3'
app.config['SECRET_KEY'] = 'secret'
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'index'


def foam_system_is_available():
    """returns true if the foam system can be cleaned. It can be cleaned once every 24 hours."""
    last_transaction = Transaction.query.filter_by(note="foam system").order_by(Transaction.date.desc()).first()
    return (datetime.now() - last_transaction.date).total_seconds() > FOAM_SYSTEM_INTERVAL if last_transaction else True


def deep_cleaning_is_available():
    """returns true if the deep cleaning can be done. It can be done once every 24 hours."""
    last_transaction = Transaction.query.filter_by(note="deep cleaning").order_by(Transaction.date.desc()).first()
    return (datetime.now() - last_transaction.date).total_seconds() > DEEP_CLEANING_INTERVAL if last_transaction else True


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    password = db.Column(db.String(100))
    email = db.Column(db.String(100))
    balance = db.Column(db.Float)
    is_admin = db.Column(db.Boolean, default=False)

    def transaction(self, amount, note):
        self.balance = round(self.balance + amount, 2)
        # admin = User.query.filter_by(is_admin=True).first()
        # admin.balance = round(admin.balance - amount, 2)
        if LOG_TRANSACTIONS:
            transaction = Transaction(user_id=self.id, amount=round(amount, 5), date=datetime.now(), note=note)
            db.session.add(transaction)
        db.session.commit()

    def take_coffee(self):
        self.transaction(-PRICE_PER_COFFEE, "coffee")

    def add_money(self, amount):
        self.transaction(amount, "add money")

    def foam_system(self):
        self.transaction(FOAM_SYSTEM_REWARD, "foam system")

    def deep_cleaning(self):
        self.transaction(DEEP_CLEANING_REWARD, "deep cleaning")
        return True


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref=db.backref('transactions', lazy=True))
    amount = db.Column(db.Float)
    date = db.Column(db.DateTime)
    note = db.Column(db.String(100))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/take-coffee', methods=['POST'])
@login_required
def endpoint_take_coffee():
    current_user.take_coffee()
    return redirect(url_for('dashboard'))


@app.route('/deep-cleaning', methods=['POST'])
@login_required
def endpoint_deep_cleaning():
    if deep_cleaning_is_available():
        current_user.deep_cleaning()
        deep_cleaning = {"success": "Deep cleaning is done."}
    else:
        deep_cleaning = {"error": "Deep cleaning is not available yet."}
    return redirect(url_for('dashboard', deep_cleaning=deep_cleaning))


@app.route('/foam-system', methods=['POST'])
@login_required
def endpoint_foam_system():
    if foam_system_is_available():
        current_user.foam_system()
        foam_system = {"Foam system is cleaned."}
    else:
        foam_system = {"error": "Foam system is not available yet."}
    return redirect(url_for('dashboard', foam_system=foam_system, dings=True))


@app.route('/add-money', methods=['POST'])
@login_required
def endpoint_add_money():
    return redirect(url_for('dashboard'))


@app.route('/update-user/<user_id>', methods=['POST', 'GET'])
@login_required
def endpoint_update_user(user_id):
    if not user_is_admin(current_user):
        return redirect(url_for('dashboard'))
    user = User.query.get(user_id)
    if request.method.upper() == "POST":
        print("post")
        user.balance = float(request.form.get("new_balance"))
        db.session.commit()
        return redirect(url_for('dashboard'))
    return redirect(url_for('dashboard'))


@app.route("/")
def index():
    return render_template("base.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if not user:
            return render_template("login.html", wrong_credentials=True)
        if user.password == password:
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            return render_template("login.html", wrong_credentials=True)

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return render_template("login.html")


def register_user(username, password, email, balance=0):
    new_user = User(username=username, password=password, balance=balance, email=email)
    db.session.add(new_user)
    db.session.commit()
    return new_user


@ app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        email = request.form.get("email")

        error_messages = set()
        if len(username) < 4 or len(password) < 4:
            error_messages.add("Username and password have to be at least four characters long.")
        if User.query.filter_by(username=username).first():
            error_messages.add("Username already exists.")
        if User.query.filter_by(email=email).first():
            error_messages.add("Email already exists.")
        if error_messages:
            return render_template("register.html", error_messages=error_messages)
        new_user = register_user(username, password, email, balance=0)
        login_user(new_user)
        return redirect(url_for("dashboard"))
    return render_template("register.html")


@ app.route("/dashboard")
@ login_required
def dashboard():
    if user_is_admin(current_user):
        return redirect(url_for('admin'))
    return render_template("dashboard.html", user=current_user)


@app.route("/admin", methods=["POST", "GET"])
@login_required
def admin():
    if not user_is_admin(current_user):
        return redirect(url_for('dashboard'))
    users = User.query.all()
    # users = [user.__dict__ for user in User.query.all()]
    # for user in users:del user["_sa_instance_state"]
    return render_template("dashboard.html", user=current_user, admin=True, users=users)


def user_is_admin(user):
    return user.is_admin


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="127.0.0.1", port=8000)
