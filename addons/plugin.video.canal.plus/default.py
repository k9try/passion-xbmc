# -*- coding: cp1252 -*-
"""
plugin video Canal+ pour XBMC 

Installer dans in Q:\plugins\video\Canal Plus

19-11-08 Version 1.0 par Alexsolex
    - Creation
13-05-09 Version Pre2.0 par Temhil 
    - Adpatation du plugin suite a des modifications sur le site de Canal+
    - Ajout du menu option
    - Ajout du choix de visionnage (HD ou SD) des videos (via les options)
    - Support multilangue
    - Ajout description video via menu info
    - Les images sont desormais automatiquement telechargees par le plugin lui meme
    - Adaptation de la fonction de recherche au modifications du site
23-10-09 Version Pre2.0b by Temhil
    - Replaced separator in the URL "&" by "#" (broken due to change made in XBMC)
    - Added plugin variable for SVN repo installer infos
23-10-09 Version 2.0 by Temhil
    - Replaced XML parser BeautifulSoup by ElementTree (needed because some XML were not correctly formed)
    - Added support of new video stream URL, now http and rtmp urls are both supported
09-06-10 Version 2.1 by Frost
    - Modified the code for Dharma compatibility
11-10-10 Version 2.2 by Temhil
    - Moved cache and download directories to user data
    - some cleanup
"""

__script__       = "Unknown"
__plugin__       = "Canal Plus"
__addonID__      = "plugin.video.canal.plus"
__author__       = "Alexsolex / Temhil"
__url__          = "http://passion-xbmc.org/index.php"
__svn_url__      = "http://passion-xbmc.googlecode.com/svn/trunk/addons/plugin.video.canal.plus/"
__credits__      = "Team XBMC Passion"
__platform__     = "xbmc media center"
__date__         = "11-10-2010"
__version__      = "2.2"
__svn_revision__ = 0

import sys
if sys.modules.has_key("cplusplus"):
    del sys.modules['cplusplus']
import resources.libs.cplusplus as cpp

import traceback

import xbmc,xbmcgui,xbmcplugin

import os,os.path

import threading
from Queue import Queue, Empty

global q_in,q_out



import xbmcaddon
 
__addon__ = xbmcaddon.Addon( __addonID__ )
__settings__ = __addon__
__language__ = __addon__.getLocalizedString
__addonDir__ = __settings__.getAddonInfo( "path" )


def getfiles():
    # fonction ex�cut�e par les threads
    # ici je me contente de sauver le contenu avec l'url dans q_out
    global q_in
    global q_out
    try:
        while True:
            title,url,dest = q_in.get_nowait()
            cpp.Cache_Pic(url,dest)
            #thumbnail = download_pic(url,CACHEDIR)
            q_out.put((title,dest))
    except Empty:
        # q_in est vide; on a termin�
        pass

ADDON_DATA  = xbmc.translatePath( "special://profile/addon_data/%s/" % __addonID__ )
DOWNLOADDIR = os.path.join( ADDON_DATA, "downloads")
CACHEDIR    = os.path.join( ADDON_DATA, "cache")

# List of directories to check at startup
dirCheckList   = ( CACHEDIR, DOWNLOADDIR, ) #Tuple - Singleton (Note Extra ,)



def verifrep( folder ):
    """
        Source MyCine (thanks!)
        Check a folder exists and make it if necessary
    """
    try:
        #print("verifrep check if directory: " + folder + " exists")
        if not os.path.exists( folder ):
            print( "verifrep Impossible to find the directory - trying to create the directory: " + folder )
            os.makedirs( folder )
    except Exception, e:
        print( "Exception while creating folder " + folder )
        print( str( e ) )

def search_item():
    url = sys.argv[0]+"?search=&referer=%s"%(theme_id,theme_titre)
    item=xbmcgui.ListItem(theme_titre)
    ok = ok and xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),
                                            url=url,
                                            listitem=item,
                                            isFolder=True)    
def show_themes():
    """
    rempli la liste avec la liste des th�mes
    un lien va contenir :
        la commande 'listesubthemes'
        le parametre 'themeid'
    """
    ok = True
    
    url = sys.argv[0]+"?search=&theme_id=%s&subtheme_id=%s&referer=%s"%("Rechercher dans toutes les cat�gories :",
                                                                        "",
                                                                        "")
    item=xbmcgui.ListItem( __language__ ( 30001 ) ) # Recherche
    ok = ok and xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),
                                            url=url,
                                            listitem=item,
                                            isFolder=True)    
    themes=cpp.get_themes()
    for theme_id,theme_titre in themes:
        #A ce jour les ID inferieurs � 10000 sont vides
        #De plus les ID au dessus de 10000 sont redondants avec ceux en dessous
        #if int(theme_id) > 10000: 
        if int(theme_id) > 0: 
            url = sys.argv[0]+"?listesubthemes=%s&referer=%s"%(theme_id,theme_titre)
            item=xbmcgui.ListItem(theme_titre)
            ok = ok and xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),
                                                    url=url,
                                                    listitem=item,
                                                    isFolder=True,
                                                    totalItems=len(themes))
        else:
            pass
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_NONE)
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category= __language__ ( 30002 )) # Cat�gories
    return ok

