from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///acc_portal.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "acc-portal-secret-key"

db = SQLAlchemy(app)


# =========================
# USER MODEL
# =========================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    student_id = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)


# =========================
# HOME
# =========================

@app.route("/")
def home():
    return render_template("index.html")


# =========================
# REGISTER
# =========================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        full_name = request.form.get("full_name")
        student_id = request.form.get("student_id")
        email = request.form.get("email")
        password = request.form.get("password")

        existing_email = User.query.filter_by(email=email).first()

        existing_student_id = User.query.filter_by(
            student_id=student_id
        ).first()

        if existing_email:
            flash("Email is already registered.")
            return redirect(url_for("register"))

        if existing_student_id:
            flash("Student ID is already registered.")
            return redirect(url_for("register"))

        # Hash password before saving
        hashed_password = generate_password_hash(password)

        new_user = User(
            full_name=full_name,
            student_id=student_id,
            email=email,
            password=hashed_password
        )

        db.session.add(new_user)
        db.session.commit()

        flash("User registered successfully!")

        return redirect(url_for("users"))

    return render_template("register.html")


# =========================
# LOGIN
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):

            session["user_id"] = user.id
            session["user_name"] = user.full_name

            flash("Login successful!")

            return redirect(url_for("users"))

        flash("Invalid email or password.")

    return render_template("login.html")


# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():

    session.clear()

    flash("You have been logged out.")

    return redirect(url_for("login"))


# =========================
# USERS / SEARCH
# =========================

@app.route("/users")
def users():

    search = request.args.get("search", "").strip()

    if search:

        all_users = User.query.filter(
            db.or_(
                User.full_name.ilike(f"%{search}%"),
                User.student_id.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%")
            )
        ).all()

    else:

        all_users = User.query.all()

    return render_template(
        "users/index.html",
        users=all_users,
        search=search
    )


# =========================
# EDIT USER
# =========================

@app.route("/users/edit/<int:user_id>", methods=["GET", "POST"])
def edit_user(user_id):

    user = User.query.get_or_404(user_id)

    if request.method == "POST":

        full_name = request.form.get("full_name")
        student_id = request.form.get("student_id")
        email = request.form.get("email")

        existing_email = User.query.filter(
            User.email == email,
            User.id != user.id
        ).first()

        existing_student_id = User.query.filter(
            User.student_id == student_id,
            User.id != user.id
        ).first()

        if existing_email:

            flash("Email is already used by another user.")

            return redirect(
                url_for("edit_user", user_id=user.id)
            )

        if existing_student_id:

            flash("Student ID is already used by another user.")

            return redirect(
                url_for("edit_user", user_id=user.id)
            )

        user.full_name = full_name
        user.student_id = student_id
        user.email = email

        db.session.commit()

        flash("User updated successfully!")

        return redirect(url_for("users"))

    return render_template(
        "users/edit.html",
        user=user
    )


# =========================
# DELETE USER
# =========================

@app.route("/users/delete/<int:user_id>", methods=["POST"])
def delete_user(user_id):

    user = User.query.get_or_404(user_id)

    db.session.delete(user)
    db.session.commit()

    flash("User deleted successfully!")

    return redirect(url_for("users"))


# =========================
# RUN APPLICATION
# =========================

if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    app.run(debug=True)