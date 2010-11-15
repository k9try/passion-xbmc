"""
ItemInstaller: this module allows download and install an item from Passion XBMC download center
"""

# Modules general
import os
import sys
import httplib
import urllib2
from traceback import print_exc
import urllib
import re


# Modules XBMC
import xbmc
import xbmcgui

# Modules custom
from utilities import *
try:
    from ItemInstaller import ArchItemInstaller, DirItemInstaller, cancelRequest
    from Item import *
except:
    print_exc()

httplib.HTTPConnection.debuglevel = 1

#FONCTION POUR RECUPERER LES LABELS DE LA LANGUE.
_ = sys.modules[ "__main__" ].__language__


class Parser:
    """ Parser Class: grabs all tag versions and urls """
    # regexpressions
    revision_regex = re.compile( '<h2>.+?Revision ([0-9]*): ([^<]*)</h2>' )
    asset_regex = re.compile( '<li><a href="([^"]*)">([^"]*)</a></li>' )

    def __init__( self, htmlSource ):
        # set our initial status
        self.dict = { "status": "fail", "revision": 0, "assets": [], "url": "" }
        # fetch revision number
        self._fetch_revision( htmlSource )
        # if we were successful, fetch assets
        if ( self.dict[ "revision" ] != 0 ):
            self._fetch_assets( htmlSource )

    def _fetch_revision( self, htmlSource ):
        try:
            # parse revision and current dir level
            revision, url = self.revision_regex.findall( htmlSource )[ 0 ]
            # we succeeded :), set our info
            urlParts = url.split( "/" )
            baseUrl = urlParts[len(urlParts)-1]
            self.dict[ "url" ] = baseUrl
            self.dict[ "revision" ] = int( revision )
        except:
            pass

    def _fetch_assets( self, htmlSource ):
        try:
            assets = self.asset_regex.findall( htmlSource )
            if ( len( assets ) ):
                for asset in assets:
                    if ( asset[ 0 ] != "../" ):
                        self.dict[ "assets" ] += [ unescape( asset[ 0 ] ) ]
                self.dict[ "status" ] = "ok"
            print self.dict[ "assets" ]
        except:
            pass


