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
import datetime
from functools import wraps
from flask import url_for
from wtforms import Form, TextField, PasswordField
from sqlalchemy import *

from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, url_for, redirect, session, flash, Response, jsonify
from sqlalchemy.orm import sessionmaker
from requests.utils import quote
#from MySQLdb import escape_string as thwart

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

  """ CHECK USER_LOGIN """
  user = []
  if 'email' in session:
      user.append(true)
  #
  # example of a database query
  #
  """ LOADING ALL POSTS ONTO THE PAGE"""
  cursor = g.conn.execute("SELECT title, abstract, content FROM item")
  data = []
  for result in cursor:
    data.append(result)

  """ LOADING ALL DROP-DOWN OPTIONS FOR SUBJECT"""
  subject_options = []
  cursor = g.conn.execute("SELECT DISTINCT subject_name FROM subject")
  for result in cursor:
      subject_options.append(result[0])

  #print subject_options

  """ LOADING ALL DROP-DOWN OPTIONS FOR AUTHOR"""
  author_options = []
  cursor = g.conn.execute("SELECT DISTINCT author_name FROM author")
  for result in cursor:
      author_options.append(result[0])

  #print author_options

  """ LOADING ALL DROP-DOWN OPTIONS FOR PUBLISHER"""
  publisher_options = []
  cursor = g.conn.execute("SELECT DISTINCT publisher_name FROM publisher")
  for result in cursor:
      publisher_options.append(result['publisher_name'])

  #print publisher_options

  """ LOADING ALL DROP-DOWN OPTIONS FOR POLITICAL STANCE"""
  political_options = []
  cursor = g.conn.execute("SELECT DISTINCT political_stance FROM publisher")
  for result in cursor:
      political_options.append(result[0])

  #print political_options

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
  context = dict(user=user, data=data, subject_options=subject_options, publisher_options=publisher_options, political_options=political_options, author_options=author_options)


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

@app.route('/view/<title>', methods=['GET', 'POST'])
def view(title):
    url = []
    cursor = g.conn.execute("SELECT content FROM item WHERE title = %s;", title)
    for result in cursor:
        url.append(result[0])
    if 'email' in session:
        email = session['email']
        iid = []
        cursor = g.conn.execute("SELECT iid FROM item WHERE title = %s;", title)
        for result in cursor:
            iid.append(result[0])
        sid = []
        cursor = g.conn.execute("SELECT sid FROM cover WHERE iid = %s;", iid[0])
        for result in cursor:
            sid.extend(result)
        g.conn = engine.connect()
        print datetime.datetime.now()
        for subject_id in sid:
            g.conn.execute("INSERT INTO user_view (view_time, iid, sid, email) VALUES (%s, %s, %s, %s);",
                                      (datetime.datetime.now(), iid[0], subject_id, email))
        g.conn.close()
        gc.collect()
    return redirect(url[0])
    return render_template("index.html")

@app.route('/fb_share/<title>', methods=['GET', 'POST'])
def fb_share(title):
    url = []
    cursor = g.conn.execute("SELECT content FROM item WHERE title = %s;", title)
    for result in cursor:
        url.append('https://www.facebook.com/sharer/sharer.php?u=' + quote(result[0]))
    if 'email' in session:
        email = session['email']
        iid = []
        cursor = g.conn.execute("SELECT iid FROM item WHERE title = %s;", title)
        for result in cursor:
            iid.append(result[0])
        sid = []
        cursor = g.conn.execute("SELECT sid FROM cover WHERE iid = %s;", iid[0])
        for result in cursor:
            sid.append(result[0])
        g.conn = engine.connect()
        print datetime.datetime.now()
        g.conn.execute("INSERT INTO user_share (share_time, platform, iid, sid, email) VALUES (%s, %s, %s, %s, %s);",
                                      (datetime.datetime.now(), 'facebook', iid[0], sid[0], email))
        g.conn.close()
        gc.collect()
    return redirect(url[0])
    return render_template("index.html")

