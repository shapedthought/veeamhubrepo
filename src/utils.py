import subprocess
import shutil
import re
import psutil
import pystemd
import netifaces
import ipaddress
import json
import os

class UtilsClasss:

    def openfile(config,d,path):
        if "writer" in config and shutil.which(config["writer"][0]) is not None:
            procrun = config["writer"] + [path]
            subprocess.call(procrun)
        else:
            d.editbox(path,width=80,height=30)

    def firstgw(networkinterface):
        gw = "169.254.128.1"

        gws = netifaces.gateways()
        if netifaces.AF_INET in gws:
            fgw = [g for g in gws[netifaces.AF_INET] if g[1] == networkinterface ]
            if len(fgw) > 0:
                gw = fgw[0][0]
        
        return gw
        

    def firstipwithnet(networkinterface):
        ipwithnet = "169.254.128.128/24"

        if netifaces.AF_INET in netifaces.ifaddresses(networkinterface):
            addrs = netifaces.ifaddresses(networkinterface)[netifaces.AF_INET]
            if len(addrs) > 0:
                nm = ipaddress.IPv4Network("0.0.0.0/"+addrs[0]['netmask'])
                ipwithnet = addrs[0]['addr'] + "/" + str(nm.prefixlen)

        return ipwithnet

    def gettimeinfo():
        timeinfo = ["Could not fetch timeinfo"]
        time = ""
        date = ""
        zone = ""
        ntpactive = False
        pout = subprocess.run(["timedatectl","status"], capture_output=True) 
        if pout.returncode == 0:
            timeinfo = []
            for line in str(pout.stdout,'utf-8').split("\n"):
                line = line.strip()
                if line != "":
                    tim = re.match("Local time: [A-Za-z]+ ([0-9]{4}-[0-9]{2}-[0-9]{2}) ([0-9]{2}:[0-9]{2}:[0-9]{2})",line)
                    if tim:
                        time = tim.group(2)
                        date = tim.group(1)
                    else:
                        zm = re.match("Time zone: ([A-Za-z/]+)",line)
                        if zm:
                            zone = zm.group(1)
                        else:
                            ntpm = re.match("NTP service: ([A-Za-z/]+)",line)
                            if ntpm:
                                ntpactive = ntpm.group(1) == "active"
                                
                    timeinfo.append(line)

        return timeinfo,time,date,zone,ntpactive

    def installpackage(d,packagename):
        error = False


        d.infobox("Checking repo's for definitions")
        pout = subprocess.run(["apt-get","update","-y"], capture_output=True) 
        if pout.returncode != 0:
            d.msgbox("Error updating {0}".format(str(pout.stderr,'utf-8')))
            error = True
    
        if not error:
            d.infobox("Installing {}".format(packagename))
            pout = subprocess.run(["apt-get","install",packagename,"-y"], capture_output=True) 
            if pout.returncode != 0:
                d.msgbox("Error updating {0}".format(str(pout.stderr,'utf-8')))
                error = True
        
        return error

    def packagetest(dpkgtest):
        code = 0
        pout = subprocess.run(["dpkg","-s",dpkgtest], capture_output=True)
        if pout.returncode != 0:
            code = -1
        else:
            for ln in str(pout.stdout,"utf-8").split("\n"):
                if re.match("Status: install ok installed",ln):
                    code = 1
        return code

    def ufw_activate():
        ufw = subprocess.run(["ufw","--force","enable"], capture_output=True)
        if ufw.returncode != 0:
            raise Exception("ufw feedback not as expected {}".format(ufw.stdout))
        else:
            return ufw.stdout

    def veeamreposshcheck(username):
        procs = [p for p in psutil.process_iter(['pid', 'name', 'username']) if username in p.username() and "ssh" in p.name()]
        return len(procs) > 0

    def veeamrunning():
        procs = [p for p in psutil.process_iter(['pid', 'name', 'username']) if "veeamtransport" in p.name()]
        return len(procs) > 0

    def getsshservice():
        ssh = pystemd.systemd1.Unit(b'ssh.service')
        ssh.load()
        return ssh

    def ufw_is_inactive():
        ufw = subprocess.run(["ufw", "status"], capture_output=True)
        if ufw.returncode == 0:
            return "inactive" in str(ufw.stdout,"utf-8")
        else:
            raise Exception("ufw feedback not as expected {}".format(ufw.stdout))

    def ufw_ssh(setstatus="deny"):
        ufw = subprocess.run(["ufw",setstatus,"ssh"], capture_output=True)
        if ufw.returncode != 0:
            raise Exception("ufw feedback not as expected {}".format(ufw.stdout))
        else:
            return ufw.stdout

    def readfile(config,d,path):
        if "reader" in config and shutil.which(config["reader"][0]) is not None:
            procrun = config["reader"] + [path]
            subprocess.call(procrun)
        else:
            d.textbox(path,width=80,height=30)

    def realnics():
        return [i for i in netifaces.interfaces() if not i == 'lo' ]

    def myips(self):
        ipaddr = []
        for nif in self.realnics():
            ifaddr = netifaces.ifaddresses(nif)
            if netifaces.AF_INET in ifaddr:
                addrdetails = ifaddr[netifaces.AF_INET]
                for addr in addrdetails:
                    ip = addr['addr']
                    if ip != '127.0.0.1':
                        ipaddr.append(ip)
        return ipaddr

    def saveconfig(cfile,config):
        with open(cfile, 'w') as outfile:
            json.dump(config, outfile)

    def screensize():
        srows,scolumns = os.popen('stty size','r').read().split()
        return int(srows),int(scolumns)