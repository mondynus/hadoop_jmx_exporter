#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import threading
import requests

import re
import socket
import sys
from requests_kerberos import HTTPKerberosAuth


from utils import get_module_logger


logger = get_module_logger(__name__)


class Scraper(threading.Thread):
    def __init__(self, url, result):
        super(Scraper, self).__init__()
        self.name = "thread-%s" % url
        self.url = self.fixurl(url)
        self.result = result
    
    def validate_ip(self,ip_str):
      reg = r"^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$"
      if re.match(reg, ip_str):
        return True
      else:
        return False

    def fixurl(self,url):
        address = url.replace("http://","")
        part_address=address.split(":")

        if self.validate_ip(part_address[0]):
          host = socket.gethostbyaddr(part_address[0])
          host=host[0]+":"+str(part_address[1])
        else:
          host=address

        return "http://"+host
    

    def run(self):
        result = []
        try:
            s = requests.session()
            if "8088" in self.url:
              response = s.get(self.url, timeout=5)
            else:
              response = s.get(self.url, timeout=5,auth=HTTPKerberosAuth())
        except Exception as e:
            logger.warning("Get {0} failed, error: {1}.".format(self.url, str(e)))
        else:
            if response.status_code != requests.codes.ok:
                logger.warning("Get {0} failed, response code is: {1}.".format(self.url, response.status_code))
            else:
                rlt = response.json()
                if rlt and "beans" in rlt:
                    result = rlt['beans']
                else:
                    logger.warning("No metrics get in the {0}.".format(self.url))
            s.close()
            if len(result) > 0:
                self.result.append(result)


class ScrapeMetrics(object):
    def __init__(self, urls):
        self.urls = urls

    def scrape(self):
        result = []
        tasks = [Scraper(url, result) for url in self.urls]
        for task in tasks:
            task.start()
        for task in tasks:
            task.join()
        return result
