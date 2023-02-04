import asyncio
import bleak
import irsdk
import pytimedinput
import re
import uuid

from util import functions

VERSION = '0.0.1'

class ir_yn360:
    def __init__(self):
        self.ir = irsdk.IRSDK()
        self.ir_connected = False
        self.current_color = [0,0,0] #RGB 0-255
        self.rest_color = [0,0,255]
        self.resting = False
        self.flags = {'bit': 0, 'active': {}, 'cycle': 1, 'flashing': '', 'waiving': ''}
        self.flash_rate = 1

    async def start(self):
        print('Welcome to iRacing YN360\n')
        functions.checkVersion(VERSION)
        address = self.getAddress()
        device = functions.getDevice()
        if device:
            user_input, timed_out = pytimedinput.timedKey(f'Existing Device Found - {device[0]}\nPress any key to select a new device or wait 5 seconds...')
            if not timed_out:
                print('')
                device = await self.scan()
        else:
            device = await self.scan()

        await self.run(device, address)

    
    async def run(self, device, address):
        print('Connecting...')
        client = bleak.BleakClient(device[1])
        try:
            await client.connect()
            print('Connected\n')
            while True:
                if self.checkiRacing():

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
                        if self.flags['flashing'] != 'checkered':
                            self.flags['cycle'] = self.flash_rate
                            self.flags['flashing'] = 'checkered'
                        if self.flags['cycle'] % self.flash_rate == 0:
                            if self.current_color != [255,255,255]:
                                await self.setColor([255,255,255], client, address)
                            else:
                                await self.setColor([0,0,0], client, address)
                    elif 'caution_waving' in self.flags['active'].keys():
                        if self.flags['waiving'] != 'caution':
                            print('Caution Flag Waiving')
                            self.flags['waiving'] = 'caution'
                        self.flags['flashing'] = ''
                        await self.setColor([255,255,0], client, address)
                    elif 'yellow_waving' in self.flags['active'].keys():
                        if self.flags['waiving'] != 'yellow':
                            print('Yellow Flag Waiving')
                            self.flags['waiving'] = 'yellow'
                        self.flags['flashing'] = ''
                        await self.setColor([255,255,0], client, address)
                    elif 'start_go' in self.flags['active'].keys():
                        if self.flags['waiving'] != 'green':
                            print('Green Flag Waiving')
                            self.flags['waiving'] = 'green'
                        self.flags['flashing'] = ''
                        await self.setColor([0,255,0], client, address)
                    elif 'repair' in self.flags['active'].keys():
                        if self.flags['waiving'] != 'repair':
                            print('Meatball Flag Waiving')
                            self.flags['waiving'] = 'repair'
                        if self.flags['flashing'] != 'repair':
                            self.flags['cycle'] = self.flash_rate
                            self.flags['flashing'] = 'repair'
                        if self.flags['cycle'] % self.flash_rate == 0:
                            if self.current_color != [255,140,0]:
                                await self.setColor([255,140,0], client, address)
                            else:
                                await self.setColor([0,0,0], client, address)
                    elif 'white' in self.flags['active'].keys():
                        if self.flags['waiving'] != 'white':
                            print('White Flag Waiving')
                            self.flags['waiving'] != 'white'
                        self.flags['flashing'] = ''
                        await self.setColor([255,255,255], client, address)
                    elif 'debris' in self.flags['active'].keys():
                        if self.flags['waiving'] != 'yellow':
                            print('Yellow Flag Waiving')
                            self.flags['waiving'] = 'yellow'
                        self.flags['flashing'] = ''
                        await self.setColor([255,255,0], client, address)
                    elif 'green' in self.flags['active'].keys():
                        if self.flags['waiving'] != 'green':
                            print('Green Flag Waiving')
                            self.flags['waiving'] = 'green'
                        self.flags['flashing'] = ''
                        await self.setColor([0,255,0], client, address)
                    elif 'red' in self.flags['active'].keys():
                        if self.flags['waiving'] != 'red':
                            print('Red Flag Waiving')
                            self.flags['waiving'] = 'red'
                        self.flags['flashing'] = ''
                        await self.setColor([255,0,0], client, address)
                    elif 'caution' in self.flags['active'].keys():
                        if self.flags['waiving'] != 'caution':
                            print('Caution Flag Waiving')
                            self.flags['waiving'] = 'caution'
                        self.flags['flashing'] = ''
                        await self.setColor([255,255,0], client, address)
                    elif 'yellow' in self.flags['active'].keys():
                        if self.flags['waiving'] != 'yellow':
                            print('Yellow Flag Waiving')
                            self.flags['waiving'] = 'yellow'
                        self.flags['flashing'] = ''
                        await self.setColor([255,255,0], client, address)
                    elif 'blue' in self.flags['active'].keys():
                        if self.flags['waiving'] != 'blue':
                            print('Blue Flag Waiving')
                            self.flags['waiving'] = 'blue'
                        self.flags['flashing'] = ''
                        await self.setColor([0,0,255], client, address)
                    else:
                        if self.flags['waiving'] != '':
                            await self.setColor(self.rest_color, client, address)
                            print('Set to Resting Color')
                            self.flags['waiving'] = ''
                            
                    self.flags['cycle'] += 1
                    await asyncio.sleep(1)
                else:
                    if not self.resting:
                        await self.setColor(self.rest_color, client, address)
                        print('Set to Resting Color')
                        self.resting = True
                    await asyncio.sleep(3)
        except KeyboardInterrupt:
            await self.setColor([0,0,0], client, address)
            print('Disconnecting...')
        except Exception as e:
            print(f'Error: {e}')
        finally:
            await client.disconnect()


    async def scan(self):
        print('Scanning for BLE Devices...\n')
        try:
            devices = await bleak.BleakScanner.discover()
        except Exception as e:
            print(f'Error: {e}')
            function.closeApp()
        if not devices:
            print('No BLE devices found')
            function.closeApp()
        names = []
        ## Probably could just find the device that is YN360
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
            print('\nSelect the corresponding number next to the YN360.  All other devices may not work.')
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


    def getAddress(self):
        address = ':'.join(re.findall('..', '%012x' % uuid.getnode()))
        print(f'System Address: {address}\n')
        return address


    async def setColor(self, color, client, address):
        if color != self.current_color:
            sendCharUuid = 'f000aa61-0451-4000-b000-000000000000'
            await client.write_gatt_char(sendCharUuid, bytearray([0xae,0xa1,color[0],color[1],color[2]]), response=True)
            self.current_color = color

    def checkiRacing(self):
        if self.ir_connected and not (self.ir.is_initialized and self.ir.is_connected):
            self.ir_connected = False
            self.ir.shutdown()
            print('iRacing Disconnected')
            return False
        elif not self.ir_connected and self.ir.startup() and self.ir.is_initialized and self.ir.is_connected:
            self.ir_connected = True
            print('iRacing Connected')
            return True
        elif self.ir_connected:
            return True
        else:
            return False

if __name__ == '__main__':
    iryn = ir_yn360()
    asyncio.run(iryn.start())