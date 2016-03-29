#!/usr/bin/env python2.7

import os
from datetime import datetime
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, session, g, url_for, abort, render_template, g, redirect, Response, flash
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
app.secret_key = 'SSDFIXKDSFJIasdllllllllfaisxs'
DATABASEURI = "postgresql://bgw2119:PGKWXN@w4111db.eastus.cloudapp.azure.com/bgw2119"
engine = create_engine(DATABASEURI, echo=True)
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
    import traceback; traceback.print_exc()
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
  print "in index"
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
  print "before cursor"
  cursor = g.conn.execute("SELECT webserviceurl FROM public.webservice AS ws ORDER BY ws.webserviceurl")
  print "after cursor"
  print cursor
  urls = []
  for result in cursor:
    print "for result: " + result['webserviceurl']
    urls.append(result['webserviceurl'])  # can also be accessed using result[0]
  cursor.close()

  #for url in urls:
#      print url

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
  context = dict(data = urls)
  return render_template("index.html", **context)


@app.route('/webservice/<webserviceurl>')
def webservice(webserviceurl):
    service_name = g.conn.execute("SELECT name FROM public.webservice AS ws WHERE ws.webserviceurl = %s ", [webserviceurl]).fetchone()[0]
    webservice_comments = []
    cursor = g.conn.execute("SELECT * FROM public.serviceusercomment AS suc, public.serviceuser AS su WHERE suc.webserviceurl = %s AND su.email = suc.email ORDER BY suc.suctime" , [webserviceurl])
    for result in cursor:
      temp = {'username': str(result['username']).strip(), 'text': str(result['suctextblob']).strip(), 'time': str(result['suctime'])}
      webservice_comments.append(temp)
    cursor.close()
    print webservice_comments
    context = dict(name = service_name, url = webserviceurl, comments = webservice_comments)
    return render_template("webservice.html", **context)


@app.route('/report/<webserviceurl>', methods=['GET', 'POST'])
def report(webserviceurl):
    print "report"
    context = dict(url = webserviceurl)
    if request.method == 'POST':
        if not session.get('logged_in'):
            abort(401)
        now = str(datetime.utcnow())[0:19]
        print session['email']
        g.conn.execute("INSERT into public.report (reporttype, webserviceurl, reporttextblob, email, reporttime) values (%s, %s, %s, %s, %s)", [str(request.form['type']), str(request.form['url']), str(request.form['comment']), str(session['email']), now])
        flash('New entry was successfully posted')
        return redirect('/report/'+webserviceurl)
    return render_template("report.html", **context)

@app.route('/comment/<webserviceurl>', methods=['GET', 'POST'])
def comment(webserviceurl):
    print "webserviceurl"
    context = dict(url = webserviceurl)
    if request.method == 'POST':
        if not session.get('logged_in'):
            abort(401)
        now = str(datetime.utcnow())[0:19]
        print session['email']
        g.conn.execute("INSERT into public.serviceusercomment (webserviceurl, suctextblob, email, suctime) values (%s, %s, %s, %s)", [str(request.form['url']), str(request.form['comment_blob']), str(session['email']), now])
        flash('New entry was successfully posted')
        return redirect('/comment/'+webserviceurl)
    return render_template("comment.html", **context)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        passwordHolder = g.conn.execute("SELECT su.password FROM public.serviceuser AS su WHERE su.email = %s ", request.form['email']).fetchone()
        if (passwordHolder == None):
            error = 'Invalid email'
        elif str(request.form['password']) != str(passwordHolder[0].strip()):
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            session['email'] = str(request.form['email'])
            flash('You were logged in')
            return redirect('/')
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('Logged out succesfully')
    return redirect(url_for('index'))


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


  #app.run()
  run()#debug=True)