def show_subthemes(theme_id,referer):
    """
    rempli la liste avec la liste des sous-th�mes pour le theme_id fourni
    un lien va contenir :
        la commande 'listevideos'
        les parametres 'themeid' et 'subthemeid'
    """
    ok = True
    url = sys.argv[0]+"?search=&theme_id=%s&subtheme_id=%s&referer=%s"%("Rechercher dans %s :"%referer,
                                                                        theme_id,
                                                                        "")
    item=xbmcgui.ListItem( __language__ ( 30001 ) ) # Recherche
    ok = ok and xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),
                                            url=url,
                                            listitem=item,
                                            isFolder=True)

    subthemes=cpp.get_subthemes(theme_id)
    i=0
    for subtheme_id,subtheme_titre in subthemes:
        i=i+1
        url = sys.argv[0]+"?listevideos=%s#%s&referer=%s"%(theme_id,subtheme_id,referer+">"+subtheme_titre)
        item=xbmcgui.ListItem(subtheme_titre)
        ok = ok and xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),
                                                url=url,
                                                listitem=item,
                                                isFolder=True,
                                                totalItems=len(subthemes))
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_NONE)
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=referer )
    return ok


def show_videos(theme_id,subtheme_id,referer,keyword=""):
    """
    rempli la liste avec la liste des videos
    un lien va contenir :
        la commande 'showvideoinfo'
        le param�tre 'videoID'
    """
    ok = True
    url = sys.argv[0]+"?search=&theme_id=%s&subtheme_id=%s&referer=%s"%("Rechercher dans %s"%referer,
                                                                        theme_id,
                                                                        subtheme_id)
    item=xbmcgui.ListItem( __language__ ( 30001 ) ) # Recherche
    ok = ok and xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),
                                            url=url,
                                            listitem=item,
                                            isFolder=True)
    xmlParam = cpp.get_xmlParam()
    i=0
    #ajout des �l�ments video clips de la page
    NUM_THREADS = 20
    global q_in,q_out
    q_in = Queue(0)
    q_out = Queue(0)

    pDialog = xbmcgui.DialogProgress()
    ret = pDialog.create( 'XBMC', __language__ ( 30200 ) )
    #chargement de la queue avec les identifiants de clips
    pDialog.update(0, __language__ ( 30201 ) )
    
    #videos = cpp.get_videos(xmlParam, theme_id=theme_id , subtheme_id = subtheme_id, keyword=keyword)
    videos = cpp.get_videos( subtheme_id = subtheme_id, keyword=keyword )
    cpt=0
    for video in videos:
        try:
            cpt=cpt+1
            pDialog.update(int(99*float(cpt)/(len(videos)*2)), __language__ ( 30202 ) )
            infos = cpp.get_info(video["videoID"])
            #url = sys.argv[0]+"?showvideoinfos="+video["videoID"]
            if int(__settings__.getSetting('video_quality') ) == 1: # Basse qualite
                url=infos["video.low"]
            else:
                url=infos["video.hi"]
            