@app.route('/twitter_share/<title>', methods=['GET', 'POST'])
def twitter_share(title):
    url = []
    cursor = g.conn.execute("SELECT content FROM item WHERE title = %s;", title)
    for result in cursor:
        url.append('https://twitter.com/home?status=Discovered%20via%20Newsie%3A%20' + quote(result[0]))
    if 'email' in session:
        email = session['email']
        iid = []
        cursor = g.conn.execute("SELECT iid FROM item WHERE title = %s;", title)
        for result in cursor:
            iid.append(result[0])
        sid = []
        cursor = g.conn.execute("SELECT sid FROM cover WHERE iid = %s;", iid[0])
        for result in cursor:
            sid.append(result[0])
        g.conn = engine.connect()
        print datetime.datetime.now()
        g.conn.execute("INSERT INTO user_share (share_time, platform, iid, sid, email) VALUES (%s, %s, %s, %s, %s);",
                                      (datetime.datetime.now(), 'twitter', iid[0], sid[0], email))
        g.conn.close()
        gc.collect()
    return redirect(url[0])
    return render_template("index.html")


@app.route('/gplus_share/<title>', methods=['GET', 'POST'])
def gplus_share(title):
    url = []
    cursor = g.conn.execute("SELECT content FROM item WHERE title = %s;", title)
    for result in cursor:
        url.append('https://plus.google.com/share?url=' + quote(result[0]))
    if 'email' in session:
        email = session['email']
        iid = []
        cursor = g.conn.execute("SELECT iid FROM item WHERE title = %s;", title)
        for result in cursor:
            iid.append(result[0])
        sid = []
        cursor = g.conn.execute("SELECT sid FROM cover WHERE iid = %s;", iid[0])
        for result in cursor:
            sid.append(result[0])
        g.conn = engine.connect()
        print datetime.datetime.now()
        g.conn.execute("INSERT INTO user_share (share_time, platform, iid, sid, email) VALUES (%s, %s, %s, %s, %s);",
                                      (datetime.datetime.now(), 'google_plus', iid[0], sid[0], email))
        g.conn.close()
        gc.collect()
    return redirect(url[0])
    return render_template("index.html")



@app.route('/fave/<title>', methods=['GET', 'POST'])
def fave(title):
    if 'email' in session:
        email = session['email']
        iid = []
        cursor = g.conn.execute("SELECT iid FROM item WHERE title = %s;", title)
        for result in cursor:
            iid.append(result[0])
        sid = []
        cursor = g.conn.execute("SELECT sid FROM cover WHERE iid = %s;", iid[0])
        for result in cursor:
            sid.append(result[0])
        check = []
        cursor = g.conn.execute("SELECT * FROM user_fave WHERE iid = %s AND sid = %s AND email = %s",
                             iid[0], sid[0], email)
        for result in cursor:
            check.append(result[0])
        if len(check)!=0 and check[0]==iid[0]:
            return render_template("have_faved.html")
        else:
            g.conn = engine.connect()
            g.conn.execute("INSERT INTO user_fave (iid, sid, email) VALUES (%s, %s, %s);",
                           (iid[0], sid[0], email))
            g.conn.close()
            gc.collect()
            return render_template("have_faved.html")
    else:
        return redirect('/user_login')

    return render_template("index.html")

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