class RemoteArchiveInstaller(ArchItemInstaller):
    """
    Download an zip addons and install it
    """

    def __init__( self , name, url ):
        ArchItemInstaller.__init__( self )

        self.itemInfo [ "name" ] = name
        #self.itemInfo [ "name" ] = unicode( name, 'ISO 8859-1', errors='ignore')
        
        self.itemInfo [ "url" ] = url
        self.itemInfo [ "filename" ] = os.path.basename(url)
        self.itemInfo [ "filesize" ] = 0
        self.itemInfo [ "raw_item_sys_type" ] = TYPE_SYSTEM_ARCHIVE
        print self.itemInfo
        #TODO: support progress bar display

    def GetRawItem( self, msgFunc=None,progressBar=None ):
        """
        Download an item from the server
        Returns the status of the download attempts : OK | ERROR
        """
        # Get ItemId
        percent = 0
        status = "OK"
        
        if progressBar != None:
            #progressBar.update( percent, unicode(_( 122 )) % ( self.itemInfo [ "name" ] ), unicode(_( 123 )) % percent )
            progressBar.update( percent, ( self.itemInfo [ "name" ] ), _( 123 ) % percent )
            #print _( 122 )
            #print self.itemInfo[ "name" ]
            #from types import *
            #print type(self.itemInfo[ "name" ])
            #print unicode(self.itemInfo[ "name" ], errors='ignore')
            #print _( 122 )%ustr
        try:            
            print "HTTPInstaller::GetRawItem "
            # Download file (to cache dir) and get destination directory
            status, self.itemInfo [ "raw_item_path" ] = self._downloadFile( progressBar=progressBar )
        
        except Exception, e:
            print "Exception during downlaodItem"
            print e
            print_exc()
            self.itemInfo [ "raw_item_path" ] = None
            status = "ERROR"
        if progressBar != None:
            progressBar.update( percent, ( self.itemInfo [ "name" ] ), _( 134 ) )
        #return status, self.itemInfo [ "raw_item_path" ]
        return status



    def getFileSize(self, sourceurl):
        """
        get the size of the file (in octets)
        !!!ISSUE!!!: +1 on nb of download just calling this method with Passion-XBMC URL
        """
        file_size = 0
        try:
            connection  = urllib2.urlopen(sourceurl)
            headers     = connection.info()
            file_size   = int( headers['Content-Length'] )
            connection.close()
        except Exception, e:
            print "Exception during getFileSize"
            print e
            print sys.exc_info()
            print_exc()
        return file_size

    def _downloadFile(self, progressBar=None):
        """
        Download a file at a specific URL and send event to registerd UI if requested
        Returns the status of the download attempt : OK | ERROR
        """
        destinationDir = self.CACHEDIR
        print("_downloadFile with url = " + self.itemInfo [ "url" ])
        print("_downloadFile with destination directory = " + destinationDir)
        destination = None
        status     = "OK" # Status of download :[OK | ERROR | CANCELED | ERRORFILENAME]
        
        try:
            # -- Downloading
            print("_downloadFile - Trying to retrieve the file")
            block_size          = 8192
            percent_downloaded  = 0
            num_blocks          = 0
            
            req = urllib2.Request(self.itemInfo [ "url" ]) # Note: downloading item with passion XBMC URL (for download count) even when there is an external URL
            req.add_header('User-Agent','Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.3) Gecko/20070309 Firefox/2.0.0.3')
            connection  = urllib2.urlopen(req)           # Open connection
            if self.itemInfo [ "filename" ] == '' or self.itemInfo [ "filesize" ] <= 0:
                # Try to retrieve file name / file size
                try:
                    headers = connection.info()# Get Headers
                    print "_downloadFile: headers:"
                    print headers
                    print "---"
                    if self.itemInfo [ "filename" ] == '':
                        try:
                            if 'Content-Disposition' in headers:
                                content_disposition =  headers['Content-Disposition']
                                if "\"" in content_disposition:
                                    self.itemInfo [ "filename" ] = headers['Content-Disposition'].split('"')[1]
                                else:
                                    self.itemInfo [ "filename" ] = headers['Content-Disposition'].split('=')[1]
                                    
                            if self.itemInfo [ "filename" ] == '':
                                # It wasn't possible to read filename within the headers
                                realURL = connection.geturl().encode('utf-8') # Get URL (possible redirection)
                                print realURL
                                if self.itemInfo [ "url" ] != realURL:
                                    # Redirection
                                    print "redirect url = %s"%realURL
                                    self.itemInfo [ "filename" ] = os.path.basename(realURL)
                                    if not self.itemInfo [ "filename" ].lower().endswith('zip') and not self.itemInfo [ "filename" ].lower().endswith('rar'):
                                        self.itemInfo [ "filename" ] = "unknownfilename"
                                        status = "ERRORFILENAME"
                                else:
                                    self.itemInfo [ "filename" ] = "unknownfilename"
                                    status = "ERRORFILENAME"
                        except:
                            self.itemInfo [ "filename" ] = "unknownfilename"
                            status = "ERRORFILENAME"
                            print_exc()
                    #if self.itemInfo [ "filesize" ] <= 0:
                    try:
                        self.itemInfo [ "filesize" ] = int( headers['Content-Length'] )
                    except:
                        pass

                except Exception, e:
                    self.itemInfo [ "filename" ] = "unknownfilename"
                    status = "ERRORFILENAME"
                    self.itemInfo [ "filesize" ] = 0
                    print("_downloadFile - Exception retrieving header")
                    print(str(e))
                    print_exc()

            
            destination = xbmc.translatePath( os.path.join( destinationDir, self.itemInfo [ "filename" ] ) )
            print "_downloadFile - file name : %s "%self.itemInfo [ "filename" ]
            print "_downloadFile - file size : %d Octet(s)"%self.itemInfo [ "filesize" ]
            print "_downloadFile: destination %s"%destination
            


            file = open(destination,'w+b')        # Get ready for writing file
            print "_downloadFile: File opened"
            # Ask for display of progress bar
            try:
                if (progressBar != None):
                    #progressBar.update(percent_downloaded)
                    progressBar.update( percent_downloaded, _( 122 ) % ( self.itemInfo [ "name" ] ), _( 123 ) % percent_downloaded )
            except Exception, e:        
                print("_downloadFile - Exception calling UI callback for download")
                print(str(e))
                print progressBar
                
            ###########
            # Download
            ###########
            print "_downloadFile: Starting download"
            while 1:
                if (progressBar != None):
                    if progressBar.iscanceled():
                        print "_downloadFile: Downloaded STOPPED by the user"
                        status = "CANCELED"
                        break
                try:
                    cur_block  = connection.read(block_size)
                    if not cur_block:
                        break
                    file.write(cur_block)
                    # Increment for next block
                    num_blocks = num_blocks + 1
                except Exception, e:        
                    print("_downloadFile - Exception during reading of the remote file and writing it locally")
                    print(str(e))
                    print ("_downloadFile: error during reading of the remote file and writing it locally: " + str(sys.exc_info()[0]))
                    print_exc()
                    status = "ERROR"
                try:
                    # Compute percent of download in progress
                    New_percent_downloaded = min((num_blocks*block_size*100)/self.itemInfo [ "filesize" ], 100)
                    #print "_downloadFile - Percent = %d"%New_percent_downloaded
                except Exception, e:        
                    print("_downloadFile - Exception computing percentage downloaded")
                    print(str(e))
                    New_percent_downloaded = 0
                # We send an update only when percent number increases
                if (New_percent_downloaded > percent_downloaded):
                    percent_downloaded = New_percent_downloaded
                    # Call UI callback in order to update download progress info
                    if (progressBar != None):
                        #progressBar.update(percent_downloaded)
                        progressBar.update( percent_downloaded, _( 122 ) % ( self.itemInfo [ "name" ] ), _( 123 ) % percent_downloaded )


            # Closing the file
            file.close()
            # End of writing: Closing the connection and the file
            connection.close()
        except Exception, e:
            status = "ERROR"
            print("_downloadFile: Exception while source retrieving")
            print(str(e))
            print ("_downloadFile: error while source retrieving: " + str(sys.exc_info()[0]))
            print_exc()
            print("_downloadFile ENDED with ERROR")

