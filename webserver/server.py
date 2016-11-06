#!/usr/bin/env python2.7

"""
Columbia W4111 Intro to databases
Example webserver

To run locally

    python server.py

Go to http://localhost:8111 in your browser


A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os
import gc
from functools import wraps
from flask import url_for
from wtforms import Form, TextField, PasswordField
from sqlalchemy import *
import validators as validators
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, url_for, redirect, session, flash, Response, jsonify
from sqlalchemy.orm import sessionmaker
from MySQLdb import escape_string as thwart

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
app.secret_key = "super secret key"

#
# The following uses the postgresql test.db -- you can use this for debugging purposes
# However for the project you will need to connect to your Part 2 database in order to use the
# data
#
# XXX: The URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@<IP_OF_POSTGRE_SQL_SERVER>/postgres
#
# For example, if you had username ewu2493, password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://ewu2493:foobar@<IP_OF_POSTGRE_SQL_SERVER>/postgres"
#
# Swap out the URI below with the URI for the database created in part 2

DATABASEURI = "postgresql://kc3031:p923n@104.196.175.120/postgres"

#
# This line creates a database engine that knows how to connect to the URI above
#
engine = create_engine(DATABASEURI)

#
# START SQLITE SETUP CODE
#
# after these statements run, you should see a file test.db in your webserver/ directory
# this is a sqlite database that you can query like psql typing in the shell command line:
# 
#     sqlite3 test.db
#
# The following sqlite3 commands may be useful:
# 
#     .tables               -- will list the tables in the database
#     .schema <tablename>   -- print CREATE TABLE statement for table
# 
# The setup code should be deleted once you switch to using the Part 2 postgresql database
#
engine.execute("""DROP TABLE IF EXISTS test;""")
engine.execute("""CREATE TABLE IF NOT EXISTS test (
  id serial,
  name text
);""")
engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")


#
# END SQLITE SETUP CODE
#



@app.before_request
def before_request():
    """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request

  The variable g is globally accessible
  """
    try:
        g.conn = engine.connect()
    except:
        print "uh oh, problem connecting to database"
        import traceback;
        traceback.print_exc()
        g.conn = None


@app.teardown_request
def teardown_request(exception):
    """
  At the end of the web request, this makes sure to close the database connection.
  If you don't the database could run out of memory!
  """
    try:
        g.conn.close()
    except Exception as e:
        pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to e.g., localhost:8111/foobar/ with POST or GET then you could use
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/')
def index():
    """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
  """

    # DEBUG: this is debugging code to see what request looks like
    print request.args

    #
    # example of a database query
    #
    cursor = g.conn.execute("SELECT title, abstract, content FROM item")
    data = []
    for result in cursor:
        data.append(result)
    cursor.close()

    #
    # Flask uses Jinja templates, which is an extension to HTML where you can
    # pass data to a template and dynamically generate HTML based on the data
    # (you can think of it as simple PHP)
    # documentation: https://realpython.com/blog/python/primer-on-jinja-templating/
    #
    # You can see an example template in templates/index.html
    #
    # context are the variables that are passed to the template.
    # for example, "data" key in the context variable defined below will be
    # accessible as a variable in index.html:
    #
    #     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
    #     <div>{{data}}</div>
    #
    #     # creates a <div> tag for each element in data
    #     # will print:
    #     #
    #     #   <div>grace hopper</div>
    #     #   <div>alan turing</div>
    #     #   <div>ada lovelace</div>
    #     #
    #     {% for n in data %}
    #     <div>{{n}}</div>
    #     {% endfor %}
    #
    context = dict(data=data)

    #
    # render_template looks in the templates/ folder for files.
    # for example, the below file reads template/index.html
    #
    return render_template("index.html", **context)


#
# This is an example of a different path.  You can see it at
# 
#     localhost:8111/another
#
# notice that the functio name is another() rather than index()
# the functions for each app.route needs to have different names
#
@app.route('/another')
def another():
    return render_template("anotherfile.html")


@app.route('/content', methods=['GET', 'POST'])
def content():
    contents = []
    t = request.args.get('title')
    contents.append(t)
    cursor = g.conn.execute("SELECT abstract FROM item WHERE title = %s;", t)
    for result in cursor:
        contents.append(result[0])
    cursor = g.conn.execute("SELECT content FROM item WHERE title = %s;", t)
    for result in cursor:
        contents.append(result[0])
    cursor.close()
    contents.append('content')
    context = dict(data=contents)
    return render_template("content.html", **context)


# @app.route('/', methods=['GET', 'POST'])
# def content():
#     title = request.args.get('title')
#     cursor = g.conn.execute("SELECT abstract FROM item WHERE title = %s;", t)
#     abstracts = []
#     for result in cursor:
#         abstracts.append(result[0])
#     cursor = g.conn.execute("SELECT content FROM item WHERE title = %s;", t)
#     contents = []
#     for result in cursor:
#         contents.append(result[0])
#     cursor.close()
#     return jsonify(title=title, abstracts=abstracts, contents=contents)

@app.route('/user_login', methods=['GET', 'POST'])
def user_login():
    try:
        if request.method == "POST":
            cursor = g.conn.execute("SELECT password FROM users WHERE email = (%s);", request.form['email'])
            for result in cursor:
                pwd = result[0]
            if request.form['password'] == pwd:
                session['email'] = request.form['email']
                return redirect('/profile')
            else:
                return render_template("login_error.html")
        gc.collect()
        return render_template("user_login.html")

    except Exception as e:
        return render_template("login_error.html")


def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'email' in session:
            return f(*args, **kwargs)
        else:
            return redirect('/user_login')
    return wrap

@app.route('/user_logout')
@login_required
def user_logout():
    session.clear()
    gc.collect()
    return render_template("user_logout.html")

@app.route('/get_session')
def get_session():
    if 'email' in session:
        return session['email']

    return "Not Logged In!"


class RegistrationForm(Form):
    email = TextField('Email')
    password = PasswordField('Password')
    username = TextField('Username')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    RegistrationForm
    """
    try:
        form = RegistrationForm(request.form)
        if request.method == "POST":
            email = form.email.data
            username = form.username.data
            password = form.password.data
            g.conn = engine.connect()
            g.conn.execute("INSERT INTO users (email, password, user_name) VALUES (%s, %s, %s);",
                               (email, password, username))
            g.conn.close()
            gc.collect()
            session['email'] = email
            return redirect('/profile')
        return render_template("register.html", form=form)
    except Exception as e:
        return "User already exists!"


