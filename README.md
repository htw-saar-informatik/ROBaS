# ROBaS 
## Introduction
ROBaS is a cloud robotic platform based on Cloudroid und ROS.
With ROBaS you can Start and Manage all ROS Nodes that where made with catkin.



## Build ROBaS
ROBaS is built and tested on Ubuntu 14.04.


1. Install python components and other dependencies:

```bash
    sudo apt-get update
    sudo apt-get install python-dev python-pip python-tk git zip unzip
    sudo pip install pip --upgrade
```
ROBaS also requires catkin.Installation guide can be found here: wiki.ros.org/catkin#Installing_catkin

2. In the root directory of ROBaS project, install other python requirements:

```bash
    git clone https://github.com/htw-saar-informatik/ROBaS.git
    cd ROBaS/
    git submodule update --recursive
    sudo pip install -r requirements.txt
```

3. Create ROS Workspace

```bash
    mkdir -p workspace/src
    cd workspace/
    catkin_make
    source devel/setup.bash
```


4. Run ROBaS server:

```bash
    cd ..
    python run.py
```