#            # Prepare message to the UI
#            msgType = "Error"
#            msgTite = _ ( 144 )
#            msg1    = file_name
#            msg2    = ""
#            msg3    = ""

        print "_downloadFile: status of download"
        print status
        print destination
        print("_downloadFile ENDED")
                
        return status, destination
        
class RemoteDirInstaller(DirItemInstaller):
    """
    Download an directory and its content and install it
    """

    def __init__( self , name, url, repoUrl ):
        DirItemInstaller.__init__( self )

        self.itemInfo [ "name" ] = name
        #self.itemInfo [ "name" ] = unicode( name, 'ISO 8859-1', errors='ignore')
        
        self.itemInfo [ "url" ] = url
        self.itemInfo [ "raw_item_sys_type" ] = TYPE_SYSTEM_DIRECTORY
        
        self._create_title()
        self.REPO_URL = repoUrl
        print self.itemInfo
        
        #TODO: pass progress bar callback instead
        self.dialog = xbmcgui.DialogProgress()

    def GetRawItem( self, msgFunc=None,progressBar=None ):
        """
        Download an item from the server
        Returns the status of the download attempts : OK | ERROR
        """
        # Get ItemId
        percent = 0
        status = "OK"
        
        if progressBar != None:
            #progressBar.update( percent, unicode(_( 122 )) % ( self.itemInfo [ "name" ] ), unicode(_( 123 )) % percent )
            progressBar.update( percent, ( self.itemInfo [ "name" ] ), _( 123 ) % percent )
        try:            
            print "HTTPInstaller::GetRawItem "
            # Download file (to cache dir) and get destination directory
            #status, self.itemInfo [ "raw_item_path" ] = self._downloadFile( progressBar=progressBar )
            status, self.itemInfo [ "raw_item_path" ] = self._download_item( )
        
        except Exception, e:
            print "Exception during downlaodItem"
            print e
            print_exc()
            self.itemInfo [ "raw_item_path" ] = None
            status = "ERROR"
        if progressBar != None:
            progressBar.update( percent, ( self.itemInfo [ "name" ] ), _( 134 ) )
        #return status, self.itemInfo [ "raw_item_path" ]
        return status

    def _create_title( self ):
        # create the script/plugin/skin title
        #parts = self.itemInfo[ "url" ].split( "/" )
        #version = ""
        #self.title = parts[ -2 ].replace( "%20", " " ) + version
        
        self.title = self.itemInfo [ "name" ]

    def _download_item( self, forceInstall=False ):
        print("> _download_item() forceInstall=%s" % forceInstall)
        status = "OK"
        finished_path = None
        try:
            #if ( forceInstall or xbmcgui.Dialog().yesno( self.title, _( 30050 ), "", "", _( 30020 ), _( 30021 ) ) ):
            if ( forceInstall or xbmcgui.Dialog().yesno( self.title, _( 30050 ), "", "" ) ):
                self.dialog.create( self.title, _( 30052 ), _( 30053 ) )
                asset_files = []
                folders = [ self.itemInfo[ "url" ].replace(self.REPO_URL + "/", "").replace( " ", "%20" ) ]
                while folders:
                    try:
                        htmlsource = readURL( self.REPO_URL + "/" + folders[ 0 ] )
                        if ( not htmlsource ): raise
                        items = self._parse_html_source( htmlsource )
                        if ( not items or items[ "status" ] == "fail" ): raise
                        files, dirs = self._parse_items( items )
                        print files
                        print dirs
                        for file in files:
                            print "Item url = %s"%items[ "url" ]
                            print " file = %s"%file
                            #asset_files.append( "%s/%s" % ( items[ "url" ], file, ) )
                            asset_files.append( folders[ 0 ] + "/" +  file )
                            
                        for folder in dirs:
                            folders.append( folders[ 0 ] + "/" + folder )
                        print "_download_item - folders BEFORE:"
                        print folders
                        folders = folders[ 1 : ]
                        print "_download_item - asset_files:"
                        print asset_files
                        print "_download_item - folders AFTER:"
                        print folders
                    except:
                        folders = []
                print 'folders'
                print folders
                print 'asset_files'
                print asset_files
                finished_path = self._get_files( asset_files )
                self.dialog.close()
                #if finished_path and not forceInstall:
                #    xbmcgui.Dialog().ok( self.title, _( 30058 ), finished_path )
                    # force list refresh
                    # xbmc.executebuiltin('Container.Refresh')
        except:
            # oops print error message
            print "ERROR: %s::%s (%d) - %s" % ( self.__class__.__name__, sys.exc_info()[ 2 ].tb_frame.f_code.co_name, sys.exc_info()[ 2 ].tb_lineno, sys.exc_info()[ 1 ], )
            self.dialog.close()
            #xbmcgui.Dialog().ok( self.title, _( 30090 ) )
            status = "ERROR"
        return status, finished_path
        
    def _get_files( self, asset_files ):
        """ fetch the files """
        try:
            finished_path = ""
            for cnt, url in enumerate( asset_files ):
                #items = os.path.split( url )
                #print "items"
                #print items
                # base path
                #drive = xbmc.translatePath( "/".join( [ "special://home", self.args.install ] ) )
                drive = self.CACHEDIR
                print "drive = %s"%drive
                # create the script/plugin/skin title
                #parts = items[ 0 ].split( "/" )
                #print parts
                version = ""
                # path = os.path.join( drive, os.path.sep.join( parts[ self.args.ioffset : ] ).replace( "%20", " " ) )
                #path = os.path.join( drive, parts[ len(parts)-1 ].replace( "%20", " " ) )
                path = os.path.dirname( xbmc.translatePath( os.path.join( drive, url.replace( "%20", " " ) ) ) )
                print "path = %s"%path
                if ( not finished_path ): finished_path = path
                #file = items[ 1 ].replace( "%20", " " )
                file = os.path.basename(url).replace( "%20", " " )
                pct = int( ( float( cnt ) / len( asset_files ) ) * 100 )
                self.dialog.update( pct, "%s %s" % ( _( 30055 ), url, ), "%s %s" % ( _( 30056 ), path, ), "%s %s" % ( _( 30007 ), file, ) )
                if ( self.dialog.iscanceled() ): raise
                if ( not os.path.isdir( path ) ): os.makedirs( path )
                url = self.REPO_URL + "/" + url.replace( " ", "%20" )
                fpath = os.path.join( path, file )
                
                print self.REPO_URL
                print fpath
                print url
                
                urllib.urlretrieve( url, fpath )
        except:
            finished_path = ""
            # oops print error message
            print "ERROR: %s::%s (%d) - %s" % ( self.__class__.__name__, sys.exc_info()[ 2 ].tb_frame.f_code.co_name, sys.exc_info()[ 2 ].tb_lineno, sys.exc_info()[ 1 ], )
            print_exc()
            raise

        return finished_path
            
    def _parse_html_source( self, htmlsource ):
        """ parse html source for tagged version and url """
        try:
            parser = Parser( htmlsource )
            print parser.dict
            return parser.dict
        except:
            return {}
            
    def _parse_items( self, items ):
        """ separates files and folders """
        folders = []
        files = []
        for item in items[ "assets" ]:
            if ( item.endswith( "/" ) ):
                folders.append( item )
            else:
                files.append( item )
        return files, folders
