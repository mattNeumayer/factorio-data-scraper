import sys

class ProgressBar:
    def __init__(self, text, total):
        self.text = text
        self.total = total
        self.length = 40
        self.update(0)

    def update(self, val):
        percent = 100.0 * val / self.total
        
        sys.stdout.write('\r')
        sys.stdout.write("{}: [{:{}}] {}/{} "
                .format(self.text, '='*int(percent / (100.0/self.length)), self.length, val, self.total))

    def finish(self):
        self.update(self.total)
        sys.stdout.write('\n')
