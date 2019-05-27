from __future__ import print_function # Only Python 2.x
# coding:utf-8
# Software License Agreement (BSD License)
#
# Copyright (c) 2016, micROS Team
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
# 
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# 
# * Neither the name of micROS-drt nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

#from flask import Flask, request, redirect, url_for
from flask import render_template, flash, redirect, session, url_for, request, g
from flask_login import login_user, logout_user, current_user, login_required
from flask import jsonify,send_from_directory,abort
from app import app, db, lm
from app.dockerops import *
from app.fileHandler import *
from app.commonset import *
from git_managment import GitManagment
import os, sys, subprocess, git_managment


reload(sys)
sys.setdefaultencoding('utf-8')



@lm.user_loader
def load_user(uid):
    return User.query.get(int(uid))



@app.before_request
def before_request():
    g.user = current_user




@app.route('/')
@app.route('/index')
@login_required
def index():
    posts = [{ 'body': 'Welcome to Cloudroid! Please set your server IP first.' }]
    return render_template('index.html',posts=posts)




@app.route('/signup', methods=['GET', 'POST'])
def signup():
    from forms import SignupForm
   
    form = SignupForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user is not None:
            form.email.errors.append("The Email address is already taken.")
            return render_template('signup.html', form=form)

        newuser = User(form.firstname.data,form.lastname.data,form.email.data,form.password.data)
        db.session.add(newuser)
        db.session.commit()

        session['email'] = newuser.email
        return redirect(url_for('login'))
   
    return render_template('signup.html', form=form)



@app.route('/login', methods=['GET', 'POST'])
def login():
    if g.user is not None and g.user.is_authenticated:
        return redirect(url_for('index'))

    from app.forms import LoginForm

    form = LoginForm()
    if form.validate_on_submit():
        session['remember_me'] = form.remember_me.data
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user and user.check_password(form.password.data):
            session['email'] = form.email.data
            login_user(user,remember=session['remember_me'])
            return redirect(url_for('index'))
        else:
            return render_template('login.html',form=form,failed_auth=True)
             
    return render_template('login.html',form=form)



@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))



@app.route('/master', methods=['GET'])
def master():
    status = check_Ros_Master_status()
    return render_template('manageRosMaster.html', status=status,succeed=None,address=getRosMasterIp())



def check_Ros_Master_status():
    import rospy
    status = True

    try:
        rospy.get_master().getPid()
    except:
        status = False    
    return status    




def getRosMasterIp():
 import rosgraph
 try:
     master = rosgraph.Master("")
     return master.master_uri
 except:
      return None




@app.route('/master/<string:status>', methods=['GET'])
def master_handler(status):
  import subprocess, os, sys
  
  if status == 'True':
      try:
           subprocess.Popen(['pkill roscore'],shell=True)
      except:
          print('Failure')
  else:
     roscore_master_process = subprocess.Popen(['gnome-terminal', '--disable-factory', '-e', 'roscore'],preexec_fn=os.setpgrp)

  time.sleep(2)
  status=check_Ros_Master_status()
  if status:
     return render_template('manageRosMaster.html',form=None, action_error_msg = None, succeed = True, status=status,address=getRosMasterIp())   
  else:
     return render_template('manageRosMaster.html',form=None, action_error_msg = None, succeed = False, status=status)




@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    from app.forms import UploadForm
    
    form = UploadForm()
    if form.validate_on_submit():
        action_msg = uploadFile(form.ros_file.data, form.manifest_file.data, form.comments.data)
        action_list = action_msg.split(";")
        if len(action_list) != 2:
            action_error_msg = action_list[0]
        else:
            action_error_msg = action_list[0]
            proxy_name = action_list[1]
        url_base = url()
        succeed = (action_error_msg == "None")
        if succeed == True:
            return render_template('download.html',download_url = "download/"+proxy_name)
        else:
            return render_template('upload.html',form=form, action_error_msg = action_error_msg, succeed = succeed)   
         
    return render_template('upload.html',form=form, action_error_msg = None, succeed = False)




@app.route('/uploadGit', methods=['GET', 'POST'])
@login_required
def uploadGit():
    from app.forms import UploadGitForm 
    form = UploadGitForm()

    if form.validate_on_submit():

        action_msg = git_managment.cloneRepository(form.git_repository.data,form.git_repository_dir.data)
        loadUploadedGitRepository(form.git_repository_dir.data,form.comments.data)
         
    return render_template('upload.html',form=form)



@app.route('/download/<string:proxy_name>', methods=['GET'])
def download(proxy_name):
    from app.forms import UploadForm
    
    form = UploadForm()
    proxy_name_zip = proxy_name + ".zip"
    
    path1 = '../upload'
    path2 = os.path.join(path1, proxy_name_zip)
    logging.info(path2)
    if os.path.exists(path2):
        return send_from_directory(path1,proxy_name_zip,as_attachment=True)
    action_error_msg = downloadFileBuild(proxy_name)
    if None == action_error_msg:
        return send_from_directory(path1,proxy_name_zip,as_attachment=True)
    else:
        return render_template('upload.html',form=form, action_error_msg = action_error_msg, succeed = False)




