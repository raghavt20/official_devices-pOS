#!/usr/bin/env python
#
# Python code which automatically sends a Message in a Telegram Group
# if any new update is found. Intended to be run on every push
#
# Copyright (C) 2021-2022 Ashwin DS <astroashwin@outlook.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation;
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

import datetime
import os
import json
import requests
import hashlib
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

SF_PASS = os.environ.get("SF_PASS")

android_version_text = "thirteen"

cred = credentials.Certificate("priv/pixelos-telegram-bot-firebase-adminsdk-crrnu-4e65db1b73.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://pixelos-telegram-bot-default-rtdb.firebaseio.com/"
})


try:
    new_tags = open("new_tags.txt", "r").readlines()
except Exception as e:
    new_tags = []

try:
    OTA = os.path.exists("no_ota.txt")
except Exception as e:
    OTA = False

if OTA:
    print("Pushing OTA")
else:
    print("Not Pushing OTA")

cur_dir = os.getcwd()

def Santize_list (mList):
    new_list = []
    for value in mList:
        if value != None:
            new_list.append(value)
    return new_list

def Release_viewQueue():
    ref = db.reference('/release/queue')
    refget = ref.get()
    if refget != None:
        mlist = Santize_list(refget)
        print (mlist)
        return mlist
    else: 
        print ("Queue None")
        return None

