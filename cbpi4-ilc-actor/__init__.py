
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

    def __init__(self, cbpi, id, props):
        super().__init__(cbpi, id, props)
        self.state = False
        self.continuous_task = None

        self.request_session = requests.Session()
        self.request_session.verify = False
        self.httpmethod_get = True
        
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
        self.url_read = "http://" + self.ip_ilc + "/cgi-bin/readVal.exe?" + self.variable_ilc
        
        #self.url_on = self.props.get("Target URL On")
        #self.url_off = self.props.get("Target URL Off")

        self.payload_on = None
        self.payload_off = None

        self.basic_auth = None

        self.continuous_interval = float(self.props.get("Continuous Interval", 5))

        self.request_session.timeout = float(self.props.get("Request Timeout", 5))

        pass

    async def set_continuous_state(self):
        logger.info('Starting continuous state setter background task interval=%s' % self.continuous_interval)
        while True:
            start_time = int(time.time())
            try:
                await self.start_request(self.state)
            except Exception as e:
                logger.error("Unknown exception: %s" % e)

            wait_time = start_time + self.continous_interval - int(time.time())
            if wait_time < 0:
                logger.warn(
                    "Continuous interval kann nicht gehalten werden, da zu klein und requests brauchen zu lange")
            else:
                await asyncio.sleep(wait_time)

        pass

    async def start_request(self, onoff):
        if onoff:
            url_read = self.url_read        
            read = self.request_session.get(url_read)
            value_read = read.text
            url = self.url_on
            payload = self.payload_on
        else:
            url_read = self.url_read        
            read = self.request_session.get(url_read)
            value_read = read.text
            url = self.url_off
            payload = self.payload_off

        if payload is not None:
            payload_logtext = payload.replace('"', '\\"')
        else:
            payload_logtext = "[not_set]"

        if self.basic_auth is not None:
            basic_auth_logtext = self.basic_auth.username
        else:
            basic_auth_logtext = "[not set]"

        logger.info("ILCActor type=request_start onoff=%s url=\"%s\" value_read=\"%s\" method_getpost=%s user=%s" % (
        onoff, url, value_read, self.httpmethod_get, basic_auth_logtext))
        if self.httpmethod_get:
            response = self.request_session.get(url, data=payload, auth=self.basic_auth)
        else:
            response = self.request_session.post(url, data=payload, auth=self.basic_auth)

        logger.info("ILCActor type=request_done onoff=%s url=\"%s\" http_statuscode=%s response_text=\"%s\"" % (
        onoff, url, response.status_code, response.text.replace('"', '\\"')))

    async def on(self, power=0):
        logger.debug("Actor %s ON" % self.id)
        self.state = True
        await self.start_request(True)

    async def off(self):
        logger.debug("Actor %s OFF" % self.id)
        self.state = False
        await self.start_request(False)

    def get_state(self):
        return self.state

    async def start(self):
        pass

    async def stop(self):
        if self.continuous_task is not None:
            self.continuous_task.cancel()

        pass

    async def on_start(self):
        pass

    async def on_stop(self):
        pass

    async def run(self):
        if self.continuous_mode:
            self.continuous_task = asyncio.create_task(self.set_continuous_state())
        pass


def setup(cbpi):
    cbpi.plugin.register("ILC Actor", ILCActor)
    pass
    async def on_stop(self):
        pass

    
    async def run(self):
        if self.continuous_mode:
            self.continuous_task = asyncio.create_task(self.set_continuous_state())
        pass
    
def setup(cbpi):
    cbpi.plugin.register("ILC Actor", ILCActor)
    pass
