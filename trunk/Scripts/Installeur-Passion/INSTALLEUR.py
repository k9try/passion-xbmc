# -*- coding: cp1252 -*-
from string import *
import sys#, os.path
import re
from time import gmtime, strptime, strftime
import os
import ftplib
import ConfigParser
import xbmcgui, xbmc
import traceback
import time
import urllib2
import socket

try:
    del sys.modules['BeautifulSoup']
except:
    pass 
from BeautifulSoup import BeautifulStoneSoup #librairie de traitement XML
import htmlentitydefs


try: Emulating = xbmcgui.Emulating
except: Emulating = False


############################################################################
# Get actioncodes from keymap.xml
############################################################################

ACTION_MOVE_LEFT                 = 1
ACTION_MOVE_RIGHT                = 2
ACTION_MOVE_UP                   = 3
ACTION_MOVE_DOWN                 = 4
ACTION_PAGE_UP                   = 5
ACTION_PAGE_DOWN                 = 6
ACTION_SELECT_ITEM               = 7
ACTION_HIGHLIGHT_ITEM            = 8
ACTION_PARENT_DIR                = 9
ACTION_PREVIOUS_MENU             = 10
ACTION_SHOW_INFO                 = 11

ACTION_PAUSE                     = 12
ACTION_STOP                      = 13
ACTION_NEXT_ITEM                 = 14
ACTION_PREV_ITEM                 = 15

#############################################################################
# autoscaling values
#############################################################################

HDTV_1080i      = 0 #(1920x1080, 16:9, pixels are 1:1)
HDTV_720p       = 1 #(1280x720, 16:9, pixels are 1:1)
HDTV_480p_4x3   = 2 #(720x480, 4:3, pixels are 4320:4739)
HDTV_480p_16x9  = 3 #(720x480, 16:9, pixels are 5760:4739)
NTSC_4x3        = 4 #(720x480, 4:3, pixels are 4320:4739)
NTSC_16x9       = 5 #(720x480, 16:9, pixels are 5760:4739)
PAL_4x3         = 6 #(720x576, 4:3, pixels are 128:117)
PAL_16x9        = 7 #(720x576, 16:9, pixels are 512:351)
PAL60_4x3       = 8 #(720x480, 4:3, pixels are 4320:4739)
PAL60_16x9      = 9 #(720x480, 16:9, pixels are 5760:4739)

############################################################################
class cancelRequest(Exception):
    """
    Exception, merci a Alexsolex 
    """
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
    
class rssReader:
    """
    
    Class responsable de la recuperation du flux RSS et de l'extraction des infos RSS
    
    """
    def __init__(self,rssUrl):
        """
        Init de rssReader
        """
        self.rssURL = rssUrl
        self.rssPage = self.get_rss_page(self.rssURL)

    def get_rss_page(self,rssUrl):
        """
        T�l�charge et renvoi la page RSS
        """
        try:
            #request = urllib2.Request("http://passion-xbmc.org/service-importation/?action=.xml;type=rss2;limit=1")
            request = urllib2.Request(rssUrl)
            request.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; fr; rv:1.9) Gecko/2008052906 Firefox/3.0')
            request.add_header('Accept','text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')
            request.add_header('Accept-Language','fr,fr-fr;q=0.8,en-us;q=0.5,en;q=0.3')
            request.add_header('Accept-Charset','ISO-8859-1,utf-8;q=0.7,*;q=0.7')
#            request.add_header('Keep-Alive','300')
#            request.add_header('Connection','keep-alive')
            response = urllib2.urlopen(request)
            the_page = response.read()
        except Exception, e:
            print("Exception get_rss_page")
            print(e)
            the_page = ""
        # renvo a page the RSS
        return the_page

    def unescape(self,text):
        """
        credit : Fredrik Lundh
        trouve : http://effbot.org/zone/re-sub.htm#unescape-html"""
        def fixup(m):# m est un objet match
            text = m.group(0)#on r�cup�re le texte correspondant au match
            if text[:2] == "&#":# dans le cas o� le match ressemble � &#
                # character reference
                try:
                    if text[:3] == "&#x":#si plus pr�cis�ment le texte ressemble � &#38;#x (donc notation hexa)
                        return unichr(int(text[3:-1], 16))#alors on retourne le unicode du caract�re en base 16 ( hexa)
                    else:
                        return unichr(int(text[2:-1]))#sinon on retourne le unicode du caract�re en base 10 (donc notation d�cimale)
                except ValueError: #si le caract�re n'est pas unicode, on le passe simplement
                    pass
            else: #sinon c'est un caract�re nomm� (htmlentities)
                # named entity
                try:
                    text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])#on renvoi le unicode de la correspondance pour le caract�re nomm�
                except KeyError:
                    pass #si le caract�re nomm� n'est pas d�fini dans les htmlentities alors on passe
            return text # leave as is #dans tous les autres cas, le match n'�tait pas un caract�re d'�chapement html on le retourne tel quel
     
        #par un texte issu de la fonction fixup
        return re.sub("&#?\w+;", fixup,   text)    
    
    def GetRssInfo(self):
        """
        Recupere les information du FLux RSS de passion XBMC
        Merci a Alexsolex
        """
        soup = BeautifulStoneSoup(self.rssPage)
        maintitle = soup.find("description").string.encode("cp1252", 'xmlcharrefreplace').replace("&#224;","�").replace("&#234;","�").replace("&#232;","�").replace("&#233;","�").replace("&#160;","  ***  ") # Note: &#160;=&
        items = ""
        for item in soup.findAll("item"): #boucle si plusieurs items dans le rss
            # Titre de l'Item 
            itemsTitle = item.find("title").string.encode("cp1252", 'xmlcharrefreplace').replace("&#224;","�").replace("&#234;","�").replace("&#232;","�").replace("&#233;","�").replace("&#160;","  ***  ") # Note: &#160;=&
            items = items + itemsTitle + ":  "
            # la ligne suivante supprime toutes les balises au sein de l'info "description"
            clean_desc = re.sub(r"<.*?>", r"", "".join(item.find("description").contents))
            # on imprime le texte sans les caracteres d'echappements html
            # Description de l'item 
            itemDesc = self.unescape(clean_desc).strip().encode("cp1252", 'xmlcharrefreplace').replace("&#224;","�").replace("&#234;","�").replace("&#232;","�").replace("&#233;","�").replace("&#160;","  ***  ") # Note: &#160;=&
            itemDesc = itemDesc.replace("-Plus d'info","").replace("-Voir la suite...","") # on supprime "-Plus d'info" et "-Voir la suite..."
            #TODO: supprimer balise link plutot que remplacer les chaines -Voir la suite...
            # Concatenation
            items = items + " " + itemDesc
        return maintitle,items




