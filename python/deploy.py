import os
import sys
import urllib
from urllib import urlopen
import zipfile

#import SimpleHTTPServer
#import BaseHTTPServer
#import CGIHTTPServer

def Download(url, path, name):
	if not os.path.exists(path):
		print "Creating path " + path
		os.makedirs(path)

	print "Download %s => %s" % (url, os.path.join(path,name))

	u = urlopen(url)
	f = open(os.path.join(path,name),"wb")
	f.write(u.read())
	f.close()


def Extract(src,dst):

	path = os.path.dirname(dst)
	if not os.path.exists(path):
		print "Creating path " + path
		os.makedirs(path)

	if not os.path.exists(src) or not zipfile.is_zipfile(src):
		print "Failed to extract " + src
		return

	print "Extract %s => %s" %(src,dst)
	
	zf = zipfile.ZipFile(src)
	zf.extractall(dst)


def Copy(src,dst):

	path = os.path.dirname(dst)
	if not os.path.exists(path):
		print "Creating path " + path
		os.makedirs(path)

	print "Copy %s => %s" %(src,dst)

	s = open(src,"rb")
	d = open(dst,"wb")
	d.write(s.read())
	d.close()
	s.close()


# There are two stages to the packaging.
# If we just want to install the Runtime and RVM then all we need to do is download and extract them to
# correct locations.  
# If we actually want to do a full locally hosted deployment where we control the Runtime and RVM update 
# process through a webserver then we can do that to.
# The RVM uses text files on the webserver to manage version information and redirect to extension less
# compressed zip files of both itself and the Runtime.


def Deploy(folder, version, host, port):

	def DeployRuntime(debug=False):

		print "Deploying OpenFin Runtime"

		runtime = os.path.join(folder,"release/runtime/")

		print "Downloading Runtime resources"

		# First we download the file which contains all the release version aliases.
		Download("http://developer.openfin.co/release/runtime/releaseChannels",runtime,"releaseChannels")
		
		# Then we may wish to save specific aliases like "latest" or "v35"
		Download("http://developer.openfin.co/release/runtime/latest",runtime,"latest")
		Download("http://developer.openfin.co/release/runtime/v35",runtime,"v35")

		# Finally we download the actual compressed binaries (these are just zip files without extension)
		try:
			Download("http://developer.openfin.co/release/runtime/" + version,runtime,version)
		except:
			print "Failed to download runtime version " + version


	def DeployRVM(debug=False):

		print "Deploying OpenFin RVM"

		# The debug/staging RVM path is "release/rvm/staging"
		rvm = "release/rvm/staging/" if debug else "release/rvm/"
		rvm = os.path.join(folder,rvm)

		Download("http://developer.openfin.co/release/rvm/latest/",rvm,"latest")
		Download("http://developer.openfin.co/release/rvm/latestVersion",rvm,"latestVersion")

		# Now we should extract the RVM to the folder specified and create a config if
		# required.  These steps will be repeated during installation.
		latest = os.path.join(rvm,"latest")

		print "Extracting RVM latest version"
		Extract(latest,folder)

		# Now write an RVM config file that will specify our deployment.  We can later copy
		# this to the install directory.

		root = "http://%s:%s/%s" % (host,port,os.path.basename(folder))

		json = """
			{
				"rootUrl": "%s/",
				"dlEncryptedRootUrl": "%s/services/s/",
				"dlRootUrl": "%s/"
			}
			""" % (root,root,root)

		print "Creating RVM config " + os.path.join(folder,"rvm.json")

		f = open(os.path.join(folder,"rvm.json"),"wb")
		f.write(json)
		f.close()


	DeployRuntime()
	DeployRVM()


