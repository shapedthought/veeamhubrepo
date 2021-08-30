#! /usr/bin/env python3

# Veeamhub Repo
# VEEAMHUBREPOVERSION: 0.3.3

import json
import locale
import os
import subprocess
import sys
import time
from pathlib import Path

from dialogs import AlternateDialog, DialogWrapper
from menus import MenuClass

# main loop


def home(style="default"):
    menus = MenuClass
    locale.setlocale(locale.LC_ALL, '')

    # config file is made under /etc/veeamhubtinyrepoman
    # mainly keeps the repositories data and the repouser
    cfile = Path('/etc') / "veeamhubtinyrepoman"
    
    #d =  Dialog(dialog="dialog")
    #d.set_background_title("VeeamHub Tiny Repo Manager")

    rows,columns = menus.utils.screensize()

    if (rows < 40 or columns < 90) and style == "default":
        print("Switching to alternate dialog style because small terminal (r{},c{}), need at least 40 rows and 90 columns".format(rows,columns))
        print("To avoid this message, resize the terminal or run with -alt flag")
        print("In VMware the console screen might be to small, you can adapt it with vga=791 in grub")
        print("https://askubuntu.com/questions/86561/how-can-i-increase-the-console-resolution-of-my-ubuntu-server")
    
        style="alternate"
        time.sleep(5)
    
    d = 0
    if style == "alternate":
        d = AlternateDialog("Alternate VeeamHub Tiny Repo Manager",rows,columns)
    else:
        d = DialogWrapper("VeeamHub Tiny Repo Manager")

    code = d.OK
    config = {"repouser":"veeamrepo","vbrserver":"","reader":["nano","-v"],"writer":["nano"],"registertimeout":500}

    firstrun = False

    # json file. If it does not exists, it's create with the default settings above
    # if exists, it is read
    if not cfile.is_file():
        d.infobox("Trying to create:\n{}".format(str(cfile)),width=80)
        time.sleep(2)
        firstrun = True
        config['repositories'] = []
        with open(cfile, 'w') as outfile:
                json.dump(config, outfile)
    else:
        with open(cfile, 'r') as outfile:
                config = json.load(outfile)
    

    if firstrun:
        c = d.yesno("This is the first time you started veeamhubrepo\n\nDo you want to run the wizard process?\n\nThis will execute certain actions automatically!",width=60,height=15)
        if c == d.OK:
            menus.setrepouser(config, d)
            menus.utils.saveconfig(cfile,config)

            rcode,mp = menus.formatdrive(config,d)
            if rcode == 0 and mp != "":
                config['repositories'].append(mp)
            menus.utils.saveconfig(cfile,config)

            c = d.yesno("Do you want to configure NTP and the timezone?")
            if c == d.OK:
                menus.configtimezone(config,d)
                menus.ntp(config,d)

            d.infobox("Disabling SSH at startup")
            time.sleep(1)
            menus.disablessh()

            d.infobox("Enabling the firewall")
            time.sleep(1)
            menus.enablefw()

            c = d.yesno("Do you want to try to update the server now?")
            if c == d.OK:
                menus.update(config,d)

            menus.registerserver(config,d)

    # while you keep getting ok, keep going
    while code == d.OK:
        updated = False


    
        ln = ["Current IPv4: {}".format(",".join(menus.utils.myips()))]
        if menus.utils.is_ssh_on():
            ln.append("! SSH is running !")

        ln.append("")
        ln.append("What do you want to do:")

        # keep structure as it, add new functionality under sub menu so that it doesn't get too big
        code, tag = d.menu("\n".join(ln),
                       choices=[("1", "Set/Create Unprivileged Repo User"),
                                ("2", "Format Drive XFS"),
                                ("3", "Register Hardened Repo"),
                                ("4", "Monitor Repositories"),
                                ("5", "Manages Repo Paths"),
                                ("6", "Manage Ubuntu"),
                                ],height=len(ln)+14,cancel="Exit")
        if code == d.OK:
            if tag == "1":
                menus.setrepouser(config,d)
                # setrepouser(config,d)
                updated = True
            elif tag == "2" or tag == "5":
                # if usersexists(config["repouser"]):
                if menus.usersexists(config["repouser"]):
                    if tag == "2":
                        rcode,mp = menus.formatdrive(config,d)
                        if rcode == 0 and mp != "":
                            config['repositories'].append(mp)
                            updated = True
                    elif tag == "5":
                        updated = menus.managerepo(config,d)
                else:
                    d.msgbox("Please create repo user first")
            elif tag == "3":
                menus.registerserver(config,d)
            elif tag == "4":
                menus.monitorrepos(config,d)
            elif tag == "6":
                menus.manageubuntu(config,d)
            if updated:
                with open(cfile, 'w') as outfile:
                    json.dump(config, outfile)

# cleans output after being done
def main():
    args = sys.argv[1:]
    if "-alt" in args:
        home(style="alternate")
    else:
        home(style="default")

    subprocess.run(["clear"])

if __name__ == "__main__":
    if os.getuid() != 0:
        print("You are running this command as a regular user")
        print("Please use sudo e.g. sudo veeamhubrepo")
        exit(1)
    main()