class scriptextracter:
    """
    
    Extracteur de script, dezip ou derar une archive et l'efface

    """
    def zipfolder (self):
        import zipfile
        self.zfile = zipfile.ZipFile(self.archive, 'r')
        for i in self.zfile.namelist():  ## On parcourt l'ensemble des fichiers de l'archive
            print i
            if i.endswith('/'):
                dossier = self.pathdst + os.sep + i
                try:
                    os.makedirs(dossier)
                except Exception, e:
                    print "Erreur creation dossier de l'archive = ",e
            else:
                print "File Case"

        # On ferme l'archive
        self.zfile.close()

    def  extract(self,archive,TargetDir):
        self.pathdst = TargetDir
        self.archive = archive
        print "self.pathdst = %s"%self.pathdst
        print "self.archive = %s"%self.archive
        
        if archive.endswith('zip'):
            self.zipfolder() #generation des dossiers dans le cas d'un zip
        #extraction de l'archive
        xbmc.executebuiltin('XBMC.Extract(%s,%s)'%(self.archive,self.pathdst) )

class ftpDownloadCtrl:
    """

    Controleur de download via FTP
    Cette classe gere les download via FTP de fichiers et repertoire

    """
    def __init__(self,host,user,password,remotedirList,localdirList,typeList):
        """
        Fonction d'init de la classe ftpDownloadCtrl
        Initialise toutes les variables et lance la connection au serveur FTP
        """

        #Initialise les attributs de la classe ftpDownloadCtrl avec les parametres donnes au constructeur
        self.host                   = host
        self.user                   = user
        self.password               = password
        self.remotedirList          = remotedirList
        self.localdirList           = localdirList
        self.downloadTypeList       = typeList
#        self.remoteplugindirlist    = remoteplugindirlist
#        self.localplugindirlist     = localplugindirlist   
        
        self.connected          = False # status de la connection (inutile pour le moment)
        self.curLocalDirRoot    = ""
        self.curRemoteDirRoot   = ""
        #self.idcancel           = False
        print "self.host = ",self.host
        print "self.user= ",self.user
        #print "self.password = ",self.password

        #Connection au serveur FTP
        self.openConnection()

    def openConnection(self):
        """
        Ouvre la connexion FTP
        """
        #Connection au serveur FTP
        try:
            self.ftp = ftplib.FTP(self.host,self.user,self.password) # on se connecte
            #self.ftp.cwd(self.remotedirList)# va au chemin specifie
            
            # DEBUG: Seulement pour le dev
            #self.ftp.set_debuglevel(2)
            
            self.connected = True
            #self.ftp.sendcmd('PASV')

        except Exception, e:
            print "ftpDownloadCtrl: __init__: Exception durant la connection FTP",e
            print "ftpDownloadCtrl: Impossible de se connecter au serveur FTP: %s"%self.host
            print ("error/MainWindow __init__: " + str(sys.exc_info()[0]))
            traceback.print_exc()
            
    def closeConnection(self):
        """
        Ferme la connexion FTP
        """
        #on se deconnecte du serveur pour etre plus propre
        self.ftp.quit()

    def getDirList(self,remotedir):
        """
        Retourne la liste des elements d'un repertoire sur le serveur
        """
        curDirList = []
        
        # Recuperation de la liste
        try:
            #self.ftp.sendcmd('PASV')
            curDirList = self.ftp.nlst(remotedir)
        except Exception, e:
            print "getDirList: __init__: Exception durant la recuperation de la liste des fichiers du repertoire: %s"%remotedir,e
            print ("error/MainWindow __init__: " + str(sys.exc_info()[0]))
            traceback.print_exc()
        
        # Tri de la liste et renvoi
        curDirList.sort(key=str.lower)
        return curDirList


    def isDir(self,pathsrc):
        """
        Verifie si le chemin sur le serveur correspond a un repertoire
        """
        isDir = True
        # Verifie se on telecharge un repertoire ou d'un fichier
        try:
            self.ftp.cwd(pathsrc) # c'est cette commande qui genere l'exception dans le cas d'un fichier
            # Pas d'excpetion => il s'agit d'un dossier
            print "isDir: %s EST un DOSSIER"%pathsrc
        except Exception, e:
            print "isDir: %s EST PAS un FICHIER"%pathsrc
            isDir = False
        return isDir

    
    def isDirAlreadyDownloaded(self,pathsrc,rootdirsrc,typeIndex):
        """
        """
        isDownloaded     = False
        curLocalDirRoot  = self.localdirList[typeIndex]
        curRemoteDirRoot = rootdirsrc
        localAbsDirPath  = None
        
        # Verifie se on telecharge un repertoire ou d'un fichier
        if self.isDir(pathsrc):
            # Cree le chemin du repertorie local
            # Extrait le chemin relatif: soustrait au chemin remote le chemin de base: par exemple on veut retirer du chemin; /.passionxbmc/Themes
            remoteRelDirPath = pathsrc.replace(curRemoteDirRoot,'')
    
            # On remplace dans le chemin sur le serveur FTP les '/' par le separateur de l'OS sur lequel on est
            localRelDirPath = remoteRelDirPath.replace('/',os.sep)
    
            # Cree le chemin local (ou on va sauver)
            localAbsDirPath = os.path.join(curLocalDirRoot, localRelDirPath)
    
            isDownloaded = os.path.isdir(localAbsDirPath)
        else:
            print "isDirAlreadyDownloaded: ERREUR %s n'est pas un repertoire!!!"%pathsrc
        return isDownloaded,localAbsDirPath




    def download(self,pathsrc,rootdirsrc,typeIndex,progressbar_cb=None,dialogProgressWin=None):
        """
        Telecharge les elements a un chemin specifie (repertoires, sous repertoires et fichiers)
        a dans un repertorie local dependant du type de telechargement (theme, scraper, script ...)
        pathsrc     : chemin sur le serveur de l'element a telecharger
        rootdirsrc  : Repertoire root sur le server (correspondant a un type de download) - Exemple : "/.passionxbmc/Scraper/" pour les scrapers
        typeIndex   : Index correspondant au type de telechargement, permet notamment de definir le repertorie local de telechargement
        Renvoi le status du download:
            - (-1) pour telechargement annule
            - (1)  pour telechargement OK
        """
            
        self.curLocalDirRoot  = self.localdirList[typeIndex]
        self.curRemoteDirRoot = rootdirsrc

        try:
            if (progressbar_cb != None) and (dialogProgressWin != None):
                percent = 0
                #print "=================================="
                #print
                #print "Pourcentage telecharger: %d"%percent
                #print
                #print "=================================="
                # Initialisation de la barre de progression (via callback)
                progressbar_cb(percent,dialogProgressWin)
        except Exception, e:
            print("download - Exception ProgressBar UI callback for download")
            print(e)
            print progressbar_cb

        # Appel de la fonction privee en charge du download - on passe en parametre l'index correspondant au type
        status = self._download(pathsrc,progressbar_cb,dialogProgressWin,0,1)
        return  status # retour du status du download recupere


    def _download(self, pathsrc,progressbar_cb=None,dialogProgressWin=None,curPercent=0,coeff=1):
        """
        Fonction privee (ne pouvant etre appelee que par la classe ftpDownloadCtrl elle meme)
        Telecharge un element sur le server FTP
        Renvoi le status du download:
            - (0) pour telechargement annule
            - (1)  pour telechargement OK
        """

        # Liste le repertoire
        curDirList     = self.ftp.nlst(pathsrc) #TODO: ajouter try/except
        curDirListSize = len(curDirList) # Defini le nombre d'elements a telecharger correspondant a 100% - pour le moment on ne gere que ce niveau de granularite pour la progressbar
        # On teste le nombre d'element dans la liste : si 0 -> rep vide
        # !!PB!!: la commande NLST dans le cas ou le path est un fichier retourne les details sur le fichier => donc liste non vide
        # donc pour le moment on essaira de telecharger en tant que fichier un rep vide (apres avoir fait un _downloaddossier)
        # mais ca ira ds une exception donc OK mais pas propre
        #TODO: a ameliorer donc
        #print "_download: Repertoire NON vide - demarrage boucle"
        for i in curDirList:
            if dialogProgressWin.iscanceled():
                print "Telechargement annul� par l'utilisateur"
                # Sortie de la boucle via return
                return 0 # 0 pour telechargement annule
            else:
                # Calcule le pourcentage avant download
                #TODO: verifier que la formule pour le pourcentage est OK (la ca ette fait un peu trop rapidement) 
                #percent = min(curPercent + int((float(curDirList.index(i)+1)*100)/(curDirListSize * coeff)),100)
                percent = min(curPercent + int((float(curDirList.index(i)+0)*100)/(curDirListSize * coeff)),100)
                #print "=================================="
                #print
                print "Pourcentage t�l�charg�: %d"%percent
                #print
                #print "=================================="
                # Verifie si le chemin correspond a un repertoire
                
                try :

                    #Mise a jour de la barre de progression (via callback)
                    #TODO: Solution temporaraire -> on veut afficher le nom du theme/script/skin en cours en plus du fichier
                    dialogProgressWin.update(0,"T�l�chargement Total: %d%%"%percent, "%s"%i)
                except Exception, e:
                    print("downloadVideo - Exception calling UI callback for download")
                    print(e)
                    print progressbar_cb
                    
                if self.isDir(i):
                    # pathsrc est un repertoire
                    # Telechargement du dossier
                    print "Telechargement du dossier %s"%pathsrc               
                    self._downloaddossier(i,dialogProgressWin=dialogProgressWin,curPercent=percent,coeff=coeff*curDirListSize)
                    percent = int((float(curDirList.index(i)+1)*100)/(curDirListSize * coeff))
                    
                else:
                    # pathsrc est un fichier
                    print "Telechargement du fichier %s"%pathsrc               
                    # Telechargement du fichier
                    self._downloadfichier(i,dialogProgressWin=dialogProgressWin,curPercent=percent,coeff=coeff*curDirListSize)
                    
                try :

                    #Mise a jour de la barre de progression (via callback)
                    #TODO: Solution temporaraire -> on veut afficher le nom du theme/script/skin en cours en plus du fichier
                    dialogProgressWin.update(100,"T�l�chargement Total: %d%%"%percent, "%s"%i)
                except Exception, e:
                    print("downloadVideo - Exception calling UI callback for download")
                    print(e)
                    print progressbar_cb

        return 1 # 1 pour telechargement OK

    def _downloaddossier(self, dirsrc,progressbar_cb=None,dialogProgressWin=None,curPercent=0,coeff=1):
        """
        Fonction privee (ne pouvant etre appelee que par la classe ftpDownloadCtrl elle meme)
        Telecharge un repertoire sur le server FTP
        Note: fait un appel RECURSIF sur _download
        """
        print "_downloaddossier: %s"%dirsrc
        emptydir = False
        