def Install(folder,version):

	def InstallRuntime(path,debug=False):

		print "Installing OpenFin Runtime"

		# We need to extract the Runtime that was previously downloaded for the deployment

		runtime = os.path.join(folder,"release/runtime/" + version)

		# The runtime is installed into the users local folder, for example %LOCALAPPDATA%\OpenFin\runtime
		# under a subfolder with its version number.
		path = os.path.join(path,"runtime/%s/" % version)

		print "Extracting Runtime to OpenFin installation folder"
		Extract(runtime,path)


	def InstallRVM(path,debug=False):

		print "Installing OpenFin RVM"

		rvm = os.path.join(folder,"OpenFinRVM.exe")

		# We should have run the deployment stage and extracted the RVM already
		if not os.path.exists(rvm):
			print "RVM not found at " + rvm
			return

		print "Copying RVM to OpenFin installation folder"
		Copy(rvm,os.path.join(path,"OpenFinRVM.exe"))


	# Get the environment variables for various target systems where we will installe the Runtime and RVM
	# are installed.

	if os.environ.get("LOCALAPPDATA"):
		# Windows 7/8
		path = os.path.join(os.environ["LOCALAPPDATA"],"OpenFin")
	else:
		# Windows XP uses a different location to Windows 7/8
		path = os.path.join(os.environ["USERNAME"],"Local Settings\Application Data\OpenFin")


	InstallRuntime(path)
	InstallRVM(path)



def Application(folder,host,port):

	print "Installing App"

	# This is an example of how to create an installer for a locally hosted app with a locally deployed
	# Runtime and RVM hosted on the same webserver.  The installer service just creates a zipped installer
	# with the appropriate command line parameters.

	# We just want the basename part of the folder, i.e. relative to web root.
	root = "http://%s:%s/%s" % (host,port,os.path.basename(folder))

	installer = "https://dl.openfin.co/services/download?fileName=app-installer&config=%s/app.json&rvmConfig=%s/rvm.json" % (root,root)

	print "Downloading app installer from OpenFin web service " + installer

	Download(installer,folder,"app-installer.zip")

	json = """
		{
		  "devtools_port" : 9090,
		  "websocket_port" : 9696,
		  "startup_app": {
		    "name": "OpenFin App",
		    "url": "http://demoappdirectory.openf.in/desktop/config/apps/OpenFin/HelloOpenFin/index.html",
		    "uuid": "OpenFinHelloWorld",
		    "applicationIcon": "http://demoappdirectory.openf.in/desktop/config/apps/OpenFin/HelloOpenFin/img/openfin.ico",
		    "autoShow": false,
		    "defaultHeight": 525,
		    "defaultWidth": 395,
		    "resizable" : false,
		    "maximizable" : false,
		    "frame": false,
		    "cornerRounding" : {
		        "width" : 5,
		        "height" : 5
		    }
		  },
		  "runtime": {
		    "arguments": "",
			"version":"3.0.1.5"
		  },
		  "shortcut": {
		    "company": "OpenFin",
		    "description": "OpenFin App",
		    "icon": "http://demoappdirectory.openf.in/desktop/config/apps/OpenFin/HelloOpenFin/img/openfin.ico",
		    "name": "OpenFin App"
		  }
		}"""

	print "Creating App config " + os.path.join(folder,"app.json")

	f = open(os.path.join(folder,"app.json"),"wb")
	f.write(json)
	f.close()	



def Webserver(port):

	# Or alternatively from the command line you can just do this
	# $ python -m SimpleHTTPServer
	# Serving HTTP on 0.0.0.0 port 8000 ...
	http = BaseHTTPServer.HTTPServer(("0.0.0.0",port),CGIHTTPServer.CGIHTTPRequestHandler)
	http.serve_forever()



if __name__ == "__main__":


	host = "localhost"
	port = 8000
	cwd = os.getcwd()

	folder = os.path.join(cwd,"deploy")
	version = "3.0.1.5"

	Deploy(folder,version,host,port)
	Install(folder,version)
	


	# Create sample application and installer for it
	Application(folder,host,port)

	# Run an example webserver at the current location (which should be the root of the deployment)
	#Webserver(port)



