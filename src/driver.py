from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.shell.core.driver_context import InitCommandContext, ResourceCommandContext, AutoLoadCommandContext, AutoLoadAttribute, AutoLoadResource, AutoLoadDetails
from cloudshell.api.cloudshell_api import CloudShellAPISession
import cloudshell.helpers.scripts.cloudshell_scripts_helpers as helpers
import tornado.ioloop
import tornado.web
import tornado.websocket
import threading
import json
import os
import socket
import xml.etree.ElementTree as ET

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        csapi = CloudShellAPISession("localhost","admin","admin","Global")
        fAM = csapi.ExportFamiliesAndModels()
        root = ET.fromstring(fAM.Configuration)
        ns = {"qs":"http://schemas.qualisystems.com/ResourceManagement/ExportImportConfigurationSchema.xsd"}
        famList = []
        modList = []
        for f in root.findall(".//qs:ResourceFamily", ns):
            famList.append(f.get("Name"))
        for m in root.findall(".//qs:ResourceModel", ns):
            modList.append(m.get("Name"))
        self.render("index.html", title="Resource Maker", wsip=socket.gethostbyname(socket.gethostname())+":6661", possibleFamily=famList, possibleModel=modList)

class WebSocketHandler(tornado.websocket.WebSocketHandler):  
    def open(self):
        print "New client connected"
        self.write_message("CONN")

    def on_message(self, message):
        if message.startswith("CREATE"):
            userPacket = message.split("/")

            if (len(userPacket) == 6):
                resName = userPacket[1]
                famName = userPacket[2]
                modName = userPacket[3]
                addr = userPacket[4]
                desc = userPacket[5]

                if (len(resName) > 0):
                    try:
                        csapi = CloudShellAPISession("localhost","admin","admin","Global")
                        csapi.CreateResource(famName, modName, resName, addr, "", "", desc)
                        self.write_message("CREATED/"+message)
                    except:
                        self.write_message("FAILED/EXCEPTION")
                        pass
                else:
                    self.write_message("FAILED/CREATENAME")
            else:
                self.write_message("FAILED/CREATEARGS")
        else:
            self.write_message("FAILED/UNKNOWN")

    # client disconnected
    def on_close(self):
        print "Client disconnected"
    
    def check_origin(self, origin):
		return True

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

        appWSHPort = 6661
        appMainPort = 6660

        # Start the websocket hander
        appWSH = tornado.web.Application([(r"/", WebSocketHandler),])
        appWSH.listen(appWSHPort)

        csapi = CloudShellAPISession("localhost","admin","admin","Global")
        csapi.WriteMessageToReservationOutput(context.reservation.reservation_id, "Head to: http://" +socket.gethostbyname(socket.gethostname())+":"+str(appMainPort))

        # start main app
        settings = {"static_path": os.path.join(os.path.dirname(__file__), "static")}
        appMain = tornado.web.Application([(r"/", MainHandler),], **settings)
        appMain.listen(appMainPort)
        tornado.ioloop.IOLoop.current().start()

        pass

    def example_function_with_params(self, context, user_param1, user_param2):
        """
        An example function that accepts two user parameters
        :param ResourceCommandContext context: the context the command runs on
        :param str user_param1: A user parameter
        :param str user_param2: A user parameter
        """
        pass


    def cleanup(self):
        """
        Destroy the driver session, this function is called everytime a driver instance is destroyed
        This is a good place to close any open sessions, finish writing to log files
        """
        pass