#        self.ftp.cwd(dirsrc) # c'est cette commande qui genere l'exception dans le cas d'un fichier
#        print "_downloaddossier: %s est un repertoire"%dirsrc
        try:
            dirContent = self.ftp.nlst(dirsrc)
            print dirContent
        except Exception, e:
            # Repertoire non vide -> il faut telecharger les elementss de ce repertoire
            emptydir = True

        # Cree le chemin du repertorie local
        # Extrait le chemin relatif: soustrait au chemin remote le chemin de base: par exemple on veut retirer du chemin; /.passionxbmc/Themes
        remoteRelDirPath = dirsrc.replace(self.curRemoteDirRoot,'')

        # On remplace dans le chemin sur le serveur FTP les '/' par le separateur de l'OS sur lequel on est
        localRelDirPath = remoteRelDirPath.replace('/',os.sep)

        # Cree le chemin local (ou on va sauver)
        localAbsDirPath = os.path.join(self.curLocalDirRoot, localRelDirPath)

        try:
            os.makedirs(localAbsDirPath)
        except Exception, e:
            print "_downloaddossier: Exception - Impossible de creer le dossier: %s"%dirsrc
            print e
        if (emptydir == True):
            #print "_downloaddossier: Repertoire %s VIDE"%dirsrc
            pass
        else:
            # Repertoire non vide - lancement du download (!!!APPEL RECURSIF!!!)
            self._download(dirsrc,dialogProgressWin=dialogProgressWin,curPercent=curPercent,coeff=coeff)

    def _downloadfichier(self, filesrc,dialogProgressWin=None,curPercent=0,coeff=1):
        """
        Fonction privee (ne pouvant etre appelee que par la classe ftpDownloadCtrl elle meme)
        Telecharge un fichier sur le server FTP
        """
        # Recupere la taille du fichier
        print "_downloadfichier: %s"%filesrc
        remoteFileSize = 1
        #block_size = 4096
        block_size = 2048
        try:
            self.ftp.sendcmd('TYPE I')
            remoteFileSize = int(self.ftp.size(filesrc))
            print "Taille du fichier %s sur le serveur: %d"%(os.path.basename(filesrc),remoteFileSize)
            #self.ftp.sendcmd('TYPE A')
        except Exception, e:
            print "_downloadfichier: Excpetion lors la recuperation de la taille du fichier: %s"%filesrc
            print e
            traceback.print_exc(file = sys.stdout)
        
        # Cree le chemin du repertorie local
        # Extrait le chemin relatif: soustrait au chemin remote le chemin de base: par exemple on veut retirer du chemin; /.passionxbmc/Themes
        remoteRelFilePath = filesrc.replace(self.curRemoteDirRoot,'')

        # On remplace dans le chemin sur le serveur FTP les '/' par le separateur de l'OS sur lequel on est
        localRelFilePath = remoteRelFilePath.replace('/',os.sep)

        # Cree le chemin local (ou on va sauver)
        localAbsFilePath = xbmc.translatePath(os.path.join(self.curLocalDirRoot, localRelFilePath))
        #localFileName = os.path.basename(localAbsFilePath)

        localFile = open(localAbsFilePath, "wb")
        try:
            #self.ftp.retrbinary('RETR ' + filesrc, localFile.write)
            ftpCB = FtpCallback(remoteFileSize, localFile,filesrc,dialogProgressWin,curPercent,coeff*remoteFileSize)
            #self.ftp.sendcmd('TYPE I')
            #self.ftp.retrbinary('RETR ' + filesrc, ftpCB, block_size)
            self.retrbinary('RETR ' + filesrc, ftpCB, block_size)
            # On ferme le fichier
        except Exception, e:
            print "_downloadfichier: Exception lors la recuperation du fichier: %s"%filesrc
            print e
            traceback.print_exc(file = sys.stdout)
        # On ferme le fichier
        localFile.close()
        
    def retrbinary(self, cmd, callback, blocksize=8192,rest=None):
        """
        Cette version de retrbinary permet d'interompte un telechargement en cours alors que la version de ftplib ne le permet pas
        Inspir� du code dispo a http://www.archivum.info/python-bugs-list@python.org/2007-03/msg00465.html
        """
        self.ftp.voidcmd('TYPE I')
        conn = self.ftp.transfercmd(cmd, rest)
        fp = conn.makefile('rb')
        while 1:
            #data = conn.recv(blocksize)
            data = fp.read()    #blocksize)
            if not data:
                break
            try:
                callback(data)
            except cancelRequest:
                #except IOError, (errno, strerror):
                traceback.print_exc(file = sys.stdout)
                print "retrbinary: Download ARRETE par l'utilisateur"
                break
        fp.close()
        conn.close()
        return self.ftp.voidresp()

        
        
