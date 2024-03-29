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
    Property.Text(label="IP ILC", configurable=True, description="IP Adress of ILC SPS (example: 192.168.1.150)",
                  default_value="192.168.1.151"),
    Property.Text(label="Actor Variable", configurable=True, description="Actor Variable in SPS",
                  default_value="CBPI4.ILC_Actor"),
    Property.Text(label="Read Variable", configurable=True, description="Read Variable in SPS",
                  default_value="CBPI4.ILC_Actor"),
    Property.Select(label="ActorType",options=["Taster","Schalter"],description="Select type for actor"),
    Property.Number(label="Request Timeout", configurable=True,
                    description="HTTP request timeout in seconds (default 5)", default_value=5),
    Property.Select(label="Continuous Mode", options=['YES', 'NO'],
                    description="Enable this if the remote url should be refreshed periodically even if our local actor state hasn't changed"),
    Property.Number(label="Continuous Interval", configurable=True,
                    description="Refresh interval in seconds used in continuous mode")
])
class ILCActor(CBPiActor):

    @action("Toggle on off once with 5 second pause", parameters={})
    async def action(self, **kwargs):
        logger.info("Action triggered %s los" % kwargs)
        self.on()
        await asyncio.sleep(5)
        self.off()
        logger.info("Action triggered %s ende" % kwargs)
        pass

    #Startparameter---------------------------------------------------------------------------------------------------

    def __init__(self, cbpi, id, props):
        super().__init__(cbpi, id, props)
        self.state = False
        self.continuous_task = None

        self.request_session = requests.Session()
        self.request_session.verify = False
        
        if self.props.get("Continuous Mode", "NO") == "YES":
            self.continuous_mode = True
        else:
            self.continuous_mode = False
        
        #http://192.168.1.152/cgi-bin/writeVal.exe?WOHNEN.WOH_LICHT_COUCHV+1
        
        self.variable_ilc = self.props.get("Actor Variable")
        self.variable_ilc_read = self.props.get("Read Variable")       
        self.ip_ilc = self.props.get("IP ILC")
        
        self.url_on = "http://" + self.ip_ilc + "/cgi-bin/writeVal.exe?" + self.variable_ilc + "+" + "1"
        self.url_off = "http://" + self.ip_ilc + "/cgi-bin/writeVal.exe?" + self.variable_ilc + "+" + "0"
        
        #url = "http://" + ip_ilc + "/cgi-bin/readVal.exe?" + variable_ilc
        self.url_read = "http://" + self.ip_ilc + "/cgi-bin/readVal.exe?" + self.variable_ilc_read

        self.payload_on = None
        self.payload_off = None
        self.basic_auth = None
        self.continuous_interval = float(self.props.get("Continuous Interval", 5))
        self.request_session.timeout = float(self.props.get("Request Timeout", 5))
        self.req_type = "read"
        self.stat_actor =""
        self.actor_type = self.props.get("ActorType","Taster")
        
        pass

    #Funktion set continous state-----------------------------------------------------------------------------------

    async def set_continuous_state(self):
        logger.info('Starting continuous state setter background task interval=%s'% self.continuous_interval)
        while True:
            start_time = int(time.time())
            try:
                await self.start_request(self.req_type)
            except Exception as e:
                logger.error("Unknown exception: %s" % e)
            
            wait_time = start_time + self.continous_interval - int(time.time())
            if wait_time < 0:
                logger.warn("Continuous interval kann nicht gehalten werden, da zu klein und requests brauchen zu lange")
            else:
                await asyncio.sleep(wait_time)

        pass

    #Funktion starte Request---------------------------------------------------------------------------------------
    
    async def start_request(self, req_type):
        if req_type == "ein":
            url = self.url_on
            payload = self.payload_on
        if req_type == "aus":
            url = self.url_off
            payload = self.payload_off
        if req_type == "read":
            url = self.url_read
            payload = self.payload_off
        logger.info("ILCActor type=request_start onoff=%s url=\"%s\"" % (req_type, url))

        response = self.request_session.get(url, data=payload, auth=self.basic_auth)
        self.stat_actor = response.text
        
        logger.info("ILCActor type=request_done onoff=%s url=\"%s\" http_statuscode=%s response_text=\"%s\"" % (req_type, url, response.status_code, response.text.replace('"', '\\"')))

    #Funktion on---------------------------------------------------------------------------------------------------

    async def on(self, power=0):
        logger.debug("Actor %s ON" % self.id)
        self.state = True
        if self.actor_type == "Taster":
            await self.start_request("ein")
            await asyncio.sleep(0.5)
            await self.start_request("aus")
        else:
            await self.start_request("ein")
        
    #Funktion off--------------------------------------------------------------------------------------------------

    async def off(self):
        logger.debug("Actor %s OFF" % self.id)
        self.state = False
        if self.actor_type == "Taster":
            await self.start_request("ein")
            await asyncio.sleep(0.5)
            await self.start_request("aus")
        else:
            await self.start_request("aus")
            
    #Funktion get_state--------------------------------------------------------------------------------------------

    def get_state(self):
        return self.state

    #Funktion start------------------------------------------------------------------------------------------------

    async def start(self):
        pass

    #Funktion stop-------------------------------------------------------------------------------------------------

    #async def stop(self):
    #    if self.continuous_task is not None:
    #        self.continuous_task.cancel()

    #    pass

    #Funktion on_start---------------------------------------------------------------------------------------------

    async def on_start(self):
        pass

    #Funktion on_stop----------------------------------------------------------------------------------------------

    async def on_stop(self):
        pass

    #Funktion run--------------------------------------------------------------------------------------------------

    async def run(self):
        while self.running is True:
            if self.continuous_mode is True:
                await self.start_request("read")

                if self.stat_actor == "0":
                    self.state = False
                    logger.info("Read from SPS {}".format(self.stat_actor))
                    logger.info("Status self.state: {}".format(self.state))
                    await self.cbpi.actor.actor_update(self.id, self.state)
                else:
                    self.state = True
                    logger.info("Read from SPS {}".format(self.stat_actor))
                    logger.info("Status self.state: {}".format(self.state))
                    await self.cbpi.actor.actor_update(self.id, self.state)
     
                await asyncio.sleep(5)
            else:
                await asyncio.sleep(1)
        pass
 

#Definitionsende----------------------------------------------------------------------------------------------------
    
def setup(cbpi):
    cbpi.plugin.register("ILC Actor", ILCActor)
    pass
