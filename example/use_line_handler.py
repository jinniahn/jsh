import sys
# adjust sys.path
sys.path.insert(0, '..')

from jsh import sh
from jsh.loghandler import LineHandler
from pprint import pprint

cmd = '''
ls -w1 /tmp
'''

class MyLine(LineHandler):
    def __init__(self):
        super().__init__()
        self.count = 0

    def on_line(self, msg):
        self.count += 1
        print('[{:2d}] {}'.format(self.count, msg))

    def on_start(self):
        print("LOG START")

    def on_end(self):
        print("LOG END")

# run cmd
ret = sh(cmd, logfile=MyLine()).splitlines()

print("\nPRINT RETURN VALUSE")
pprint(ret)