class FtpCallback(object):
    """
    Inspired from source Justin Ezequiel (Thanks)
    http://coding.derkeiler.com/pdf/Archive/Python/comp.lang.python/2006-09/msg02008.pdf
    """
    def __init__(self, filesize, localfile, filesrc, dp=None, curPercent=0, coeff=1):
        self.filesize   = filesize
        self.localfile  = localfile
        self.srcName    = filesrc
        self.received   = 0
        self.curPercent = curPercent
        self.coeff      = coeff
        self.dp         = dp
        print filesize
        print self.filesize
        print  self.localfile
        print self.received
        print self.curPercent
        print self.coeff
        print self.dp

        
    def __call__(self, data):
        if self.dp != None:
            if self.dp.iscanceled(): 
                print "FtpCallback: DOWNLOAD CANCELLED" # need to get this part working
                #dp.close() #-> will be close in calling function
                #raise IOError
                raise cancelRequest,"User pressed CANCEL button"
        self.localfile.write(data)
        self.received += len(data)
        #print '\r%.3f%%' % (100.0*self.received/self.filesize)
        try:
            percent = min((self.received*100)/self.filesize, 100)
            #percent = min(curPercent + int((float(curDirList.index(i)+1)*100)/(curDirListSize * coeff)),100)
            #percent = min(int(float(self.curPercent) + (float(self.received*100)/(self.filesize * self.coeff))),100)
            print "FtpCallback - percent = %s%%"%percent
            if self.dp != None:
                self.dp.update(percent,"T�l�chargement Total: %d%%"%self.curPercent, "%s"%self.srcName)
        except Exception, e:        
            print("FtpCallback - Exception during percent computing AND update")
            print(e)
            percent = 100
            traceback.print_exc(file = sys.stdout)
            if self.dp != None:
                #TODO: garder le titre principal
                #self.dp.update(self.curPercent,"%s:"%(self.localFileName),"%d%%"%(percent))
                self.dp.update(percent,"T�l�chargement Total: %d%%"%self.curPercent, "%s"%(self.srcName))

class MainWindow(xbmcgui.Window):
    """

    Interface graphique

    """
    def __init__(self):
        """
        Initialisation de l'interface
        """
        if Emulating: xbmcgui.Window.__init__(self)
        if not Emulating:
            self.setCoordinateResolution(PAL_4x3) # Set coordinate resolution to PAL 4:3

        #TODO: TOUTES ces varibales devraient etre passees en parametre du constructeur de la classe (__init__ si tu preferes)
        # On ne devraient pas utiliser de variables globale ou rarement en prog objet

        self.host               = host
        self.user               = user
        self.rssfeed            = rssfeed
        self.password           = password
        self.remotedirList      = remoteDirLst
        self.localdirList       = localDirLst
        self.downloadTypeList   = downloadTypeLst
        
        self.racineDisplayList  = racineDisplayLst
        self.pluginDisplayList  = pluginDisplayLst
         
#        self.remotePluginDirList    = remotePluginDirLst     
#        self.localPluginDirList     = localPluginDirLst
#        self.pluginTypeList         = pluginTypeLst
        self.curDirList         = []
        self.connected          = False # status de la connection (inutile pour le moment)
        #self.racine             = RACINE
        self.index              = ""
        self.scraperDir         = scraperDir
        self.type               = "racine"
