from flask import Blueprint, render_template, url_for, redirect, request
from .models import db, UserRegister, UserAuth
from .access_db import add_userauth, delete_userauth, update_userauth

authorization = Blueprint("authorize", __name__)

@authorization.route("/authorize", methods = ["GET", "POST"])
def authorize(*args, **kwargs):
    if request.method == 'GET':
        m = request.args["secret_code"]
        print(m)
        user_register = UserRegister.query.filter_by(m=m).first()
        if user_register is None:
            return render_template('404.html')
        return render_template('login.html', m=m)

    elif request.method == "POST":
        m = request.form["secret_code"]
        user_register = UserRegister.query.filter_by(m=m).first()
        
        u = request.form["u"]
        p = request.form["p"]
        user_id = user_register.user_id
        user_auth = UserAuth.query.filter_by(user_id=user_id).first()
        if user_auth is None:
            add_userauth(db, user_id, u, p)
        else:
            update_userauth(db, user_id, u, p)

        # Delete after use.
        UserRegister.query.filter_by(m=m).delete()
        db.session.commit()

        return render_template('response.html')
        
        