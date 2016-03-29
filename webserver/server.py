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
  try:
    g.conn = engine.connect()
  except:
    print "uh oh, problem connecting to database"
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  try:
    g.conn.close()
  except Exception as e:
    pass

@app.route('/')
def index():
  cursor = g.conn.execute("SELECT webserviceurl FROM public.webservice AS ws ORDER BY ws.webserviceurl")
  urls = []
  for result in cursor:
    urls.append(result['webserviceurl'])  # can also be accessed using result[0]
  cursor.close()
  context = dict(data = urls)
  return render_template("index.html", **context)

@app.route('/sign_up',methods=['POST'])
def sign_up():





@app.route('/webservice/<webserviceurl>')
def webservice(webserviceurl):
    service_name = g.conn.execute("SELECT name FROM public.webservice AS ws WHERE ws.webserviceurl = %s ", [webserviceurl]).fetchone()[0]

    #comments
    webservice_comments = []
    cursor = g.conn.execute("SELECT * FROM public.serviceusercomment AS suc, public.serviceuser AS su WHERE suc.webserviceurl = %s AND su.email = suc.email ORDER BY suc.suctime" , [webserviceurl])
    for result in cursor:
      temp = {'username': str(result['username']).strip(), 'text': str(result['suctextblob']).strip(), 'time': str(result['suctime'])}
      webservice_comments.append(temp)
    cursor.close()

    #reports
    webservice_reports = []
    cursor = g.conn.execute("SELECT * FROM public.report AS rpt, public.serviceuser AS su WHERE rpt.webserviceurl = %s AND su.email = rpt.email ORDER BY rpt.reporttime" , [webserviceurl])
    for result in cursor:
      temp = {'username':str(result['username']).strip(), 'type':str(result['reporttype']).strip(), 'text': str(result['reporttextblob']).strip(), 'time': str(result['reporttime'])}
      webservice_reports.append(temp)
    cursor.close()

    #announcements
    webservice_announcements = []
    cursor = g.conn.execute("SELECT * FROM public.representativeannouncement AS ra, public.webservicerepresentative AS su WHERE ra.webserviceurl = %s AND su.email = ra.email ORDER BY ra.ratime" , [webserviceurl])
    for result in cursor:
      temp = {'text': str(result['ratextblob']).strip(), 'time': str(result['ratime'])}
      print "temp" + str(temp)
      webservice_announcements.append(temp)
    print "webservice_announcements" + str(webservice_announcements);
    cursor.close()
    context = dict(name = service_name, url = webserviceurl, comments = webservice_comments, reports = webservice_reports, announcements = webservice_announcements)

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
        if request.form['sign_up'] == 'TRUE'
            suCheck = g.conn.execute("SELECT * FROM public.serviceuser AS su WHERE su.email = %s ", request.form['email'])
            if (suCheck.rowcount > 0):
                error = 'Email in use.'
            elif (request.form['password1'] != request.form['password2']):
                error = 'Passwords must match.'
            g.conn.execute("INSERT into public.webservicerepresentative (email, username, password) values (%s, %s, %s)", request.form['email'], request.form['username'], request.form['password1']);
            session['logged_in'] = True
            session['email'] = str(request.form['email'])
            flash('You were signed up and logged in')
            return redirect('/')
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
    HOST, PORT = host, port
    print "running on %s:%d" % (HOST, PORT)
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  #app.run()
  run()#debug=True)
