from flask import Flask, g, request, Response, make_response, send_file
from flask import session, render_template, Markup, url_for, redirect
from datetime import date, datetime, timedelta
import os
from init_db import init_database, db_session, User, Post, Signature, Notice
from flask import flash
from datetime import datetime
from werkzeug.utils import secure_filename
from urllib.parse import urlparse
import zipfile


init_database()  # init database

app = Flask(__name__)
admin_list = [1]

@app.route('/')  # main page
def idx():
    result = db_session.query(Post).all()
    return render_template("main.html", result=result[:4])

@app.route('/notice', methods=['GET'])  #  show notice posts
def notice():
    result = db_session.query(Notice).all()

    return render_template("notice.html", result=result)

@app.route('/notice_writing', methods=['POST'])  # upload notice posts
def notice_writing_post():
    user_id = session['loginUser']["userid"]
    username = session['loginUser']["name"]
    title = request.form['title']
    content = request.form['content']
    created_at = datetime.now()

    if len(title) == 0 or len(content) == 0:
        flash("Wrong input")
        return redirect(request.referrer)

    n = Notice(user_id, username, title, content, created_at)
    db_session.add(n)
    db_session.commit()
    return redirect("/notice")

@app.route('/notice_writing', methods=['GET'])   # only admin user can enter writing notice page
def notice_writing():
    if session['loginUser'] is None:  # not login state
        redirect("/login")
    elif session['loginUser']["userid"] in admin_list:  # whether user is admin
        return render_template("notice_writing.html")
    else:
        flash("You can not access notice writing")
        return redirect('/notice')

@app.route('/notice_detail', methods=['GET'])  # detailed notice post page
def notice_detail():
    post_id = request.args.get('post_id', default=-1, type = int)
    post = db_session.query(Notice).filter_by(id=post_id).first()

    return render_template("notice_detail.html", post=post)


@app.route('/login', methods=['GET'])  # login page
def login():
    return render_template("login.html")


@app.route('/login', methods=['POST'])  # login request
def login_post():
    email = request.form['email']
    passwd = request.form['password']
    u = db_session.query(User).filter_by(email=email, passwd=passwd).first()

    if u is not None:
        session['loginUser'] = {'userid': u.id, 'name': u.name}
        return redirect('/')
    else:
        flash("Invaild account")  # there is no such account
        return render_template("login.html", email=email)


@app.route('/logout')  # log out button
def logout():
    if session.get('loginUser'):
        del session['loginUser']

    return redirect('/')


@app.route('/signup', methods=['get'])  # go to the sign up page
def signup():
    return render_template("signup.html")


@app.route('/signup', methods=['POST'])  # request sign up
def signup_post():
    email = request.form['email']
    passwd = request.form['password']
    passwd_confirm = request.form['password_confirm']
    name = request.form['name']
    major = request.form['major']
    studentid = request.form['studentid']

    if passwd != passwd_confirm:  # password confirm check
        flash("Please input same password!")
        return render_template("signup.html", email=email, name=name)
    elif len(email) == 0 or len(passwd) == 0 or len(name) == 0 or len(major) == 0 or len(studentid) == 0:  # There is a blank
        flash("Fill the blanks")
        return render_template("signup.html")
    else:                                                          # login success
        u = User(email, passwd, name, major, studentid)
        if db_session.query(User).filter_by(email=email).first() is None:
            db_session.add(u)
            db_session.commit()
            return redirect("/login")
        else:
            flash("Duplicated email!")


@app.route('/club', methods=['GET'])  # signature for club page
def club():
    result = db_session.query(Post).filter_by(board='Club').all()

    return render_template("club.html", result=result)

@app.route('/suggestion', methods=['GET'])  # signature for suggestion page
def suggestion():
    result = db_session.query(Post).filter_by(board='Suggestion').all()

    return render_template("suggestion.html", result=result)


@app.route('/writing', methods=['GET'])  # go to the writing a post page for club or suggestion
def writing():
    if 'loginUser' not in session.keys():
        redirect("/login")
    else:
        board = request.args.get('board', type=str)
        return render_template("writing.html", board=board)

