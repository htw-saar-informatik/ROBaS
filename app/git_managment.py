import git, fileHandler,os
from git import Repo
import fileinput

class GitManagment:
 repository = None

 def __init__(self,dir_name):
  self.repository = git.Repo(fileHandler.src_path+"/"+dir_name)
  
 def getGitStatus():
  self.repository.git.status()

 def git_checkout(self,newBranch):
  self.repository.git.checkout(newBranch) 

 def git_fetch(self):
   if(self.repository != None):
     branches = self.repository.refs 
     non_protected_branch_names =[] 
     for branch in branches:
       if(non_protected_branch_names.count(branch.name.replace("origin/","")) == 0):
         non_protected_branch_names.append(branch.name.replace("origin/",""))
     return non_protected_branch_names  
   return None  

 def get_active_branch(self):
   if(self.repository != None):
     return self.repository.active_branch

 def git_pull(self):
   if(self.repository != None):
     self.repository.remotes.origin.pull()   
    
    
def cloneRepository(repository_link,repository_target_dir):
  Repo.clone_from(repository_link, fileHandler.src_path+"/"+repository_target_dir)