#            q_in.put((video["title"],video['image.url'],os.path.join(CACHEDIR,str(video["videoID"])+".jpg")))
#            item=xbmcgui.ListItem(label=video["title"],label2=video["publication_date"],
#                                  iconImage=os.path.join(CACHEDIR,str(video["videoID"])+".jpg"),
#                                  thumbnailImage=os.path.join(CACHEDIR,str(video["videoID"])+".jpg"))
            item=xbmcgui.ListItem(label=video["title"],label2=video["publication_date"],
                                  iconImage=video['image.url'],
                                  thumbnailImage=video['image.url'])
    
            #menu contextuel
            label  = __language__( 30100 ) # Enregistrer (Haute Qualit�e)
            action = 'XBMC.RunScript(%s,%s,%s)'%(os.path.join(os.getcwd(), "resources", "libs", "FLVdownload.py"),
                                                 infos["video.hi"],
                                                 os.path.join(DOWNLOADDIR,xbmc.makeLegalFilename(os.path.basename(infos["video.hi"])))
                                                 )
            item.addContextMenuItems([ (
                __language__( 30100 ),
                'XBMC.RunScript(%s,%s,%s)'%(os.path.join(os.getcwd(), "resources", "libs","FLVdownload.py"),
                                            infos["video.hi"],
                                            os.path.join(DOWNLOADDIR,xbmc.makeLegalFilename(os.path.basename(infos["video.hi"])))
                                            ),
                                        ),(
                __language__( 30101 ),
                'XBMC.RunScript(%s,%s,%s)'%(os.path.join(os.getcwd(), "resources", "libs","FLVdownload.py"),
                                                 infos["video.low"],
                                                 os.path.join(DOWNLOADDIR,xbmc.makeLegalFilename(os.path.basename(infos["video.hi"])))
                                                 ),
                                        )
                ])
            #infos sur la video
            item.setInfo( type="Video",
                          infoLabels={ "Title": video["title"] + " " + video["publication_date"],
                                       "Rating":video["note"],
                                       "Date": video["publication_date"],
                                       "Plot": video["description"]})
            ok = ok and xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),
                                                    url=url,
                                                    listitem=item,
                                                    isFolder=False)
            pDialog.update(int(99*float(cpt)/(len(videos)*2)), "Chargement des �l�ments...")
        except:
            print "cplusplus - show_videos: error while retrieving videos list and info"
            traceback.print_exc()
        
        
    # TODO: on n'a plus besoin des threads pour telecharger les images que l'on laisse telecharger par le plugin lui meme desormaus    
    for i in xrange(NUM_THREADS):
        t = threading.Thread(target = getfiles)
        t.start()
    while threading.activeCount() > 1 or not q_out.empty():
        try:
            # on retire les r�sultats de la queue
            # on attend au plus 500 ms si la queue est vide
            # le timeout est n�cessaire pour �viter une race condition
            title,localpath = q_out.get(True, 0.5)
            pDialog.update(int( 99*float(cpt)/(len(videos)*2) ), title)
            cpt=cpt+1
        except Exception,msg:
            pass
            #ajout d'un �l�ment de navigation 'page suivante' si besoin
    pDialog.close()
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_NONE)
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=referer )
    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    return ok

def show_keyboard(theme_id,subtheme_id):
    """Display virtual keyboard"""
    kb = xbmc.Keyboard("", __language__( 30203 ), False) #Recherche sur Canal Plus Videos
    kb.doModal()
    if kb.isConfirmed():
        motcle = kb.getText()
        if ( len(motcle) > 2): # Taille mini pour une recherche
            show_videos(theme_id=theme_id,subtheme_id=subtheme_id,referer="Resultats pour '%s'"%motcle,keyword=motcle)
        else:
            dialogError = xbmcgui.Dialog()
            ok = dialogError.ok( __language__( 30204 ), __language__( 30205 ), __language__( 30206 ) )

def show_video_infos(videoid):
    """
    sera utilis� pour lire une video selon son id
    """
    ok = True

    infos = cpp.get_info(videoid)

    #TITRE
    item=xbmcgui.ListItem("Titre : %s"%infos["title"])
    ok = ok and xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),
                                            url="",
                                            listitem=item,
                                            isFolder=False)

    #RESUME
    item=xbmcgui.ListItem(u"R�sum� : %s"%infos["summary"])
    ok = ok and xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),
                                            url="",
                                            listitem=item,
                                            isFolder=False)

    #DATE
    item=xbmcgui.ListItem(u"Publi�e le %s"%infos["publication_date"])
    ok = ok and xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),
                                            url="",
                                            listitem=item,
                                            isFolder=False)

    #IMAGE (a faire)
    item=xbmcgui.ListItem(u"Obtenir l'image (A FAIRE)")#%infos["image.url"])#ou smallimage.url
    #item.setInfo("Image",{ "Url": infos["image.url"] } )
    cpp.Cache_Pic(infos['image.url'],
                  os.path.join(CACHEDIR,
                               xbmc.makeLegalFilename( os.path.basename( str(infos["image.url"]) ) )
                               ) )
    ok = ok and xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),
                                            url=sys.argv[0]+"?showpicture="+xbmc.makeLegalFilename( os.path.basename( str(infos["image.url"]) ) ),#infos["image.url"],
                                            listitem=item,
                                            isFolder=False)

    #LECTURE HI
    item=xbmcgui.ListItem(u"Voir la video (Haute Qualit�)")
    ok = ok and xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),
                                            url=infos["video.hi"],
                                            listitem=item,
                                            isFolder=False)

    #LECTURE LO
    item=xbmcgui.ListItem(u"Voir la video (Basse Qualit�)")
    ok = ok and xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),
                                            url=infos["video.low"],
                                            listitem=item,
                                            isFolder=False)

    #ENREGISTREMENT HI
    item=xbmcgui.ListItem(u"T�l�charger la video (Haute Qualit�)")
    ok = ok and xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),
                                            url=sys.argv[0]+"?dlvideo="+infos["video.hi"],
                                            listitem=item,
                                            isFolder=False)

    #ENREGISTREMENT LOW
    item=xbmcgui.ListItem(u"T�l�charger la video (Basse Qualit�)")
    ok = ok and xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),
                                            url=sys.argv[0]+"?dlvideo="+infos["video.low"],
                                            listitem=item,
                                            isFolder=False)

    path_img = os.path.join(CACHEDIR,
                               xbmc.makeLegalFilename( os.path.basename( str(infos["image.url"]) ) )
                               ) 
    fanart_color1 = ""
    fanart_color2 = ""
    fanart_color3 = ""
    xbmcplugin.setPluginFanart( handle=int( sys.argv[ 1 ] ), image=path_img, color1=fanart_color1, color2=fanart_color2, color3=fanart_color3 )
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_NONE)
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category= infos["title"])
    return ok