#        self.numindex           = ""
        self.USRPath            = USRPath
        self.rightstest         = ""
        self.scriptDir          = scriptDir
        self.extracter          = scriptextracter() # On cree un instance d'extracter
        self.CacheDir           = CACHEDIR
        self.targetDir          = ""
        self.delCache           = ""
        self.scrollingSizeMax   = 480
        self.RssOk              = False

        # Display Loading Window while we are loading the information from the website
        dialogUI = xbmcgui.DialogProgress()
        dialogUI.create("Installeur Passion XBMC", "Creation de l'interface Graphique", "Veuillez patienter...")

        # Verifie si les repertoires cache et imagedir existent et les cree s'il n'existent pas encore
        self.verifrep(CACHEDIR)
        self.verifrep(IMAGEDIR)

        #TODO: A nettoyer, ton PMIIIDir n'est pas defini pour XBOX sans le test si dessous
        if self.USRPath == True:
            self.PMIIIDir = PMIIIDir


        # Background image
        self.addControl(xbmcgui.ControlImage(0,0,720,576, os.path.join(IMAGEDIR,"background.png")))

        # Set List border image
        self.listborder = xbmcgui.ControlImage(19,120,681,446, os.path.join(IMAGEDIR, "list-border.png"))
        self.addControl(self.listborder)
        self.listborder.setVisible(True)

        # Set List background image
        self.listbackground = xbmcgui.ControlImage(20, 163, 679, 402, os.path.join(IMAGEDIR, "list-white.png"))
        self.addControl(self.listbackground)
        self.listbackground.setVisible(True)

        # Set List hearder image
        # print ("Get Logo image from : " + os.path.join(IMAGEDIR,"logo.gif"))
        self.header = xbmcgui.ControlImage(20,121,679,41, os.path.join(IMAGEDIR, "list-header.png"))
        self.addControl(self.header)
        self.header.setVisible(True)

        # Title of the current pages
        self.strMainTitle = xbmcgui.ControlLabel(35, 130, 200, 40, "S�lection", 'special13')
        self.addControl(self.strMainTitle)

        # item Control List
        self.list = xbmcgui.ControlList(22, 166, 674 , 420,'font14','0xFF000000', buttonTexture = os.path.join(IMAGEDIR,"list-background.png"),buttonFocusTexture = os.path.join(IMAGEDIR,"list-focus.png"), imageWidth=40, imageHeight=32, itemTextXOffset=0, itemHeight=55)
        self.addControl(self.list)

        # Version and author(s):
        self.strVersion = xbmcgui.ControlLabel(621, 69, 350, 30, version, 'font10','0xFF000000', alignment=1)
        self.addControl(self.strVersion)

        # Recupeartion du Flux RSS
        try:
            # Cree une instance de rssReader recuperant ainsi le flux/page RSS
            self.passionRssReader = rssReader(self.rssfeed)
            #print "Flux RSS page:"
            #print self.passionRssReader.rssPage
            # Extraction des infos du la page RSS
            maintitle,title = self.passionRssReader.GetRssInfo()
            self.RssOk = True

        except Exception, e:
            print "Window::__init__: Exception durant la recuperation du Flux RSS",e
            # Message a l'utilisateur
            dialogRssError = xbmcgui.Dialog()
            dialogRssError.ok("Erreur", "Impossible de recuperer le flux RSS")
            print ("error/MainWindow __init__: " + str(sys.exc_info()[0]))
            traceback.print_exc()

        if (self.RssOk == True):
            # Scrolling message
            self.scrollingText = xbmcgui.ControlFadeLabel(20, 87, 680, 30, 'font12', '0xFFFFFFFF')
            self.addControl(self.scrollingText)
            scrollStripTextSize = len(title)

            # Afin d'avoir un message assez long pour defiler, on va ajouter des espaces afin d'atteindre la taille max de self.scrollingSizeMax
            scrollingLabel = title.rjust(self.scrollingSizeMax)
            scrollingLabelSize = len(scrollingLabel)
            self.scrollingText.addLabel(scrollingLabel)
            #self.scrollingText.setVisible(False)

        # Connection au serveur FTP
        try:
            
            self.passionFTPCtrl = ftpDownloadCtrl(self.host,self.user,self.password,self.remotedirList,self.localdirList,self.downloadTypeList)
            self.connected = True

            # Recuperation de la liste des elements
            self.updateList()

        except Exception, e:
            print "Window::__init__: Exception durant la connection FTP",e
            print "Impossible de se connecter au serveur FTP: %s"%self.host
            dialogError = xbmcgui.Dialog()
            dialogError.ok("Erreur", "Exception durant l'initialisation")
            print ("error/MainWindow __init__: " + str(sys.exc_info()[0]))
            traceback.print_exc()

        # Close the Loading Window
        dialogUI.close()

    def onAction(self, action):
        """
        Remonte l'arborescence et quitte le script
        """
        try:
            if action == ACTION_PREVIOUS_MENU:

                # Sortie du script
                #print('action recieved: previous')

                # On se deconnecte du serveur pour etre plus propre
                self.passionFTPCtrl.closeConnection()

                # On vide le cache
                #if self.delCache == True:
                self.delFiles(CACHEDIR)

                #on ferme tout
                self.close()

            if action == ACTION_PARENT_DIR:
                #remonte l'arborescence
                print ("Previous page requested")
                # On verifie si on est a l'interieur d'un ses sous section plugin 
                if (self.type == "Plugins Musique") or (self.type == "Plugins Images") or (self.type == "Plugins Programmes") or (self.type == "Plugins Vid�os"):
                    print "Nous sonnmes dans la sous-section : %s"%self.type
                    print "Nous sremontons dans la section Plugins"
                    self.type = "Plugins"
                    try:
                        print "Appel updateList()"
                        self.updateList()
                    except Exception, e:
                        print "Window::onAction ACTION_PREVIOUS_MENU: Exception durant updateList()",e
                        print ("error/onaction: " + str(sys.exc_info()[0]))
                        traceback.print_exc()
                else:
                    # cas standard
                    print "Nous sonnmes dans la section : %s"%self.type
                    print "Nous sremontons a la racine"
                    #self.racine = True
                    self.type = "racine"
                    try:
                        print "Appel updateList()"
                        self.updateList()
                    except Exception, e:
                        print "Window::onAction ACTION_PREVIOUS_MENU: Exception durant updateList()",e
                        print ("error/onaction: " + str(sys.exc_info()[0]))
                        traceback.print_exc()
                
        except Exception, e:
            print "Window::onAction: Exception",e
            print ("error/onaction: " + str(sys.exc_info()[0]))
            traceback.print_exc()

    def onControl(self, control):
        """
        Traitement si selection d'un element de la liste
        """
        try:
            if control == self.list:

                #if (self.racine == True):
                if (self.type   == "racine"):
                    #self.racine = False
                    self.index = self.list.getSelectedPosition()
                    #self.type = self.downloadTypeList[self.list.getSelectedPosition()]
                    self.type = self.downloadTypeList[self.racineDisplayList[self.list.getSelectedPosition()]] # On utilise le filtre
                    
                    print "Type courant est Racine - nouveau type est:%s"%self.type
                    print "Mise a jour de la liste"

                    self.updateList() #on raffraichit la page pour afficher le contenu

                elif (self.type   == "Plugins"):
                    #self.racine = False
                    self.index = self.list.getSelectedPosition()
                    #self.type = self.downloadTypeList[self.list.getSelectedPosition()]
                    self.type = self.downloadTypeList[self.pluginDisplayList[self.list.getSelectedPosition()]] # On utilise le filtre
                    
                    print "Type courant est Plugins - nouveau type est:%s"%self.type
                    print "Mise a jour de la liste"
                    
                    self.updateList() #on raffraichit la page pour afficher le contenu

#                elif (self.type == "Plugins Musique") or (self.type == "Plugins Images") or (self.type == "Plugins Programmes") or (self.type == "Plugins Vid�os"):
#                    pass
                else:
                    downloadOK = True
                    correctionPM3bidon = False
                    self.index = self.list.getSelectedPosition()
                    source = self.curDirList[self.index]

                    if self.type == self.downloadTypeList[0]:   #Themes
                        # Verifions le themes en cours d'utilisation
                        mySkinInUse = xbmc.getSkinDir()
                        if mySkinInUse in source:
                            # Impossible de telecharger une skin en cours d'utlisation
                            dialog = xbmcgui.Dialog()
                            dialog.ok('Action impossible', "Vous ne pouvez �craser le Theme en cours d'utilisation", "Merci de changer le Theme en cours d'utilisation", "avant de le t�l�charger")
                            downloadOK = False
                        if 'Project Mayhem III' in source and self.USRPath == True:
                            self.linux_chmod(self.PMIIIDir)
                            if self.rightstest == True:
                                self.localdirList[0]= self.PMIIIDir
                                downloadOK = True
                                correctionPM3bidon = True
                            else:
                                dialog = xbmcgui.Dialog()
                                dialog.ok('Action impossible', "Vous ne pouvez installer ce theme sans les droits", "d'administrateur")
                                downloadOK = False


                    elif self.type == self.downloadTypeList[1] and self.USRPath == True:   #Linux Scrapers
                        self.linux_chmod(self.scraperDir)
                        if self.rightstest == True :
                            downloadOK = True
                        else:
                            dialog = xbmcgui.Dialog()
                            dialog.ok('Action impossible', "Vous ne pouvez installer le scraper sans les droits", "d'administrateur")
                            downloadOK = False
                            
#                    elif (self.type == "Plugins Musique") or (self.type == "Plugins Images") or (self.type == "Plugins Programmes") or (self.type == "Plugins Vid�os"):
#                        pass
                    if source.endswith('zip') or source.endswith('rar'):
                        #self.delCache = True