@app.route('/profile')
def profile():
    if 'email' in session:
        contents = []
        contents.append(session['email'])
        cursor = g.conn.execute("SELECT password FROM users WHERE email = %s;", session['email'])
        for result in cursor:
            contents.append(result[0])
        cursor = g.conn.execute("SELECT user_name FROM users WHERE email = %s;", session['email'])
        for result in cursor:
            contents.append(result[0])

        list = []
        cursor = g.conn.execute("SELECT DISTINCT iid FROM user_view WHERE email = %s;", session['email'])
        for result in cursor:
            list.append(result)
        for id in list:
            cursor = g.conn.execute("SELECT DISTINCT title FROM item WHERE iid = %s;", id)
            for result in cursor:
                contents.append("View  : " + result[0])

        list = []
        cursor = g.conn.execute("SELECT DISTINCT iid FROM user_fave WHERE email = %s;", session['email'])
        for result in cursor:
            list.append(result)
        for id in list:
            cursor = g.conn.execute("SELECT DISTINCT title FROM item WHERE iid = %s;", id)
            for result in cursor:
                contents.append("Fave  : " + result[0])

        list = []
        cursor = g.conn.execute("SELECT DISTINCT iid FROM user_share WHERE email = %s;", session['email'])
        for result in cursor:
            list.append(result)
        for id in list:
            cursor = g.conn.execute("SELECT DISTINCT title FROM item WHERE iid = %s;", id)
            for result in cursor:
                contents.append("Share: " + result[0])

        cursor.close()
        context = dict(data=contents)
        return render_template("profile.html", **context)
    else:
        return redirect('/user_login')
        return render_template("user_login.html")


# Example of adding new data to the database
@app.route('/add', methods=['POST'])
def add():
    name = request.form['name']
    print name
    cmd = 'INSERT INTO test(name) VALUES (:name1), (:name2)';
    g.conn.execute(text(cmd), name1=name, name2=name);
    return redirect('/')


@app.route('/login')
def login():
    abort(401)
    this_is_never_executed()


if __name__ == "__main__":
    import click


    @click.command()
    @click.option('--debug', is_flag=True)
    @click.option('--threaded', is_flag=True)
    @click.argument('HOST', default='0.0.0.0')
    @click.argument('PORT', default=8111, type=int)
    def run(debug, threaded, host, port):
        """
    This function handles command line parameters.
    Run the server using

        python server.py

    Show the help text using

        python server.py --help

    """

        HOST, PORT = host, port
        print "running on %s:%d" % (HOST, PORT)
        app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


    run()