def show_dialog(titre,message,message2="",message3=""):
    dialog = xbmcgui.Dialog()
    dialog.ok(titre, message,message2,message3)
    return True

if ( __name__ == "__main__" ):

    try:
        cpp.CACHEDIR = CACHEDIR
        #Il faut parser les param�tres
        stringparams = sys.argv[2] #les param�tres sont sur le 3ieme argument pass� au script
        try:
            if stringparams[0]=="?":#pour enlever le ? si il est en d�but des param�tres
                stringparams=stringparams[1:]
        except:
            pass
        parametres={}
        for param in stringparams.split("&"):#on d�coupe les param�tres sur le '&'
            try:
                cle,valeur=param.split("=")#on s�pare les couples cl�/valeur
            except:
                cle=param
                valeur=""
            parametres[cle]=valeur #on rempli le dictionnaire des param�tres
        #voil�, 'parametres' contient les param�tres pars�s
        
        if "listethemes" in parametres.keys():
            #� priori non utilis� !
            #on liste les themes
            show_themes()
        elif "listesubthemes" in parametres.keys():
            #on liste les sous-themes
            show_subthemes(parametres["listesubthemes"],parametres["referer"])
        elif "listevideos" in parametres.keys():
            #on liste les videos
            theme_id,subtheme_id = parametres["listevideos"].split("#")
            show_videos(theme_id,subtheme_id,parametres["referer"])
        elif "showvideoinfos" in parametres.keys():
            #montre les infos de la video
            show_video_infos(parametres["showvideoinfos"])
        
        elif "dlvideo" in parametres.keys():
            xbmc.executebuiltin('XBMC.RunScript(%s,%s,%s)'%(os.path.join(os.getcwd(), "resources", "libs","FLVdownload.py"),
                                                            parametres["dlvideo"],
                                                            os.path.join(DOWNLOADDIR,xbmc.makeLegalFilename(os.path.basename(parametres["dlvideo"])))
                                                            ))
        elif "search" in parametres.keys():
            show_keyboard(parametres["theme_id"],parametres["subtheme_id"])
        #    #t�l�charge la vid�o selon l'url fournie
        #    pDialog = xbmcgui.DialogProgress()
        #    ret = pDialog.create('CanalPlus', 'D�marrage du t�l�chargement ...')
        #    #t�l�chargement par Thread : FONCTIONNE MAIS TRES MAL : pas convaincant
        #    goDL = cpp.DL_video(parametres["dlvideo"],
        #                        #xbmc.makeLegalFilename(os.path.join(DOWNLOADDIR,os.path.basename(parametres["dlvideo"]))),
        #                        os.path.join(DOWNLOADDIR,xbmc.makeLegalFilename(os.path.basename(parametres["dlvideo"]))),
        #                        pDialog.update,pDialog)
        #    pDialog.close()
        #    if goDL==1:
        #        xbmc.executebuiltin("XBMC.Notification(%s,%s)"%("Telechargement termine !",""))
        #    elif goDL == 0:
        #        xbmc.executebuiltin("XBMC.Notification(%s,%s)"%("Fichier existant !","Telechargement annule."))
        #    elif goDL == -1:
        #        xbmc.executebuiltin("XBMC.Notification(%s,%s)"%("Telechargement annule par l'utilisateur.",""))
        
        elif "showpicture" in parametres.keys():
            #ne fait rien
            print os.path.join(CACHEDIR,parametres["showpicture"])
        else:
            show_themes()
            
            # Verifions si les repertoire dans user data ont ete crees.
            for i in range( len( dirCheckList ) ):
                verifrep( dirCheckList[i] ) 
        
            #show_dialog("erreur","param�tre inconnu")
        
        xbmcplugin.endOfDirectory(int(sys.argv[1]))#il faut cloturer le plugin avec ca pour finaliser la liste
    
    except:
        print_exc()
    