#                        self.targetDir = self.localdirList[self.numindex]
#                        self.localdirList[self.numindex]= self.CacheDir
                        self.targetDir = self.localdirList[self.downloadTypeList.index(self.type)]
                        self.localdirList[self.downloadTypeList.index(self.type)]= self.CacheDir
                        
                        
                        print "%s remplace par %s"%(self.targetDir,self.localdirList[self.downloadTypeList.index(self.type)])
                        print "self.downloadTypeList.index(self.type) = %s"%self.downloadTypeList.index(self.type)
                        print "self.localdirList"
                        print self.localdirList


                    if downloadOK == True:
                        continueDownload = True
                        
                        # on verifie le si on a deja telecharge cet element (ou une de ses version anterieures)
                        isDirDownloaded,localDirPath = self.passionFTPCtrl.isDirAlreadyDownloaded(source, self.remotedirList[self.downloadTypeList.index(self.type)], self.downloadTypeList.index(self.type))
                        print "isDirDownloaded:"
                        print isDirDownloaded
                    
                        if (isDirDownloaded) and  (localDirPath != None):
                            print "Repertoire deja present localement"
                            # On traite le repertorie deja present en demandant a l'utilisateur de choisir
                            continueDownload = self.processOldDownload(localDirPath)

                        if continueDownload == True:
                            #fenetre de telechargement
                            dp = xbmcgui.DialogProgress()
                            lenbasepath = len(self.remotedirList[self.downloadTypeList.index(self.type)])
                            downloadItem = source[lenbasepath:]
                            percent = 0
                            dp.create("T�l�chargement: %s"%downloadItem,"T�l�chargement Total: %d%%"%percent)
                            
                            # Type est desormais reellement le type de download, on utlise alors les liste pour recuperer le chemin que l'on doit toujours passer
                            # on appel la classe passionFTPCtrl avec la source a telecharger                        
                            downloadStatus = self.passionFTPCtrl.download(source, self.remotedirList[self.downloadTypeList.index(self.type)], self.downloadTypeList.index(self.type),progressbar_cb=self.updateProgress_cb,dialogProgressWin = dp)
                            dp.close()
                            #print "downloadStatus %d"%downloadStatus
    
    
                            #On se base sur l'extension pour determiner si on doit telecharger dans le cache.
                            #Un tour de passe passe est fait plus haut pour echanger les chemins de destination avec le cache, le chemin de destination
                            #est retabli ici 'il s'agit de targetDir'
                            if downloadItem.endswith('zip') or downloadItem.endswith('rar'):
                                #Appel de la classe d'extraction des archives
                                print "self.localdirList"
                                print self.localdirList
                                print "Extraction de l'archives: %s"%downloadItem
                                remoteDirPath = self.remotedirList[self.downloadTypeList.index(self.type)]#chemin ou a ete telecharge le script
                                localDirPath = self.localdirList[self.downloadTypeList.index(self.type)]
                                print "localDirPath = %s"%localDirPath
                                archive = source.replace(remoteDirPath,localDirPath + os.sep)#remplacement du chemin de l'archive distante par le chemin local temporaire
                                print "archive = %s"%archive
                                self.localdirList[self.downloadTypeList.index(self.type)]= self.targetDir
                                fichierfinal0 = archive.replace(localDirPath,self.localdirList[self.downloadTypeList.index(self.type)])
                                if fichierfinal0.endswith('.zip'):
                                    fichierfinal = fichierfinal0.replace('.zip','')
                                elif fichierfinal0.endswith('.rar'):
                                    fichierfinal = fichierfinal0.replace('.rar','')
    
                                print "fichierfinal = %s"%fichierfinal
                                # On n'a besoin d'ue d'un instance d'extracteur sinon on va avoir une memory leak ici car on ne le desalloue jamais
                                # Je l'ai donc creee dans l'init comme attribut de la classe
                                #extracter = scriptextracter()
                                self.extracter.extract(archive,self.localdirList[self.downloadTypeList.index(self.type)])
    
                            if downloadStatus == -1:
                                # Telechargment annule par l'utilisateur
                                title    = "T�l�chargement annul�"
                                message1 = "%s: %s"%(self.type,downloadItem)
                                message2 = "T�l�chargement annul� alors qu'il etait en cours "
                                message3 = "Il se peut que des fichiers aient d�j� �t� t�l�charg�s"
                            else:
                                title    = "T�l�chargement termin�"
                                message1 = "%s: %s"%(self.type,downloadItem)
                                message2 = "a �t� t�l�charg� dans le repertoire:"
                                message3 = "%s"%self.localdirList[self.downloadTypeList.index(self.type)]
    
                            dialogInfo = xbmcgui.Dialog()
                            dialogInfo.ok(title, message1, message2,message3)
    
    
                            #TODO: Attention correctionPM3bidon n'est pa defini dans le cas d'un scraper ou script
                            #      Je l;ai donc defini a False au debut
                            # On remet a la bonne valeur initiale self.localdirList[0]
                            if correctionPM3bidon == True:
                                self.localdirList[0] = themesDir
                                correctionPM3bidon = False
        except:
            print ("error/onControl: " + str(sys.exc_info()[0]))
            traceback.print_exc()

    def updateProgress_cb(self, percent, dp=None):
        """
        Met a jour la barre de progression
        """
        #TODO Dans le futur, veut t'on donner la responsabilite a cette fonction le calcul du pourcentage????
        try:
            print percent
            dp.update(percent)
        except:
            percent = 100
            dp.update(percent)

    def updateList(self):
        """
        Mise a jour de la liste affichee
        """
        #if (self.racine == True):
        # On verifie self.type qui correspond au type de liste que l'on veut afficher
        if (self.type  == "racine"):
            #liste virtuelle des sections
#            del self.curDirList[:] # on vide la liste
#            
#            # On utilise le filtre pour creer la liste d'affichage
#            for idx in self.racineDisplayList:
#                self.curDirList.append(self.racineDisplayList[idx]) 
            self.curDirList = self.racineDisplayList
            
            print "self.curDirList pour la Racine:"
            print self.curDirList
            
        elif (self.type  == "Plugins"):
            #liste virtuelle des sections
