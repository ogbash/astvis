
import logging

class ColorTerminalHandler(logging.StreamHandler):

    def emit(self, record):
        self.acquire()
        try:
            # set color
            if record.levelno>=logging.WARN:
                self.stream.write("\033[031m")
            elif record.levelno>=logging.WARN:
                self.stream.write("\033[033m")
            elif record.levelno>=logging.INFO:
                self.stream.write("\033[034m")
            elif record.levelno<logging.DEBUG:
                self.stream.write("\033[037m") # white should be gray
            # print
            try:
                logging.StreamHandler.emit(self,record)
            finally:
                self.stream.write("\033[030m")
        finally:
            self.release()

