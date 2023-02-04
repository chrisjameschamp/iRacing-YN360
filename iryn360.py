import asyncio
import bleak
import irsdk
import logging
import pytimedinput
import re
import uuid

from util import functions

VERSION = '1.1.2'

class ir_yn360:
    def __init__(self):
        self.ir = irsdk.IRSDK()
        self.status = 'disconnected' #Options are: connected, disconnected, waiting, racing
        self.client = None
        self.current_color = [0,0,0]
        self.rest_color = [0,0,255]
        self.flags = {'bit': 0, 'active': {}, 'waiving': ''}

    async def start(self):
        print('Welcome to iRacing YN360')
        functions.checkVersion(VERSION)
        device = functions.getDevice()
        if device:
            user_input, timed_out = pytimedinput.timedKey(f'Existing Device Found - {device[0]}\nPress any key to select a new device or wait 5 seconds...')
            if not timed_out:
                print('')
                device = await self.scan()
        else:
            device = await self.scan()

        await self.run(device)

    async def setColor(self, color):
        if color != self.current_color:
            sendCharUuid = 'f000aa61-0451-4000-b000-000000000000'
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
                            print('Checkered Flag Waiving')
                            self.flags['waiving'] = 'checkered'
                            if self.current_color != [255,255,255]:
                                await self.setColor([255,255,255])
                            else:
                                await self.setColor([0,0,0])
                    elif 'caution_waving' in self.flags['active'].keys():
                        if self.flags['waiving'] != 'caution':
                            print('Caution Flag Waiving')
                            self.flags['waiving'] = 'caution'
                        self.flags['flashing'] = ''
                        await self.setColor([255,255,0])
                    elif 'yellow_waving' in self.flags['active'].keys():
                        if self.flags['waiving'] != 'yellow':
                            print('Yellow Flag Waiving')
                            self.flags['waiving'] = 'yellow'
                        self.flags['flashing'] = ''
                        await self.setColor([255,255,0])
                    elif 'start_go' in self.flags['active'].keys():
                        if self.flags['waiving'] != 'green':
                            print('Green Flag Waiving')
                            self.flags['waiving'] = 'green'
                        self.flags['flashing'] = ''
                        await self.setColor([0,255,0])
                    elif 'repair' in self.flags['active'].keys():
                        if self.flags['waiving'] != 'repair':
                            print('Meatball Flag Waiving')
                            self.flags['waiving'] = 'repair'
                        if self.current_color != [255,140,0]:
                            await self.setColor([255,140,0])
                        else:
                            await self.setColor([0,0,0])
                    elif 'white' in self.flags['active'].keys():
                        if self.flags['waiving'] != 'white':
                            print('White Flag Waiving')
                            self.flags['waiving'] != 'white'
                        self.flags['flashing'] = ''
                        await self.setColor([255,255,255])
                    elif 'debris' in self.flags['active'].keys():
                        if self.flags['waiving'] != 'yellow':
                            print('Yellow Flag Waiving')
                            self.flags['waiving'] = 'yellow'
                        self.flags['flashing'] = ''
                        await self.setColor([255,255,0])
                    elif 'green' in self.flags['active'].keys():
                        if self.flags['waiving'] != 'green':
                            print('Green Flag Waiving')
                            self.flags['waiving'] = 'green'
                        self.flags['flashing'] = ''
                        await self.setColor([0,255,0])
                    elif 'red' in self.flags['active'].keys():
                        if self.flags['waiving'] != 'red':
                            print('Red Flag Waiving')
                            self.flags['waiving'] = 'red'
                        self.flags['flashing'] = ''
                        await self.setColor([255,0,0])
                    elif 'caution' in self.flags['active'].keys():
                        if self.flags['waiving'] != 'caution':
                            print('Caution Flag Waiving')
                            self.flags['waiving'] = 'caution'
                        self.flags['flashing'] = ''
                        await self.setColor([255,255,0])
                    elif 'yellow' in self.flags['active'].keys():
                        if self.flags['waiving'] != 'yellow':
                            print('Yellow Flag Waiving')
                            self.flags['waiving'] = 'yellow'
                        self.flags['flashing'] = ''
                        await self.setColor([255,255,0])
                    elif 'blue' in self.flags['active'].keys():
                        if self.flags['waiving'] != 'blue':
                            print('Blue Flag Waiving')
                            self.flags['waiving'] = 'blue'
                        self.flags['flashing'] = ''
                        await self.setColor([0,0,255])
                    else:
                        if self.flags['waiving'] != '':
                            await self.setColor(self.rest_color)
                            print('Set to Resting Color')
                            self.flags['waiving'] = ''
                    await asyncio.sleep(1)
                else:
                    if self.status != 'waiting':
                        await self.setColor(self.rest_color)
                        print('Waiting for iRacing...')
                        print('Light set to resting color')
                        print('Press CTRL + C to exit')
                        self.status = 'waiting'
                    await asyncio.sleep(3)

    async def connect(self, device):
        print('Connecting...')
        self.client = bleak.BleakClient(device[1])
        try:
            await self.client.connect()
            self.status = 'connected'
            print('Connected')
            return True
        except:
            print('Error: Could not connect to device')
            return False

    async def disconnect(self):
        if self.status != 'disconnected':
            print('Disconnecting...')
            if self.status == 'racing':
                self.ir.shutdown()
                print('iRacing Disconnected')
            try:
                await self.setColor([0,0,0])
                await self.client.disconnect()
                self.status = 'disconnected'
                print('Disconnected')
                return True
            except:
                print('Error: Could not disconnect from device')
                return False

    def checkiRacing(self):
        if self.status == 'racing' and not (self.ir.is_initialized and self.ir.is_connected):
            self.status = 'waiting'
            self.ir.shutdown()
            print('iRacing Disconnected')
            return False
        elif self.status == 'waiting' and self.ir.startup() and self.ir.is_initialized and self.ir.is_connected:
            self.status = 'racing'
            print('iRacing Connected')
            return True
        elif self.status =='racing':
            return True
        else:
            return False

    async def scan(self):
        print('Scanning for BLE Devices...')
        try:
            devices = await bleak.BleakScanner.discover()
        except Exception as e:
            print(f'Error: {e}')
            function.closeApp()
        if not devices:
            print('No BLE devices found')
            function.closeApp()
        names = []
        for i, item in enumerate(devices):
            device = str(item).split(':')
            name = device[-1].lstrip()
            device = device[:-1]
            device = ':'.join(device)
            if name != 'None':
                names.append([name, device])
        print(f'Found {len(names)}')
        for i, item in enumerate(names, start=1):
            print(f'  {i}) {item[0]}')
        while True:
            print('Select the corresponding number next to the YN360.  All other devices may not work.')
            user_input = input('>>> ')
            try:
                value = int(user_input)
                if value >= 1 and value <= len(names):
                    device = names[int(user_input)-1]
                    print(f'You chose: {device[0]}')
                    print('Confirm Y/N?')
                    if input('>>> ').lower() == 'y':
                        break
                else:
                    print(f'Invalid input, please enter a number between 1 and {len(names)}')
            except ValueError:
                print(f'Invalid input, please enter a number between 1 and {len(names)}')
        functions.saveDevice(device)
        return device

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    ir = ir_yn360()
    try:
        loop.run_until_complete(ir.start())
    except Exception as e:
        print(f'Error: {e}')
    except KeyboardInterrupt as e:
        print('Exiting...')
    finally:
        loop.run_until_complete(ir.disconnect())
        loop.close()