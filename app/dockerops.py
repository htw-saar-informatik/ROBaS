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

import zipfile, os, shutil, json, time, logging

import docker
from app import db, models 
from app.models import *
from app.commonset import *
from datetime import datetime
from flask_login import current_user
from flask.templating import render_template
from flask.globals import session
from Tkinter import image_names
import subprocess, roslaunch


current_milli_time = lambda: int(round(time.time() * 1000))



class StreamLineBuildGenerator(object):
    def __init__(self, json_data):
        self.__dict__ = json.loads(json_data)

def downloadFileBuild(downloadFileName):


 return None
            
def build_Package_With_Catkin(package_Name):
     devel_path='./workspace/devel/share/'+package_Name
     if os.path.exists(devel_path):
        shutil.rmtree(devel_path)
    
     subprocess.call(['./app/catkin_make.sh'],env=os.environ.copy())
        





def serviceinfo():
    logging.info('The query of services info list')
    
    try:  
        services = models.Service.query.all()
        result = []
        part_line = {'serviceid':'default','imagename':'default','filename':'default','user':'default','createtime':'default','namepace':'default','pid':'default'}
        for i in services:
            part_line['serviceid'] = i.serviceid
            part_line['imagename'] = i.imagename
            part_line['filename'] = i.uploadname
            part_line['user'] = i.username
            part_line['createtime'] = i.createdtime
            part_line['namespace'] = i.namespace
            part_line['pid'] = i.pid
            result.append(part_line)
            part_line = {}
        
        return result
            
    except Exception, e:
        logging.error('Unable to list the services info. \nReason: %s', str(e))
        return
    


def removeServices(serviceid, pid):
    import  os, signal
    
    remove_ser = models.Service.query.all()
    for i in remove_ser:
         if (i.serviceid == serviceid and i.pid == pid):
             try:
                 os.killpg(int(pid), signal.SIGINT)
             except:
               logging.info('Remove')
             db.session.delete(i)
             db.session.commit()
             
   
def deleteLogs(launchName):
   logging.info(launchName)
   path ='./logs/'+launchName +".txt"
   path_error = './logs/'+launchName+"_error.txt"
   try:
        os.remove(path)
        os.remove(path_error)
   except:
     logging.info("error")
     

def deleteImageFromDb(image_name):
  image = models.Image.query.filter_by(imagename=image_name).first()
  arguments = models.Arguments.query.filter_by(image_id = image.uid).all()  
  for arg in arguments:
     db.session.delete(arg)
  db.session.delete(image)
  db.session.commit()


def deleteImage(image_name):
    logging.info('Delete the image %s', image_name)
    
    image = models.Image.query.filter_by(imagename=image_name).first()
    arguments = models.Arguments.query.filter_by(image_id = image.uid).all()
    if(image.typ == "ZipFile"):
     fileName = './upload/'+image_name+'.zip'
     os.remove(fileName)
     src_path='./workspace/src/'+image.uploadname[:len(image.uploadname)-4]
    else:
     src_path='./workspace/src/'+image.uploadname   

    devel_path='./workspace/devel/share/'+image.package_name
    if os.path.exists(src_path):
     shutil.rmtree(src_path)

    if os.path.exists(devel_path):
     shutil.rmtree(devel_path)
           
   
    
    for arg in arguments:
     db.session.delete(arg)
    db.session.delete(image)
    db.session.commit()
    return None


def ListToString(lista):
    if lista.__len__() == 0:
        stringa = "None"
        return stringa
    else:
        stringa = ""
        for i in range(0,lista.__len__()):
            if (lista[i].split("#")).__len__() <= 1:
                lista[i] = str(lista[i]+"#")
        stringa = stringa.join(lista)
        return stringa


def StringToList(stringa):
    if stringa == "None":
        lista = []
        return lista
    else:
        lista = stringa.split('#')
        lista.pop()
        return lista
    