@app.route('/writing', methods=['POST'])  # upload post for club or suggestion
def writing_post():
    parts = urlparse(request.referrer)
    board = parts.query.split('=')[1]

    user_id = session['loginUser']["userid"]
    username = session['loginUser']["name"]
    title = request.form['title']
    content = request.form['content']
    created_at = datetime.now()
    required_signature_num = request.form['num_signature']
    signature_num = 0

    if len(title) == 0 or len(content) == 0 or required_signature_num is None:  # blank input check
        flash("Wrong input")
        return redirect(request.referrer)
    elif board == "Club":  # signature for club
        p = Post(user_id, username, title, content, created_at, required_signature_num, signature_num, board)
        db_session.add(p)
        db_session.commit()
        return redirect("/club")
    elif board == "Suggestion":  # signature for suggestion
        p = Post(user_id, username, title, content, created_at, required_signature_num, signature_num, board)
        db_session.add(p)
        db_session.commit()
        return redirect("/suggestion")



@app.route('/detail', methods=['GET'])  # show detail infomation of post for club or suggestion
def detail():
    if 'loginUser' not in session.keys():
        return redirect("/login")
    else:
        post_id = request.args.get('post_id', default=-1, type = int)
        post = db_session.query(Post).filter_by(id=post_id).first()
        return render_template("detail.html", post=post)

@app.route('/upload', methods=['POST'])  # upload signature file
def upload():
    f = request.files['file']

    if len(f.filename) == 0:  # user did not attach file
        flash("You did not attach signature file")
        return redirect(request.referrer)

    parts = urlparse(request.referrer)  # parse url for post_id
    query = parts.query.split('&')
    post_id = query[1]
    post_id = post_id.split('=')[1]

    user_id = session['loginUser']["userid"]
    type = f.filename[-4:]
    s = db_session.query(Signature).filter_by(post_id=post_id, user_id=user_id).first()

    if s is None:  # The user have not uploaded the signature to this post
        sign = Signature(post_id, user_id)
        db_session.add(sign)
        db_session.commit()
        p = db_session.query(Post).filter_by(id=post_id).first()
        p.signature_num = p.signature_num + 1
        db_session.commit()

    else:  # The user have uploaded the signature to this post
        flash("You already signed this post")
        return redirect(request.referrer)

    signature_id = str(db_session.query(Signature).filter_by(post_id=post_id, user_id=user_id).first().id)  # file name: {signature id}.{format}, ex) 3.jpg
    f.save(os.path.join('./signatures', signature_id + type))
    flash("Upload completed")
    return redirect(request.referrer)

@app.route('/mypost', methods=['GET'])  # go to the my page
def mypost():
    user_id = session['loginUser']["userid"]
    result = db_session.query(Post).filter_by(user_id=user_id).all()
    return render_template("mypage.html", result=result)

@app.route('/mysignature', methods=['GET'])  # go to the mysignature tab in my page
def mysignature():
    user_id = session['loginUser']["userid"]
    sign_list = db_session.query(Signature).filter_by(user_id=user_id).all()
    signed_post = []

    for obj in sign_list:
        signed_post.append(db_session.query(Post).filter_by(id=obj.post_id).first())
    return render_template("mypage2.html", result=signed_post)


@app.route('/download', methods=['GET'])  # download signatures of the post
def download():
    post_id = request.args.get('post_id', default=-1, type=int)
    list = db_session.query(Signature).filter_by(post_id=post_id).all()
    print(list)
    owd = os.getcwd()
    zip_file = zipfile.ZipFile(owd + "\\output.zip", "w")
    file_path = owd + '\\signatures'
    for file in os.listdir(file_path):  #  make a zip file of signature files
        print('This is file  ', file)
        for obj in list:
            print(file[:-4], obj.id)
            if file[:-4] == str(obj.id):
                u = db_session.query(User).filter_by(id=obj.user_id).first()
                studentid = u.studentid
                major = u.major
                name = u.name
                type = file[-4:]
                new_file_name = studentid + "_" + major + "_" + name +type
                old_file = os.path.join(file_path, file)
                new_file = os.path.join(file_path, new_file_name)
                os.rename(old_file, new_file)
                zip_file.write(os.path.join(file_path, new_file_name), new_file_name, compress_type=zipfile.ZIP_DEFLATED)
                os.rename(new_file, old_file)
    zip_file.close()

    return send_file(owd + "\\output.zip", as_attachment=True)



if __name__ == "__main__":
    app.config['SECRET_KEY'] = 'wcsfeufhwiquehfdx'
    app.run(debug=True, host='localhost', port=8888)
