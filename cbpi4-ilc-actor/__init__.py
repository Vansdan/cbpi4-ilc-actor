import os
from aiohttp import web
import logging
import asyncio
from cbpi.api import *

import requests
from requests.auth import HTTPBasicAuth
import time

logger = logging.getLogger(__name__)

@parameters([
    Property.Text(label="IP ILC", configurable=True, description="IP Adress of ILC SPS (example: 192.168.1.150)", default_value="192.168.1.151"),
    Property.Text(label="Actor Variable", configurable=True, description="Actor Variable in SPS", default_value="CBPI4.ILC_Actor"),
    #Property.Text(label="Actor Variable - Get", configurable=True, description="Actor Variable in SPS", default_value="MAISCHEN.RPBI_HZG"),
    ])
class CustomActor(CBPiActor):

    @action("action", parameters={})
    async def action(self, **kwargs):
        print("Action Triggered", kwargs)
        pass
    
    def on_start(self):
        self.state = False
        pass

    async def on(self, power=0):
        logger.info("ACTOR 1111 %s ON" % self.id)
        self.state = True
        
            #ip_ilc = self.props.get("IP ILC")
            #variable_ilc = self.props.get("Actor Variable")            
            #url = "http://" + ip_ilc + "/cgi-bin/writeVal.exe?" + variable_ilc + "+" + "1"

        
        

    async def off(self):
        logger.info("ACTOR %s OFF " % self.id)
        self.state = False

    def get_state(self):
        return self.state
    
    async def run(self):
        pass

def setup(cbpi):
    cbpi.plugin.register("ILC Actor", CustomActor)
    pass
