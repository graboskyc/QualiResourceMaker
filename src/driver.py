from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.shell.core.driver_context import InitCommandContext, ResourceCommandContext, AutoLoadCommandContext, AutoLoadAttribute, AutoLoadResource, AutoLoadDetails
from cloudshell.api.cloudshell_api import CloudShellAPISession
from cloudshell.api.cloudshell_api import ResourceAttributesUpdateRequest
from cloudshell.api.cloudshell_api import AttributeNamesValues
from cloudshell.api.cloudshell_api import AttributeNameValue
import cloudshell.helpers.scripts.cloudshell_scripts_helpers as helpers
import tornado.ioloop
import tornado.web
import tornado.websocket
import threading
import json
import os
import socket
import xml.etree.ElementTree as ET
import sys

class QSCreds():
    def __init__(self):
        self.Host = "localhost"
        self.Un = "admin"
        self.Pw = "admin"
        self.Dom = "Global"
        self.appWSHPort = 6661
        self.appMainPort = 6660

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        creds = QSCreds()
        csapi = CloudShellAPISession(creds.Host, creds.Un, creds.Pw, creds.Dom)
        fAM = csapi.ExportFamiliesAndModels()
        root = ET.fromstring(fAM.Configuration)
        ns = {"qs":"http://schemas.qualisystems.com/ResourceManagement/ExportImportConfigurationSchema.xsd"}
        famList = []
        modList = []
        attList = []
        for f in root.findall(".//qs:ResourceFamily", ns):
            famList.append(f.get("Name"))
        for m in root.findall(".//qs:ResourceModel", ns):
            modList.append(m.get("Name"))
        for a in root.findall(".//qs:AttributeInfo", ns):
            attList.append(a.get("Name"))
        self.render("index.html", title="Resource Maker", wsip="6661", possibleFamily=famList, possibleModel=modList, possibleAtts=attList)

class WebSocketHandler(tornado.websocket.WebSocketHandler):  
    def open(self):
        print "New client connected"
        self.write_message("CONN")

    def on_message(self, message):
        obj = json.loads(message)
        if obj["TASK"] == "CREATE":
            resName = obj["NAME"]
            famName = obj["FAM"]
            modName = obj["MOD"]
            addr = obj["ADDR"]
            desc = obj["DESC"]
            dom = obj["DOM"]

            if (len(resName) > 0):
                try:
                    creds = QSCreds()
                    csapi = CloudShellAPISession(creds.Host, creds.Un, creds.Pw, creds.Dom)
                    folder = ""
                    parent = ""
                    
                    csapi.CreateResource(famName, modName, resName, addr, folder, parent, desc)
                    csapi.AddResourcesToDomain(dom, [resName])
                    self.write_message("CREATED/"+message)
                except:
                    e = sys.exc_info()[0]
                    self.write_message("FAILED/EXCEPTION/"+str(e))
                    pass
            else:
                self.write_message("FAILED/CREATENAME")
        elif obj["TASK"] == "ATTR":
            resName = obj["NAME"]

            if (len(resName) > 0):
                try:
                    creds = QSCreds()
                    csapi = CloudShellAPISession(creds.Host, creds.Un, creds.Pw, creds.Dom)
                    allRaud = []
                    
                    for n,v in zip(obj["ATTS"], obj["VALS"]):
                        if (n != "XXXNAXXX"):
                            anv = AttributeNameValue(n,v)
                            anvs = AttributeNamesValues(anv)
                            raud = ResourceAttributesUpdateRequest(resName, anvs)
                            allRaud.append(raud)
                    	    csapi.SetAttributesValues(allRaud)
                    self.write_message("ATTR/"+message)
                except:
                    e = sys.exc_info()[0]
                    self.write_message("FAILED/EXCEPTION/"+str(e))
                    pass
            else:
                self.write_message("FAILED/ATTRNAME")
        elif obj["TASK"] == "SUB":
            rootName = obj["ROOT"]
            if (len(rootName) > 0):
                try:
                    creds = QSCreds()
                    csapi = CloudShellAPISession(creds.Host, creds.Un, creds.Pw, creds.Dom)

                    for f,m,n in zip(obj["SUBFAMS"], obj["SUBMODS"],  obj["SUBNAMES"]):
                        if (len(n) > 0):
                            csapi.CreateResource(f, m, n, n, "", rootName, "")
                    self.write_message("SUB/"+message)
                except:
                    e = sys.exc_info()[0]
                    self.write_message("FAILED/EXCEPTION/"+str(e))
                    pass
            else:
                self.write_message("FAILED/ROOTNAME")
        else:
            self.write_message("FAILED/UNKNOWN")

    # client disconnected
    def on_close(self):
        print "Client disconnected"
    
    def check_origin(self, origin):
		return True

class Runner():
    def __init__(self, printOutput=False):
        creds = QSCreds()
        appWSHPort = creds.appWSHPort
        appMainPort = creds.appMainPort

        # Start the websocket hander
        appWSH = tornado.web.Application([(r"/", WebSocketHandler),])
        appWSH.listen(appWSHPort)

        if printOutput:
            csapi = CloudShellAPISession(creds.Host, creds.Un, creds.Pw, creds.Dom)
            csapi.WriteMessageToReservationOutput(context.reservation.reservation_id, "Head to: http://" +socket.gethostbyname(socket.gethostname())+":"+str(appMainPort))

        # start main app
        settings = {"static_path": os.path.join(os.path.dirname(__file__), "static")}
        appMain = tornado.web.Application([(r"/", MainHandler),], **settings)
        appMain.listen(appMainPort)
        tornado.ioloop.IOLoop.current().start()

class ResourcemakerDriver (ResourceDriverInterface):

    def __init__(self):
        """
        ctor must be without arguments, it is created with reflection at run time
        """
        pass

    def initialize(self, context):
        """
        Initialize the driver session, this function is called everytime a new instance of the driver is created
        This is a good place to load and cache the driver configuration, initiate sessions etc.
        :param InitCommandContext context: the context the command runs on
        """
        pass

    def RunResourceMaker(self, context, cancellation_context):
        r = Runner(True)
        pass


    def cleanup(self):
        """
        Destroy the driver session, this function is called everytime a driver instance is destroyed
        This is a good place to close any open sessions, finish writing to log files
        """
        pass

if __name__ == "__main__":
    r = Runner()