@app.route('/', methods=['POST'])
def filter_result():
    if request.method == "POST":
        """ SUBJECT FILTERING"""
        subject_query = "SELECT title, abstract, content FROM subject s, item i, cover c WHERE c.iid = i.iid AND c.sid = s.sid GROUP BY title, abstract, content"
        if request.form.getlist('Subject'):
            print request.form.getlist('Subject')
            subject_query = "SELECT title, abstract, content FROM subject s, item i, cover c WHERE c.iid = i.iid AND c.sid = s.sid AND subject_name in %(Subject)s"

        """PUBLISHER FILTERING"""
        publisher_query = "SELECT title, abstract, content FROM item i, publisher p, publisher_publish_item ppi WHERE ppi.iid = i.iid AND ppi.pid = p.pid GROUP BY title, abstract, content"
        if request.form.getlist('Publisher'):
            print request.form.getlist('Publisher')
            publisher_query = "SELECT title, abstract, content FROM item i, publisher p, publisher_publish_item ppi WHERE ppi.iid = i.iid AND ppi.pid = p.pid AND publisher_name in %(Publisher)s GROUP BY title, abstract, content"

        """AUTHOR FILTERING"""
        author_query = "SELECT title, abstract, content FROM item i, author a, author_write_item awi WHERE awi.iid = i.iid AND awi.aid = a.aid GROUP BY title, abstract, content"
        if request.form.getlist('Author'):
            print request.form.getlist('Author')
            publisher_query = "SELECT title, abstract, content FROM item i, author a, author_write_item awi WHERE awi.iid = i.iid AND awi.aid = a.aid  AND author_name in %(Author)s GROUP BY title, abstract, content"

        """POLITICAL STANCE FILTERING"""
        political_query = "SELECT title, abstract, content FROM item i, publisher p, publisher_publish_item ppi WHERE ppi.iid = i.iid AND ppi.pid = p.pid GROUP BY title, abstract, content"
        if request.form['Political_Stance']:
            print request.form['Political_Stance']
            political_query = "SELECT title, abstract, content FROM item i, publisher p, publisher_publish_item ppi WHERE ppi.iid = i.iid AND ppi.pid = p.pid AND political_stance = %(Political_Stance)s GROUP BY title, abstract, content"

        query = subject_query + " INTERSECT " + publisher_query + " INTERSECT " + author_query + " INTERSECT " + political_query + ";"
        params = dict(Subject=tuple(request.form.getlist('Subject')), Publisher=tuple(request.form.getlist('Publisher')), Author=tuple(request.form.getlist('Author')), Political_Stance=request.form['Political_Stance'])
        cursor = g.conn.execute(query, params)

        data = []
        for result in cursor:
            data.append(result)

    return render_template("results.html", data=data)

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
        user = []
        user.append(true)
        contents = []
        contents.append(session['email'])
        cursor = g.conn.execute("SELECT password FROM users WHERE email = %s;", session['email'])
        for result in cursor:
            contents.append(result[0])
        cursor = g.conn.execute("SELECT user_name FROM users WHERE email = %s;", session['email'])
        for result in cursor:
            contents.append(result[0])
            user.append(result[0])

        list = []
        view = []
        cursor = g.conn.execute("SELECT DISTINCT iid FROM user_view WHERE email = %s;", session['email'])
        for result in cursor:
            list.append(result)
        for id in list:
            cursor = g.conn.execute("SELECT DISTINCT title FROM item WHERE iid = %s;", id)
            for result in cursor:
                view.append(result[0])

        list = []
        fave = []
        cursor = g.conn.execute("SELECT DISTINCT iid FROM user_fave WHERE email = %s;", session['email'])
        for result in cursor:
            list.append(result)
        for id in list:
            cursor = g.conn.execute("SELECT DISTINCT title FROM item WHERE iid = %s;", id)
            for result in cursor:
                fave.append(result[0])

        list = []
        share = []
        cursor = g.conn.execute("SELECT DISTINCT iid FROM user_share WHERE email = %s;", session['email'])
        for result in cursor:
            list.append(result)
        for id in list:
            cursor = g.conn.execute("SELECT DISTINCT title FROM item WHERE iid = %s;", id)
            for result in cursor:
                share.append(result[0])

        top_subjects = []
        cursor = g.conn.execute("SELECT subject_name from user_view uv, subject s WHERE uv.sid = s.sid AND email = %s GROUP BY subject_name ORDER BY count(subject_name) DESC LIMIT 5;", session['email'])

        for result in cursor:
          top_subjects.append(result[0])

        cursor.close()
        context = dict(user=user, data=contents, fave=fave, view=view, share=share, top_subjects=top_subjects)
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