#            del self.curDirList[:] # on vide la liste
#            
#            # On utilise le filtre pour creer la liste d'affichage
#            for idx in self.pluginDisplayList:
#                self.curDirList.append(self.pluginDisplayList[idx]) 

            self.curDirList = self.pluginDisplayList

            print "self.curDirList pour Plugins"
            print self.curDirList
            
        elif (self.type == "Plugins Musique") or (self.type == "Plugins Images") or (self.type == "Plugins Programmes") or (self.type == "Plugins Vid�os"):
            self.curDirList = self.passionFTPCtrl.getDirList(self.remotedirList[self.pluginDisplayList[self.index]])
            print "self.curDirList pour une section"
            print self.curDirList
            
        else:
            #liste virtuelle des sections
            #del self.curDirList[:] # on vide la liste

            #liste physique d'une section sur le ftp
            #self.curDirList = self.ftp.nlst(self.remotedirList[self.index])
            self.curDirList = self.passionFTPCtrl.getDirList(self.remotedirList[self.index])
            print "self.curDirList pour une section"
            print self.curDirList

        print self.curDirList
        xbmcgui.lock()
        # Clear all ListItems in this control list
        self.list.reset()

        # Calcul du mobre d'elements de la liste
        itemnumber = len(self.curDirList)

        # On utilise la fonction range pour faire l'iteration sur index
        for j in range(itemnumber):
            #if (self.racine == False):
            if (self.type  == "racine") or (self.type  == "Plugins"):
                # Element de la liste
                if (self.type  == "racine"):
                    sectionName = self.downloadTypeList[self.racineDisplayList[j]] # On utilise le filtre
                    # Met a jour le titre:
                    self.strMainTitle.setLabel("S�lection")
                elif (self.type  == "Plugins"):
                    sectionName = self.downloadTypeList[self.pluginDisplayList[j]] # On utilise le filtre
                    # Met a jour le titre:
                    self.strMainTitle.setLabel("Plugins")

                print "updateList : cas racine et plugins"
                # Affichage de la liste des sections
                # -> On compare avec la liste affichee dans l'interface
                #sectionName = self.downloadTypeList[j]
                if sectionName == self.downloadTypeList[0]:
                    imagePath = os.path.join(IMAGEDIR,"icone_theme.png")
                elif sectionName == self.downloadTypeList[1]:
                    imagePath = os.path.join(IMAGEDIR,"icone_scrapper.png")
                elif sectionName == self.downloadTypeList[2]:
                    imagePath = os.path.join(IMAGEDIR,"icone_script.png")
                elif sectionName == self.downloadTypeList[3]:
                    imagePath = os.path.join(IMAGEDIR,"icone_script.png")
                else:
                    # Image par defaut (ou aucune si = "")
                    imagePath = imagePath = os.path.join(IMAGEDIR,"icone_script.png")

                displayListItem = xbmcgui.ListItem(label = sectionName, thumbnailImage = imagePath)
                self.list.addItem(displayListItem)
                
#            elif (self.type  != "Plugins"):
#                pass
            elif (self.type == "Plugins Musique") or (self.type == "Plugins Images") or (self.type == "Plugins Programmes") or (self.type == "Plugins Vid�os"):
                # Element de la liste
                ItemListPath = self.curDirList[j]
                
                #self.numindex = self.index
                print "updateList : sous-sectipn %s"%self.type
                lenindex = len(self.remotedirList[self.pluginDisplayList[self.index]]) # on a tjrs besoin de connaitre la taille du chemin de base pour le soustraire/retirer du chemin global plus tard
                
                #TODO: creer de nouveau icones pour les sous-sections plugins
                # Met a jour le titre et les icones:
                if self.type == self.downloadTypeList[4]:   #Themes
                    self.strMainTitle.setLabel(str(itemnumber) + " Plugins Musique")
                    imagePath = os.path.join(IMAGEDIR,"icone_theme.png")
                elif self.type == self.downloadTypeList[5]: #Scrapers
                    self.strMainTitle.setLabel(str(itemnumber) + " Plugins Images")
                    imagePath = os.path.join(IMAGEDIR,"icone_scrapper.png")
                elif self.type == self.downloadTypeList[6]: #Scripts
                    self.strMainTitle.setLabel(str(itemnumber) + " Plugins Programmes")
                    imagePath = os.path.join(IMAGEDIR,"icone_script.png")
                elif self.type == self.downloadTypeList[7]: #Plugins
                    self.strMainTitle.setLabel(str(itemnumber) + " Plugins Vid�os")
                    imagePath = os.path.join(IMAGEDIR,"icone_script.png")
                else:
                    # Image par defaut (ou aucune si = "")
                    imagePath = ""

                item2download = ItemListPath[lenindex:]

                displayListItem = xbmcgui.ListItem(label = item2download, thumbnailImage = imagePath)
                self.list.addItem(displayListItem)
                
            else:
                # Element de la liste
                ItemListPath = self.curDirList[j]
                
                print "updateList : autres cas"
                #affichage de l'interieur d'une section
                #self.numindex = self.index
                lenindex = len(self.remotedirList[self.index]) # on a tjrs besoin de connaitre la taille du chemin de base pour le soustraire/retirer du chemin global plus tard

                # Met a jour le titre et les icones:
                if self.type == self.downloadTypeList[0]:   #Themes
                    self.strMainTitle.setLabel(str(itemnumber) + " Themes")
                    imagePath = os.path.join(IMAGEDIR,"icone_theme.png")
                elif self.type == self.downloadTypeList[1]: #Scrapers
                    self.strMainTitle.setLabel(str(itemnumber) + " Scrapers")
                    imagePath = os.path.join(IMAGEDIR,"icone_scrapper.png")
                elif self.type == self.downloadTypeList[2]: #Scripts
                    self.strMainTitle.setLabel(str(itemnumber) + " Scripts")
                    imagePath = os.path.join(IMAGEDIR,"icone_script.png")
