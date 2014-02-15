#!/opt/local/bin/python3.3   -*- cofing:utf-8 -*-
#
#
#  Created by NAKAJIMA Takaaki 
#  Last modified: Feb 15, 2014.
#
import logging

from optparse import OptionParser
parser = OptionParser()
parser.add_option("-c", "--config", dest="config", default="~/.softlayer",
                  help="SoftLayer configuration FILE", metavar="FILE")

(options, args) = parser.parse_args()

def load_config(fname):
    logging.info("Loading config file: " + fname)
    import configparser
    config = configparser.ConfigParser()
    try:
        config.read(fname)
        return config['softlayer']
    except Exception as exc:
        logging.error('Failed to load config file:' + fname)
        raise(exc)

conf = load_config(options.config)

import SoftLayer
client = SoftLayer.Client(username=conf['username'], api_key=conf['api_key'])

print(client['Account'].getObject())



