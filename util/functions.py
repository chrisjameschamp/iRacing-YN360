import json
import logging
import os
import requests
import sys

from packaging.version import Version
from appdirs import *

APPDATA_FOLDER = user_data_dir('iRacing-YN360', 'ChrisJamesChamp')

logger = logging.getLogger(__name__)

def ensureAppDataFolder():
    folder = APPDATA_FOLDER
    #print('Ensuring App Data Folder Exists')
    if not os.path.exists(folder):
        logger.warning('App Data Folder Does Not Exist')
        logger.info('Creating App Data Folder...')

        try:
            os.makedirs(folder)
            logger.info('Created App Data Folder')
        except:
            logger.error('Could not open the App Data Folder')
            closeApp()

    else:
        logger.debug('App Data Folder Exists: {}', folder)

def closeApp():
    logger.info('Exiting...')
    sys.exit();

def getDevice():
    ensureAppDataFolder()
    try:
        with open(f'{APPDATA_FOLDER}/device.json') as infile:
            data = json.load(infile)
        logger.info('Loaded Existing Device')
        return data
    except:
        logger.warning('No Existing Device Found')
        return None

def saveDevice(device):
    ensureAppDataFolder()
    logger.info('Saving Device...')
    try:
        with open(f'{APPDATA_FOLDER}/device.json', 'w') as outfile:
            json.dump(device, outfile)
        logger.info('Device Saved')
    except Exception as e:
        logger.error('Could Not Save Device | {}', e)

def checkVersion(version):
    logger.info('Version: {}', version)
    logger.info('Checking for Updates...')
    
    url = 'https://api.github.com/repos/chrisjameschamp/iRacing-YN360/releases/latest'
    response = requests.get(url).json()
    if 'tag_name' in response:
        gitVersion = Version(response['tag_name'])
        curVersion = Version(version)

        if gitVersion > curVersion:
            logger.info('There is a new version of iRacing-YN360 availableThe Most recent version is {}', gitVersion)
            logger.info('Get the latest version by visiting https://github.com/chrisjameschamp/iRacing-YN360')
        else:
            logger.info('You are up to date')

    else:
        logger.error('Error Checking for Updates')

FLAGS = [
    ## Global Flags
    (0x0001, 'checkered'),
    (0x0002, 'white'),
    (0x0004, 'green'),
    (0x0008, 'yellow'),
    (0x0010, 'red'),
    (0x0020, 'blue'),
    (0x0040, 'debris'),
    (0x0080, 'crossed'),
    (0x0100, 'yellow_waving'),
    (0x0200, 'one_lap_to_green'),
    (0x0400, 'green_held'),
    (0x0800, 'ten_to_go'),
    (0x1000, 'five_to_go'),
    (0x2000, 'random_waving'),
    (0x4000, 'caution'),
    (0x8000, 'caution_waving'),

    ## Drivers Black Flags
    (0x010000, 'black'),
    (0x020000, 'disqualified'),
    (0x040000, 'serviceable'), # Car Is Allowed Service (Not A Flag)
    (0x080000, 'furled'),
    (0x100000, 'repair'),

    ## Start Lights
    (0x10000000, 'start_hidden'),
    (0x20000000, 'start_ready'),
    (0x40000000, 'start_set'),
    (0x80000000, 'start_go'),

    ## Pace Flags
    (0x01, 'end_of_line'),
    (0x02, 'free_pass'),
    (0x04, 'waved_around')
]