#                elif self.type == self.downloadTypeList[3]: #Plugins
#                    self.strMainTitle.setLabel(str(itemnumber) + " Plugins")
#                    imagePath = os.path.join(IMAGEDIR,"icone_script.png")
                else:
                    # Image par defaut (ou aucune si = "")
                    imagePath = ""

                item2download = ItemListPath[lenindex:]

                displayListItem = xbmcgui.ListItem(label = item2download, thumbnailImage = imagePath)
                self.list.addItem(displayListItem)
        xbmcgui.unlock()
        # Set Focus on list
        self.setFocus(self.list)

    def deleteDir(self,path):
        """
        Efface un repertoir et tout son contenu (le repertoire n'a pas besoin d'etre vide)
        """
        dirItems=os.listdir(path)
        for item in dirItems:
            itemFullPath=os.path.join(path, item)   
            try:
                if os.path.isfile(itemFullPath):
                    # Fichier
                    os.remove(itemFullPath)
                elif os.path.isdir(itemFullPath):
                    # Repertoire
                    self.deleteDir(itemFullPath)
            except Exception, e: 
                print "deleteDir: Exception la suppression du reperoire: %s"%path
                print e
                traceback.print_exc(file = sys.stdout)
        # Suppression du repertoire pere        
        os.rmdir(path)            

    def delFiles(self,folder):
        """
        Source: Joox
        Efface tous le fichier d'un repertorie donne ainsi que des sous-repertoires
        Note: les sous-repertoires eux-memes ne sont pas effaces
        folder: chemin du repertpoire local
        """
        for root, dirs, files in os.walk(folder , topdown=False):
            for name in files:
                try:
                    os.remove(os.path.join(root, name))
                except Exception, e:
                    print e

    def verifrep(self,folder):
        """
        Source: myCine
        Verifie l'existance  d'un repertoire et le cree si besoin
        """
        try:
            if not os.path.exists(folder):
                os.makedirs(folder)
        except Exception, e:
            print("verifrep - Exception durant la creation du repertoire: " + folder)
            print(e)
            pass

    def linux_chmod(self,path):
        """
        Effectue un chmod sur un repertoire pour ne plus etre bloque par les droits root sur plateforme linux
        """
        Wtest = os.access(path,os.W_OK)
        if Wtest == True:
            self.rightstest = True
            print "rightest OK"
        else:
            dialog = xbmcgui.Dialog()
            dialog.ok('Demande de mot de passe', "Vous devez saisir votre mot de passe administrateur", "systeme")
            keyboard = xbmc.Keyboard("","Mot de passe Administrateur", True)
            keyboard.doModal()
            if (keyboard.isConfirmed()):
                password = keyboard.getText()
                PassStr = "echo %s | "%password
                ChmodStr = "sudo -S chmod 777 -R %s"%path
                try:
                    os.system(PassStr + ChmodStr)
                    self.rightstest = True

                except Exception, e:
                    print "erreur CHMOD %s"%path
                    print e
                    self.rightstest = False
            else:
                self.rightstest = False

    def processOldDownload(self,localAbsDirPath):
        """
        Traite les ancien download suivant les desirs de l'utilisateur
        retourne True si le download peut continuer.
        """
        continueDownload = True
        
        # Verifie se on telecharge un repertoire ou d'un fichier
        if os.path.isdir(localAbsDirPath):
            # Repertoire
            print "processOldDownload: Repertoire : %s"%localAbsDirPath
            menuList = ["Ecraser (sans supprimer)","Supprimer puis     ","Renommer puis t�l�charger","Annuler"]
            dialog = xbmcgui.Dialog()
            chosenIndex = dialog.select("%s est deja present, que d�sirez vous faire?"%(os.path.basename(localAbsDirPath)), menuList)               
            #if (dialog.yesno("Erreur", "%s est deja present, voulez vous le renommer"%(os.path.basename(localAbsDirPath)),"Sinon il sera �cras�")):
            if chosenIndex == 0: 
                # Ecraser
                pass
            if chosenIndex == 1: 
                # Supprimer
                print "Suppression du repertoire"
                self.deleteDir(localAbsDirPath)
            elif chosenIndex == 2: # Renommer
                # Suppression du repertoire
                print "On renomme le repertoire"
                keyboard = xbmc.Keyboard("", heading = "Saisir le nouveau nom:")
                keyboard.setHeading('Saisir le nouveau nom:')  # optional
                keyboard.setDefault(os.path.basename(localAbsDirPath))                    # optional

                keyboard.doModal()
                if (keyboard.isConfirmed()):
                    inputText = keyboard.getText()
                    print"Nouveau nom: %s"%inputText
                    os.rename(localAbsDirPath,localAbsDirPath.replace(os.path.basename(localAbsDirPath),inputText))
                    dialogInfo = xbmcgui.Dialog()
                    dialogInfo.ok("L'element a ete renomm�:", localAbsDirPath.replace(os.path.basename(localAbsDirPath),inputText))
                del keyboard
            else:
                print "Annulation"
                continueDownload = False
        else:
            # Fichier archive
            print "processOldDownload: Fichier archive : %s"%localAbsDirPath
            
        return continueDownload

                

########
#
# Main
#
########



def go():
    #Fonction de demarrage
    w = MainWindow()
    w.doModal()
    print "Delete Window"
    del w
    print "INSTALLEUR - Fin go"

ROOTDIR = os.getcwd().replace(';','')

##############################################################################
#                   Initialisation conf.cfg                                  #
##############################################################################
fichier = os.path.join(ROOTDIR, "conf.cfg")
config = ConfigParser.ConfigParser()
config.read(fichier)

##############################################################################
#                   Initialisation parametres locaux                         #
##############################################################################
IMAGEDIR        = config.get('InstallPath','ImageDir')
CACHEDIR        = config.get('InstallPath','CacheDir')
themesDir       = config.get('InstallPath','ThemesDir')
scriptDir       = config.get('InstallPath','ScriptsDir')
scraperDir      = config.get('InstallPath','ScraperDir')
pluginDir       = config.get('InstallPath','PluginDir')
pluginMusDir    = config.get('InstallPath','PluginMusDir')
pluginPictDir   = config.get('InstallPath','PluginPictDir')
pluginProgDir   = config.get('InstallPath','PluginProgDir')
pluginVidDir    = config.get('InstallPath','PluginVidDir')
USRPath         = config.getboolean('InstallPath','USRPath')
if USRPath == True:
    PMIIIDir = config.get('InstallPath','PMIIIDir')
RACINE = True

##############################################################################
#                   Initialisation parametres serveur                        #
##############################################################################
host                = config.get('ServeurID','host')
user                = config.get('ServeurID','user')
rssfeed             = config.get('ServeurID','rssfeed')
password            = config.get('ServeurID','password')

downloadTypeLst     = ["Themes","Scrapers","Scripts","Plugins","Plugins Musique","Plugins Images","Plugins Programmes","Plugins Vid�os"]
#TODO: mettre les chemins des rep sur le serveur dans le fichier de conf
remoteDirLst        = ["/.passionxbmc/Themes/","/.passionxbmc/Scraper/","/.passionxbmc/Scripts/","/.passionxbmc/Plugins/","/.passionxbmc/Plugins/Music/","/.passionxbmc/Plugins/Pictures/","/.passionxbmc/Plugins/Programs/","/.passionxbmc/Plugins/Videos/"]
localDirLst         = [themesDir,scraperDir,scriptDir,pluginDir,pluginMusDir,pluginPictDir,pluginProgDir,pluginVidDir]

racineDisplayLst    = [0,1,2,3] # Liste de la racine: Cette liste est un filtre (utilisant l'index) sur les listes ci-dessus
pluginDisplayLst    = [4,5,6,7] # Liste des plugins : Cette liste est un filtre (utilisant l'index) sur les listes ci-dessus


## Plugins
#pluginTypeLst       = ["Plugins Musique","Plugins Images","Plugins Programmes","Plugins Vid�os"]
##TODO: mettre les chemins des rep sur le serveur dans le fichier de conf
#remotePluginDirLst  = ["/.passionxbmc/Plugins/Music","/.passionxbmc/Plugins/Pictures","/.passionxbmc/Plugins/Programs","/.passionxbmc/Plugins/Videos"]
#localPluginDirLst   = [pluginMusDir,pluginPictDir,pluginProgDir,pluginVidDir]

##############################################################################
#                   Version et auteurs                                       #
##############################################################################
version  = config.get('Version','version')
author   = 'Seb & Temhil'
designer = 'Jahnrik'

##############################################################################
#                   Verification parametres locaux et serveur                #
##############################################################################
print "FTP host: %s"%host
print "Chemin ou les themes seront telecharges: %s"%themesDir

print("===================================================================")
print("")
print("        Passion XBMC Installeur " + version + " STARTS")
print("        Auteurs : "+ author)
print("        Graphic Design by : "+ designer)
print("")
print("===================================================================")

if __name__ == "__main__":
    #ici on pourrait faire des action si le script �tait lanc� en tant que programme
    print "demarrage du script INSTALLEUR.py en tant que programme"
    go()
else:
    #ici on est en mode librairie import�e depuis un programme
    pass
