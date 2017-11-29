'''\

log handler.

This is like file-like object.

  - LineHandler:
    - on_line method is called back when it received line data

'''

class LineHandler():
    '''Print Log line by line'''
    
    def __init__(self):
        self.last_line = None
        self.first = True

    def write(self, msg):
        if self.first:
            self.first = False
            self.on_start()
            
        lines = msg.split('\n')
        if lines:
            self.last_line = lines[-1]
            lines = lines[:-1]
        for l in lines:
            self.on_line(l)

    def close(self):
        if self.last_line:
            self.on_line(l)
        self.on_end()

    def on_line(self, line):
        pass

    def on_start(self):
        pass

    def on_end(self):
        pass

