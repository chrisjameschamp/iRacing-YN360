import asyncio
import bleak
import irsdk
import logging
import pytimedinput
import sys

from util import functions, colargulog

VERSION = '1.3.2'

DEBUG = False

class ir_yn360:
    def __init__(self):
        self.ir = irsdk.IRSDK()
        self.status = 'disconnected' #Options are: connected, disconnected, waiting, racing
        self.client = None
        self.current_color = [0,0,0]
        self.rest_color = [0,0,255]
        self.flags = {'bit': 0, 'active': {}, 'waiving': ''}

    async def start(self):
        logger.info('Welcome to iRacing YN360')
        functions.checkVersion(VERSION)
        device = functions.getDevice()
        if device:
            logger.info('Existing Device Found - {}', device[0])
            logger.info('Press any key to select a new device or wait 5 seconds...')
            user_input, timed_out = pytimedinput.timedKey('>>>')
            if not timed_out:
                device = await self.scan()
        else:
            device = await self.scan()
        await self.run(device)

    async def setColor(self, color):
        if color != self.current_color:
            sendCharUuid = 'f000aa61-0451-4000-b000-000000000000'
            logger.debug('Color Change Sent: R{}, G{}, B{}', color[0], color[1], color[2])
            await self.client.write_gatt_char(sendCharUuid, bytearray([0xae,0xa1,color[0],color[1],color[2]]), response=True)
            self.current_color = color

    async def run(self, device):
        if await self.connect(device):
            while True:
                self.checkiRacing()
                if self.status == 'racing':
                    # Flags
                    diff = self.flags['bit'] ^ self.ir['SessionFlags']
                    if diff:
                        self.flags['bit'] = self.ir['SessionFlags']

                        for flag in functions.FLAGS:
                            if diff & flag[0]:
                                if flag[0] & self.flags['bit']:
                                    if flag[1] not in self.flags['active'].keys():
                                        self.flags['active'][flag[1]] = flag[0]
                                else:
                                    if flag[1] in self.flags['active'].keys():
                                        del self.flags['active'][flag[1]]

                    self.resting = False

                    if 'checkered' in self.flags['active'].keys():
                        if self.flags['waiving'] != 'checkered':
                            logger.info('Checkered Flag Waiving')
                            self.flags['waiving'] = 'checkered'
                        if self.flags['waiving'] == 'checkered':
                            if self.current_color != [255,255,255]:
                                await self.setColor([255,255,255])
                            else:
                                await self.setColor([0,0,0])
                    elif 'caution_waving' in self.flags['active'].keys():
                        if self.flags['waiving'] != 'caution':
                            logger.info('Caution Flag Waiving')
                            self.flags['waiving'] = 'caution'
                        self.flags['flashing'] = ''
                        await self.setColor([255,255,0])
                    elif 'yellow_waving' in self.flags['active'].keys():
                        if self.flags['waiving'] != 'yellow':
                            logger.info('Yellow Flag Waiving')
                            self.flags['waiving'] = 'yellow'
                        self.flags['flashing'] = ''
                        await self.setColor([255,255,0])
                    elif 'start_go' in self.flags['active'].keys():
                        if self.flags['waiving'] != 'green':
                            logger.info('Green Flag Waiving')
                            self.flags['waiving'] = 'green'
                        self.flags['flashing'] = ''
                        await self.setColor([0,255,0])
                    elif 'repair' in self.flags['active'].keys():
                        if self.flags['waiving'] != 'repair':
                            logger.info('Meatball Flag Waiving')
                            self.flags['waiving'] = 'repair'
                        if self.current_color != [255,140,0]:
                            await self.setColor([255,140,0])
                        else:
                            await self.setColor([0,0,0])
                    elif 'white' in self.flags['active'].keys():
                        if self.flags['waiving'] != 'white':
                            logger.info('White Flag Waiving')
                            self.flags['waiving'] = 'white'
                        self.flags['flashing'] = ''
                        await self.setColor([255,255,255])
                    elif 'debris' in self.flags['active'].keys():
                        if self.flags['waiving'] != 'yellow':
                            logger.info('Yellow Flag Waiving')
                            self.flags['waiving'] = 'yellow'
                        self.flags['flashing'] = ''
                        await self.setColor([255,255,0])
                    elif 'green' in self.flags['active'].keys():
                        if self.flags['waiving'] != 'green':
                            logger.info('Green Flag Waiving')
                            self.flags['waiving'] = 'green'
                        self.flags['flashing'] = ''
                        await self.setColor([0,255,0])
                    elif 'red' in self.flags['active'].keys():
                        if self.flags['waiving'] != 'red':
                            logger.info('Red Flag Waiving')
                            self.flags['waiving'] = 'red'
                        self.flags['flashing'] = ''
                        await self.setColor([255,0,0])
                    elif 'caution' in self.flags['active'].keys():
                        if self.flags['waiving'] != 'caution':
                            logger.info('Caution Flag Waiving')
                            self.flags['waiving'] = 'caution'
                        self.flags['flashing'] = ''
                        await self.setColor([255,255,0])
                    elif 'yellow' in self.flags['active'].keys():
                        if self.flags['waiving'] != 'yellow':
                            logger.info('Yellow Flag Waiving')
                            self.flags['waiving'] = 'yellow'
                        self.flags['flashing'] = ''
                        await self.setColor([255,255,0])
                    elif 'blue' in self.flags['active'].keys():
                        if self.flags['waiving'] != 'blue':
                            logger.info('Blue Flag Waiving')
                            self.flags['waiving'] = 'blue'
                        self.flags['flashing'] = ''
                        await self.setColor([0,0,255])
                    else:
                        if self.flags['waiving'] != '':
                            await self.setColor(self.rest_color)
                            logger.info('Set to Resting Color')
                            self.flags['waiving'] = ''
                    await asyncio.sleep(1)
                else:
                    if self.status != 'waiting':
                        await self.setColor(self.rest_color)
                        logger.info('Waiting for iRacing...')
                        logger.info('Light set to resting color')
                        logger.info('Press CTRL + C to exit')
                        self.status = 'waiting'
                    await asyncio.sleep(3)

    async def connect(self, device):
        logger.info('Connecting...')
        self.client = bleak.BleakClient(device[1])
        try:
            await self.client.connect()
            self.status = 'connected'
            logger.info('Connected')
            return True
        except:
            logger.error('Could not connect to device')
            return False

    async def disconnect(self):
        if self.status != 'disconnected':
            logger.info('Disconnecting...')
            if self.status == 'racing':
                self.ir.shutdown()
                logger.info('iRacing Disconnected')
            try:
                await self.setColor([0,0,0])
                await self.client.disconnect()
                self.status = 'disconnected'
                logger.info('Disconnected')
                return True
            except:
                logger.error('Could not disconnect from device')
                return False

    def checkiRacing(self):
        if self.status == 'racing' and not (self.ir.is_initialized and self.ir.is_connected):
            self.status = 'waiting'
            self.ir.shutdown()
            logger.info('iRacing Disconnected')
            return False
        elif self.status == 'waiting' and self.ir.startup() and self.ir.is_initialized and self.ir.is_connected:
            self.status = 'racing'
            logger.info('iRacing Connected')
            return True
        elif self.status =='racing':
            return True
        else:
            return False

    async def scan(self):
        logger.info('Scanning for BLE Devices...')
        try:
            devices = await bleak.BleakScanner.discover()
        except Exception as e:
            logger.error('{}', e)
            function.closeApp()
        if not devices:
            logger.info('No BLE devices found')
            function.closeApp()
        names = []
        for i, item in enumerate(devices):
            device = str(item).split(':')
            name = device[-1].lstrip()
            device = device[:-1]
            device = ':'.join(device)
            if name != 'None':
                names.append([name, device])
        logger.info('Found {}', len(names))
        for i, item in enumerate(names, start=1):
            logger.info('  {}) {}', i, item[0])
        while True:
            logger.info('Select the corresponding number next to the YN360.  All other devices may not work.')
            user_input = input('>>> ')
            try:
                value = int(user_input)
                if value >= 1 and value <= len(names):
                    device = names[int(user_input)-1]
                    logger.info('You chose: {}', device[0])
                    logger.info('Confirm Y/N?')
                    if input('>>> ').lower() == 'y':
                        break
                else:
                    logger.info('Invalid input, please enter a number between {} and {}', '1', len(names))
            except ValueError:
                logger.info('Invalid input, please enter a number between {} and {}', 1, len(names))
        functions.saveDevice(device)
        return device

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--debug':
        DEBUG = True

    # SETUP LOG LEVEL - DEBUG: debug message | INFO: info message | WARNING: warn message | ERROR: error message
    console_handler = logging.StreamHandler(stream=sys.stdout)
    if DEBUG:
        colored_formatter = colargulog.ColorizedArgsFormatter('%(asctime)s [%(levelname)s] %(name)-25s - %(message)s')
    else:
        colored_formatter = colargulog.ColorizedArgsFormatter('%(asctime)s [%(levelname)s] - %(message)s', '%H:%M:%S')
    logging.getLogger().setLevel(logging.INFO)
    logger = logging.getLogger()
    logger.name = 'iRacing-YN360'
    logger.addHandler(console_handler)

    loop = asyncio.new_event_loop()
    ir = ir_yn360()
    try:
        loop.run_until_complete(ir.start())
    except Exception as e:
        logger.error('{}', e)
    except KeyboardInterrupt as e:
        logger.info('Exiting...')
    finally:
        loop.run_until_complete(ir.disconnect())
        loop.close()