print(new_tags)
print (Release_viewQueue())
for tag in new_tags:
    os.chdir(cur_dir + "/releases")
    os.system("gh release download " + tag.replace("\n", "") + " && ls")
    print (cur_dir)
    BIG_ROM_FILE = os.path.exists(cur_dir + "/releases/ROM_TOO_BIG.txt")
    if BIG_ROM_FILE:
        print("Big Zip")
        BIG_FILE_INFO = open(cur_dir + "/releases/ROM_TOO_BIG.txt", "r").readlines()[0]
        print (BIG_FILE_INFO)
        ROM_HASH = BIG_FILE_INFO.split(" ")[0]
        ROM_NAME = BIG_FILE_INFO.split("/")[-1].replace("\n", "")
        print (ROM_HASH , ROM_NAME)
        # If Size>2GB
        print ("Combining bigger files to one ")
        os.system("cat PixelOS.part?? > " + ROM_NAME)

        try: 
            with open(ROM_NAME, 'rb') as file_to_check:
                data = file_to_check.read()    
                hash_returned = hashlib.sha256(data).hexdigest()

            if ROM_HASH == hash_returned:
                print ("sha256 verified.")
            else:
                print ("sha256 verification failed!.")
        except Exception as e:
            print (e)
    
    CONTAINS_UPDATEPACKAGE = os.path.exists(cur_dir + "/releases/big_updatepackage.txt")
    
    if CONTAINS_UPDATEPACKAGE:
        print("UpdatePackage found")
        UPDATEPACKAGE_INFO = open(cur_dir + "/releases/big_updatepackage.txt", "r").readlines()[0]
        print (UPDATEPACKAGE_INFO)
        UPDATEPACKAGE_HASH = UPDATEPACKAGE_INFO.split(" ")[0]
        UPDATEPACKAGE_NAME = UPDATEPACKAGE_INFO.split("/")[-1].replace("\n", "")
        print (UPDATEPACKAGE_HASH , UPDATEPACKAGE_NAME)
        print ("Combining bigger files to one ")
        os.system("cat PixelOS-updatepackage.part?? > " + UPDATEPACKAGE_NAME)

        try: 
            with open(UPDATEPACKAGE_NAME, 'rb') as file_to_check:
                data = file_to_check.read()    
                hash_returned = hashlib.sha256(data).hexdigest()

            if UPDATEPACKAGE_HASH == hash_returned:
                print ("sha256 verified.")
            else:
                print ("sha256 verification failed!.")
        except Exception as e:
            print (e)

    mDevice = ""
    device = ""
    for file in os.listdir(cur_dir + "/releases/"):
        if file.endswith(".json"):
            device = file.replace(".json", "")
            mDevice = device + "-"
    VendorBootExists = False
    os.system ("mkdir " + cur_dir + "/images_to_upload")
    for file in os.listdir(cur_dir + "/releases"):
        if file.endswith (".img"):
            os.system("mv " + cur_dir + "/releases/" + file + " " + cur_dir + "/images_to_upload/" + file.replace(".img", "") + "-" +
                      tag.split("_")[0] + "-" + str(datetime.date.today()).replace("-", "") + ".img")
    
    print("Downloaded")
    os.chdir(cur_dir + "/releases-public")
    os.system("gh release create " + str(datetime.date.today()))
    if not BIG_ROM_FILE:
        os.system("gh release upload " + str(datetime.date.today()) +
                  " " + cur_dir + "/releases/PixelOS_*.zip")
    os.system("gh release upload " + str(datetime.date.today()) +
              " " + cur_dir + "/images_to_upload/*.img")

    ROM_ZIP_NAME = "none"

    for file in os.listdir(cur_dir + "/releases/"):
        if file.endswith(".zip") and file.startswith("PixelOS_"):
            ROM_ZIP_NAME = file

    for file in os.listdir(cur_dir + "/releases/"):
        if file.endswith(".json"):
            device = file.replace(".json", "")
            if not BIG_ROM_FILE:
                github_download_link = "https://github.com/PixelOS-Releases/releases-public/releases/download/" + str(datetime.date.today()) + "/" + ROM_ZIP_NAME
            else: 
                # GH releases will not work over 2GB, so just use SF
                github_download_link = "https://sourceforge.net/projects/pixelos-releases/files/thirteen/" + device + "/" + ROM_ZIP_NAME
            mjson = open(cur_dir + "/releases/" + file, "r").read().replace("GITHUB_RELEASES_PLACEHOLDER", github_download_link)
            open(cur_dir + "/releases/" + file, "w+").write(mjson)

    if OTA:
        for file in os.listdir(cur_dir + "/releases/"):
            if file.endswith(".json"):
                device = file.replace(".json", "")
                mjson = open(cur_dir + "/releases/" + file, "r").read().replace("URL_PLACEHOLDER",
                                                                               "https://sourceforge.net/projects/pixelos-releases/files/thirteen/" + device + "/" + ROM_ZIP_NAME)
                open(cur_dir + "/releases/" + file, "w+").write(mjson)

    else:
        for file in os.listdir(cur_dir + "/releases/"):
            if file.endswith(".json"):
                device = file.replace(".json", "")
                updaterInfo = json.loads(requests.get("https://raw.githubusercontent.com/PixelOS-AOSP/official_devices/" + android_version_text  + "/API/updater/" + device + ".json").content)
                updaterInfo ["github_releases_url"] = "https://github.com/PixelOS-Releases/releases-public/releases/download/" + str(datetime.date.today()) + "/" + ROM_ZIP_NAME
                open(cur_dir + "/releases/" + file, "w+").write(json.dumps(updaterInfo, indent=4), )



    os.system("cp " + cur_dir + "/releases/*.json " + cur_dir + "/API/updater/")


    push_commands = [
        "git config --global user.name \"PixelOS-Bot\"",
        "git config --global user.email \"pixelos.pixelish@gmail.com\"",
        "git fetch",
        "git pull",
        "git add .",
        "git commit -m \"official_devices: update tags [no ci]\"",
        "git push origin thirteen",
    ]

    for command in push_commands:
        os.system(command)

    os.system("sudo apt install sshpass")
    # os.system("mkdir ~/.ssh/")
    # os.system("ssh-keyscan frs.sourceforge.net >> ~/.ssh/known_hosts")

    try:
        for file in os.listdir(cur_dir + "/images_to_upload"):
            if file.endswith(".img"):
                os.system("sshpass -p " + SF_PASS + " scp -o \"StrictHostKeyChecking no\" " + cur_dir +
                  "/images_to_upload/" + file + " pixelos@frs.sourceforge.net:/home/frs/project/pixelos-releases/thirteen/" + device + "/recovery")

        os.system("sshpass -p " + SF_PASS + " scp -o \"StrictHostKeyChecking no\" " + cur_dir +
                  "/releases/PixelOS_*.zip pixelos@frs.sourceforge.net:/home/frs/project/pixelos-releases/thirteen/" + device + "")
        if CONTAINS_UPDATEPACKAGE:
            os.system("sshpass -p " + SF_PASS + " scp -o \"StrictHostKeyChecking no\" " + cur_dir +
                  "/releases/aosp_*-img-*.zip pixelos@frs.sourceforge.net:/home/frs/project/pixelos-releases/thirteen/" + device + "")
    except:
        print("Something went wrong")
    finally:
        os.system("rm -rf " + cur_dir + "/releases/*.img " +
              cur_dir + "/releases/*.zip " + cur_dir + "/images_to_upload")
    print("Uploaded")

    # Remove tag from queue 
    current_queue = Release_viewQueue()
    mtag = tag.replace("\n", "")
    if current_queue != None:
        if mtag in current_queue:
            current_queue.remove(mtag)
            ref = db.reference('/release/queue')
            ref.set(current_queue)
    else:
        print ("No Release Queue")
