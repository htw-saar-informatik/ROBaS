import subprocess, roslaunch,time,logging,os
import roslaunch.arg_dump 
import xml.etree.ElementTree as ET
import zipfile
from app.models import *
from datetime import datetime
from flask_login import current_user

upload_path='./upload'
src_path='./workspace/src'

current_milli_time = lambda: int(round(time.time() * 1000))


def uploadFile(ros_file, manifest_file, comments):
     
    '''The internal unique id of a uploaded file will be the mill time since 1970''' 
    image_name = str(current_milli_time()) 
    save_filename = image_name + '.zip'
    logging.info('Uploading %s to path %s', ros_file.filename, upload_path)
    saveZipFileToUploadDir(save_filename,ros_file)   
    
    logging.info('Unzipping uploaded file %s', ros_file.filename)
    
    '''Unzip the uploaded file''' 
    unzipFile(save_filename)
    

    package_name = ""
    start_services = ""
    launch_dir = src_path+"/"+ros_file.filename.split(".zip")[0]+"/launch/" 

    try:
      start_services = loadManifest_File(manifest_file)
    except:
     start_services = getLaunchFiles(launch_dir)

    arg_record = loadLaunchFiles(start_services,launch_dir)
              
    tree = ET.parse(src_path+"/"+ros_file.filename.split(".zip")[0]+"/package.xml")
    root = tree.getroot()
    for child in root:
       if child.tag == "name":
          package_name = child.text
          
  
     
    '''Insert a new record to the image table in the database'''  
    image_record = Image(imagename = image_name, uploadname = ros_file.filename, comments = comments, uploadtime = datetime.now(), uploaduser = current_user.email, 
                         start_services = start_services.strip(),args = "", package_name = package_name,category= arg_record,typ="ZipFile")
    db.session.add(image_record)
    db.session.commit()
    
    
    return "None;"+image_name


def loadUploadedGitRepository(dir_name,comments):
 package_name = ""
 start_services = ""
 launch_dir = src_path+"/"+dir_name+"/launch/" 

 try:
     start_services = loadManifest_File(manifest_file)
 except:
     start_services = getLaunchFiles(launch_dir)

 arg_record = loadLaunchFiles(start_services,launch_dir)
 tree = ET.parse(src_path+"/"+dir_name+"/package.xml")
 root = tree.getroot()

 for child in root:
    if child.tag == "name":
        package_name = child.text

 image_record = Image(imagename = package_name, uploadname = dir_name, comments = comments, uploadtime = datetime.now(), uploaduser = current_user.email, 
                         start_services = start_services.strip(),args = "", package_name = package_name,category= arg_record,typ="GitRepository")
 db.session.add(image_record)
 db.session.commit()       
 return "None"


def unzipFile(save_filename):
 '''Unzip the uploaded file''' 
 try:      
    zip_ref = zipfile.ZipFile(os.path.join(upload_path, save_filename), 'r')
    for name in zip_ref.namelist():
         is_dir = lambda name: name.filename.endswith('/')
         if is_dir and os.path.exists(src_path+'/'+name):
             raise Exception('Directory '+ name +' exists') 
             break

    zip_ref.extractall(src_path)
    zip_ref.close()
    p = subprocess.Popen(["chmod","-R","777",src_path])
        
 except Exception, e:
    error_string = 'Unzip file {} to path {} failure. \nReason: {}'.format(save_filename, src_path, str(e))
    logging.error(error_string)
    return error_string 


def saveZipFileToUploadDir(save_filename,ros_file):
   '''Save file to the upload directory. Replace filename with the internal unique id'''      
   try:
        if not os.path.exists(upload_path):
            os.mkdir(upload_path)
             
        ros_file.save(os.path.join(upload_path, save_filename))
   except Exception, e:
        error_string = 'Unable to save file {} to path {}. \nReason: {}'.format(save_filename, upload_path, str(e))
        logging.error(error_string)
        return error_string





def getLaunchFiles(launch_dir):
 start_services=""
 for file in os.listdir(launch_dir):
          start_services = file +" "+start_services
 start_services.strip()     
 return start_services



def loadLaunchFiles(start_services,launch_dir):
    arg_record =[]
    start_services_as_list = start_services.strip().split(" ")
    args_as_String = ""
    for file in os.listdir(launch_dir):
        for service in start_services_as_list:
          if file == service:
            roslaunch_file = launch_dir+file
            args = roslaunch.arg_dump.get_args([roslaunch_file])
            for x in args:
                arg_record.append(Arguments(arg = x,service=file))
               
                args_as_String = args_as_String + x +" "

    if args_as_String == "":
        args_as_String = None            
    return arg_record



def loadManifest_File(manifest_file):
    manifest = json.load(manifest_file)
    start_services  = manifest.get('start_services')
    return start_services 

