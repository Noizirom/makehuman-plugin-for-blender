#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

""" 
**Project Name:**      MakeHuman community assets

**Product Home Page:** http://www.makehumancommunity.org

**Code Home Page:**    https://github.com/makehumancommunity/community-plugins

**Authors:**           Joel Palmius

**Copyright(c):**      Joel Palmius 2016

**Licensing:**         MIT

Abstract
--------

This plugin manages community assets

"""

import gui3d
import mh
import gui
import log
import json
import urllib2
import os

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4.QtGui import *

from progress import Progress

from core import G

mhapi = gui3d.app.mhapi

class AssetDownloadTaskView(gui3d.TaskView):

    def __init__(self, category):        
        
        gui3d.TaskView.__init__(self, category, 'Download assets')

        self.notfound = mhapi.locations.getSystemDataPath("notfound.thumb")

        self.human = gui3d.app.selectedHuman

        self.selectBox = self.addLeftWidget(gui.GroupBox('Select asset'))

        self.selectBox.addWidget(gui.TextView("\nType"))
        self.typeList = self.selectBox.addWidget(gui.ListView())
        self.typeList.setSizePolicy(gui.SizePolicy.Ignored, gui.SizePolicy.Preferred)

        types = [
            "Target",
            "Clothes",
            "Hair",
            "Proxy",
            "Skin"
        ]

        self.typeList.setData(types)
        self.typeList.setCurrentRow(0)
        self.typeList.selectionModel().selectionChanged.connect(self.onTypeChange)

        self.selectBox.addWidget(gui.TextView("\nCategory"))
        self.categoryList = self.selectBox.addWidget(gui.ListView())
        self.categoryList.setSizePolicy(gui.SizePolicy.Ignored, gui.SizePolicy.Preferred)

        categories = [
            "All"
        ]

        self.categoryList.setData(categories)
        self.categoryList.setCurrentRow(0)

        self.selectBox.addWidget(gui.TextView("\nAsset"))
        self.assetList = self.selectBox.addWidget(gui.ListView())
        self.assetList.setSizePolicy(gui.SizePolicy.Ignored, gui.SizePolicy.Preferred)

        assets = [
        ]

        self.assetList.setData(assets)
        self.assetList.selectionModel().selectionChanged.connect(self.onAssetChange)

        self.selectBox.addWidget(gui.TextView(" "))
        self.showButton = self.selectBox.addWidget(gui.Button('Asset homepage'))

        @self.showButton.mhEvent
        def onClicked(event):
            self.showButtonClick()

        self.downloadButton = self.selectBox.addWidget(gui.Button('Download'))

        @self.downloadButton.mhEvent
        def onClicked(event):
            self.downloadButtonClick()

        self.refreshBox = self.addRightWidget(gui.GroupBox('Synchronize'))
        refreshString = "Synchronizing data with the server can take some time, so it is not done automatically. Synchronizing will also download thumbnails and screenshots, if available. Click here to start the synchronization."
        self.refreshLabel = self.refreshBox.addWidget(gui.TextView(refreshString))
        self.refreshLabel.setWordWrap(True)
        self.refreshButton = self.refreshBox.addWidget(gui.Button('Synchronize'))

        @self.refreshButton.mhEvent
        def onClicked(event):
            self.refreshButtonClick()

        self.mainPanel = QtGui.QWidget()
        layout = QtGui.QVBoxLayout()

        self.assetInfoBox = gui.GroupBox("Asset info")
        self.assetInfoText = self.assetInfoBox.addWidget(gui.TextView("No asset selected"))

        layout.addWidget(self.assetInfoBox)

        self.assetThumbBox = gui.GroupBox("Asset thumbnail (if any)")
        self.thumbnail = self.assetThumbBox.addWidget(gui.TextView())
        self.thumbnail.setPixmap(QtGui.QPixmap(os.path.abspath(self.notfound)))
        self.thumbnail.setGeometry(0,0,128,128)

        layout.addWidget(self.assetThumbBox)

        self.assetScreenieBox = gui.GroupBox("Asset screenshot (if any)")
        self.screenshot = self.assetScreenieBox.addWidget(gui.TextView(""))
        self.screenshot.setPixmap(QtGui.QPixmap(os.path.abspath(self.notfound)))

        layout.addWidget(self.assetScreenieBox)

        layout.addStretch(1)

        self.mainPanel.setLayout(layout)

        self.addTopWidget(self.mainPanel)

        self.setupAssetDir()

    def onTypeChange(self):
        assetType = str(self.typeList.currentItem().text)
        if assetType == "Clothes":
            cats = sorted(self.clothesAssets.keys())
            self.categoryList.setData(cats)
            self.assetList.setData([])
        else:
            self.categoryList.setData(["All"])
            self.categoryList.setCurrentRow(0)

            assets = []

            if assetType == "Target":
                assets = self.targetNames
            if assetType == "Hair":
                assets = self.hairNames
            if assetType == "Proxy":
                assets = self.proxyNames
            if assetType == "Skin":
                assets = self.skinNames

            self.assetList.setData(sorted(assets))

        self.screenshot.setPixmap(QtGui.QPixmap(os.path.abspath(self.notfound)))
        self.thumbnail.setPixmap(QtGui.QPixmap(os.path.abspath(self.notfound)))
        self.assetInfoText.setText("Nothing selected")

    def onCategoryChange(self):
        assetType = str(self.typeList.currentItem().text)
        if assetType == "Clothes":
            pass

    def onAssetChange(self):
        assetType = str(self.typeList.currentItem().text)

        log.debug("Asset change: " + assetType)

        if assetType == "Target":
            self.onSelectTarget()
        if assetType == "Skin":
            self.onSelectSkin()

    def showButtonClick(self):
        print "showButton"

    def downloadButtonClick(self):      
        print "downloadButton"    

    def refreshButtonClick(self):

        self.progress = Progress()
        self.progress(0.0,0.1)

        web = urllib2.urlopen("http://www.makehumancommunity.org/sites/default/files/assets.json");
        jsonstring = web.read()
        assetJson = json.loads(jsonstring)

        increment = 0.8 / len(assetJson.keys())
        current = 0.1

        log.debug("Finished downloading json file")

        for key in assetJson.keys():
            current = current + increment
            self.progress(current,current + increment)
            self.setupOneAsset(assetJson[key])

        with open(os.path.join(self.root,"assets.json"),"w") as f:
            f.write(jsonstring)

        self.loadAssetsFromJson(assetJson)

        self.progress(1.0)

    def downloadUrl(self,url,saveAs):
        try:            
            web = urllib2.urlopen(url)
            data = web.read()
            with open(saveAs,"w") as f:
                f.write(data)                
        except:
            return False

        return True

    def loadAssetsFromJson(self, assetJson):

        self.clothesAssets = dict()
        self.clothesAssets["All"] = [];

        self.hairAssets = []
        self.skinAssets = []
        self.targetAssets = []
        self.proxyAssets = []

        self.clothesNames = dict()
        self.clothesNames["All"] = [];

        self.hairNames = []
        self.skinNames = []
        self.targetNames = []
        self.proxyNames = []

        for key in assetJson.keys():
            asset = assetJson[key]
            aType = asset["type"]
            aCat = "All"

            found = False

            if aType == "clothes":
                aCat = asset["category"]

                if aCat == "Hair":
                    self.hairAssets.append(asset)
                    self.hairNames.append(asset["title"])
                    found = True
                else:
                    self.clothesAssets["All"].append(asset)
                    if not aCat in self.clothesAssets.keys():
                        self.clothesAssets[aCat] = []
                    if not aCat in self.clothesNames.keys():
                        self.clothesNames[aCat] = []
                    self.clothesAssets[aCat].append(asset)
                    self.clothesNames[aCat].append(asset["title"])
                    found = True

            if aType == "target":
                self.targetAssets.append(asset)
                self.targetNames.append(asset["title"])
                found = True

            if aType == "skin":
                self.skinAssets.append(asset)
                self.skinNames.append(asset["title"])
                found = True

            if aType == "proxy":
                self.proxyAssets.append(asset)
                self.proxyNames.append(asset["title"])
                found = True

            if not found:
                log.debug("Unmatched asset type. " + str(asset["nid"]) + " (" + asset["type"] + "): " + asset["title"])

        self.assetList.setData(sorted(self.targetNames))

    def setupOneAsset(self, jsonHash):

        assetDir = os.path.join(self.root,str(jsonHash["nid"]))
        if not os.path.exists(assetDir):
            os.makedirs(assetDir)
        if "files" in jsonHash.keys():
            files = jsonHash["files"]
            if "render" in files.keys():
                fn = os.path.join(assetDir,"screenshot.png")
                if not os.path.exists(fn):                    
                    log.debug("Downloading " + files["render"])
                    self.downloadUrl(files["render"],fn)
                else:
                    log.debug("Screenshot already existed")

            if "thumb" in files.keys():
                fn = os.path.join(assetDir,"thumb.png")
                if not os.path.exists(fn):                    
                    log.debug("Downloading " + files["thumb"])
                    self.downloadUrl(files["thumb"],fn)
                else:
                    log.debug("thumb already existed")

    def setupAssetDir(self):

        self.root = mhapi.locations.getUserDataPath("community-assets")

        if not os.path.exists(self.root):
            os.makedirs(self.root)

        assets = os.path.join(self.root,"assets.json")    

        if os.path.exists(assets):
            with open(assets,"r") as f:
                jsonstring = f.read()
                assetJson = json.loads(jsonstring)
                self.loadAssetsFromJson(assetJson)

    def setThumbScreenshot(self,assetDir):
        screenshot = os.path.join(assetDir,"screenshot.png")
        thumbnail = os.path.join(assetDir,"thumb.png")
 
        if os.path.exists(screenshot):
            self.screenshot.setPixmap(QtGui.QPixmap(os.path.abspath(screenshot)))
        else:
            self.screenshot.setPixmap(QtGui.QPixmap(os.path.abspath(self.notfound)))
 
        if os.path.exists(thumbnail):
            self.thumbnail.setPixmap(QtGui.QPixmap(os.path.abspath(thumbnail)))
        else:
            self.thumbnail.setPixmap(QtGui.QPixmap(os.path.abspath(self.notfound)))
 
        self.thumbnail.setGeometry(0,0,128,128)

    def onSelectTarget(self):
        foundAsset = None
        name = str(self.assetList.currentItem().text)
        for asset in self.targetAssets:
            if str(asset["title"]) == name:
                foundAsset = asset

        if foundAsset:
            desc = "<big>" + foundAsset["title"] + "</big><br />\n&nbsp;<br />\n"
            desc = desc + "<b><tt>Author...: </tt></b>" + foundAsset["username"] + "<br />\n"
            desc = desc + "&nbsp;<br />\n"
            desc = desc + foundAsset["description"]

            self.assetInfoText.setText(desc)

            assetDir = os.path.join(self.root,str(foundAsset["nid"]))
            self.setThumbScreenshot(assetDir)

    def onSelectSkin(self):
        foundAsset = None
        name = str(self.assetList.currentItem().text)
        for asset in self.skinAssets:
            if str(asset["title"]) == name:
                foundAsset = asset

        if foundAsset:
            desc = "<big>" + foundAsset["title"] + "</big><br />\n&nbsp;<br />\n"
            desc = desc + "<b><tt>Author...: </tt></b>" + foundAsset["username"] + "<br />\n"
            desc = desc + "&nbsp;<br />\n"
            desc = desc + foundAsset["description"]

            self.assetInfoText.setText(desc)

            assetDir = os.path.join(self.root,str(foundAsset["nid"]))
            self.setThumbScreenshot(assetDir)


