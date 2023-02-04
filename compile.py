import subprocess

from iryn360 import VERSION

print('Compiling iRacing-YN360\n')

command = f'pyinstaller iryn360.spec --distpath dist/{VERSION}/'

process = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE,  stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
for line in process.stdout:
    print(line, end='')
process.wait()