@app.route('/images', methods=['GET'])
def images():
    from app import db, models         
    images = models.Image.query.all()
    result = []
    part_line = {'imagename':'default','uploadname':'default','uploaduser':'default','comments':'default'}
    for i in images:
        part_line['imagename'] = i.imagename
        part_line['uploadname'] = i.uploadname
        part_line['uploaduser'] = i.uploaduser
        part_line['comments'] = i.comments
        result.append(part_line)
        part_line = {}
    return render_template('images.html',imagetables = result)
  


@app.route('/checkoutBranch/<string:image_name>',methods=['POST'])
def checkoutBranch(image_name):
  image = models.Image.query.filter_by(imagename = image_name).first()  
  gitSession = GitManagment(image.uploadname)
  gitSession.git_checkout(request.form['dropdown'])
  deleteImageFromDb(image.uploadname)
  loadUploadedGitRepository(image.uploadname,image.comments)
  return idetailed(image_name)  


@app.route('/idetailed/<string:image_name>', methods=['GET'])
def idetailed(image_name):
    from app import db, models 
    
    image = models.Image.query.filter_by(imagename = image_name).first()
    args = models.Arguments.query.filter_by(image_id = image.uid).all()
    gitSession = GitManagment(image.uploadname)
    branches = gitSession.git_fetch()
    active_branch = gitSession.get_active_branch().name
    return render_template('idetailed.html',args=args, imagename = image.imagename, uploadname = image.uploadname, 
    uploaduser = image.uploaduser, uploadtime = image.uploadtime, 
    subscribed_topics = (image.start_services).split(" "), comments = image.comments,package_name=image.package_name,typ=image.typ,
    branches=branches,active_branch=active_branch.strip())


@app.route('/pull/<string:image_name>', methods=['GET'])
def pull(image_name):
    from app import db, models 
    
    image = models.Image.query.filter_by(imagename = image_name).first()
    args = models.Arguments.query.filter_by(image_id = image.uid).all()
    gitSession = GitManagment(image.uploadname)
    branches = gitSession.git_fetch()
    active_branch = gitSession.get_active_branch().name

    gitSession.git_pull()


    return render_template('idetailed.html',args=args, imagename = image.imagename, uploadname = image.uploadname, 
    uploaduser = image.uploaduser, uploadtime = image.uploadtime, 
    subscribed_topics = (image.start_services).split(" "), comments = image.comments,package_name=image.package_name,typ=image.typ,
    branches=branches,active_branch=active_branch.strip())



@app.route('/delete/<string:image_name>', methods=['GET'])
def delete(image_name):
    
    error_msg = deleteImage(image_name)
    
    return render_template('delete.html', imagename = image_name, error_msg = error_msg)
    





@app.route('/start/<string:image_name>/<string:launch_file_name>', methods=['GET', 'POST'])
def start_with_topic_name(image_name, launch_file_name):
    import logging,cgi
    from app import db, models 
    import subprocess, os, sys, signal, rospy
    from subprocess import Popen, PIPE, STDOUT
    from multiprocessing import Pool
    from thread import start_new_thread
    
    image = models.Image.query.filter_by(imagename = image_name).first()
    args = models.Arguments.query.filter_by(image_id = image.uid).all()
    arguments =""
    for arg in args:
       if( arg.service == launch_file_name):
         arguments = arguments +" " +arg.arg +":="+ request.form[arg.arg+launch_file_name]
         

    arguments.strip()

    
   
    package_name = image.package_name
    
  

    now = datetime.now()
    time = now.strftime("%H:%M:%S")
    
    file1 = open("./logs/"+launch_file_name+time+".txt","w+",buffering=0)
    my_env = os.environ.copy()
    p = subprocess.Popen(["stdbuf","-oL","roslaunch",package_name,launch_file_name,arguments.strip()],preexec_fn=os.setpgrp,stdout=file1,stderr=file1, universal_newlines=True,env=my_env)
     
    
    
    service_record=Service(serviceid=launch_file_name, createdtime=time,imagename=image_name,uploadname=image.uploadname,
                           username=image.uploaduser,firstcreatetime =datetime.now(),namespace = arguments,pid = p.pid)

    db.session.add(service_record)
    db.session.commit()
   
   
    return render_template('idetailed.html',args=args,imagename = image.imagename, uploadname = image.uploadname, uploaduser = image.uploaduser, 
                            uploadtime = image.uploadtime, subscribed_topics = (image.start_services).split(" "), 
                            comments = image.comments,node_name = launch_file_name, succeed = True,error_Message = None)



@app.route('/services/<string:launch_file_name>', methods=['GET'])
def view_log(launch_file_name):
    log = open("./logs/"+launch_file_name+".txt","r")

    return render_template('test.html',text=log.read(),service_name=launch_file_name)

@app.route('/services', methods=['GET'])
def services():
    servicei = serviceinfo()
    return render_template('service.html', servicetables = servicei)


@app.route('/build/<string:image_name>', methods=['GET'])
def build_image(image_name):
    
    build_Package_With_Catkin(image_name)
    return ""


@app.route('/remove/<string:serviceid>/<string:pid>', methods=['GET'])
def remove(serviceid, pid):
    removeServices(serviceid,pid)
    servicei = serviceinfo()
    return render_template('service.html', servicetables = servicei)




@app.route('/node_info/', methods=['GET'])
def node_info():
    import rosnode
    try:
      rosnodes_aslist = rosnode.get_node_names()
    except:
         return render_template('node_info.html',rosnodes = ['No Nodes Running'],success = False)
    return render_template('node_info.html',rosnodes = rosnodes_aslist,success = True)
    


