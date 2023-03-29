"""
This class was created to create a log file when running the reach averaged
forest resistance model (Hydraulics.py). Logged lines are printed to the
console and a plain text log file.
"""
from datetime import datetime
import os


class LogFile:
    def __init__(self):
        self.file_name = ''
        self.event_file = ''
        self.ufm = ''

    def set_log_file_name(self, ufm):
        # set the filename of the log file
        folder = '{}/log/'.format(os.path.dirname(ufm))
        base_file_name = os.path.basename(ufm)
        base_file_name = os.path.splitext(base_file_name)[0]
        self.file_name = '{}{}_log_file.txt'.format(folder, base_file_name)

    def initialise(self, ufm):
        self.ufm = ufm

        # set the filename of the log file
        self.set_log_file_name(ufm)

        # set the file name of the event file
        self.event_file = '{}\\..\\_Event_file.txt'.format(os.path.dirname(ufm))
        print(os.path.abspath(self.event_file))

        # create files and write intialisation info
        lines = ['\nStarting uniform flow model: {}'.format(datetime.now()),
                 '\nopening uniform flow model (ufm) file...',
                 os.path.abspath(self.ufm),
                 '\nModel home path is: {}\n'.format(os.path.abspath(os.path.dirname(self.ufm)))]
        for line in lines:
            print(line)
        lf = open(self.file_name, 'w+')
        lf.writelines(lines)
        lf.close()

    def log(self, log_line):
        print(log_line)
        log_line = '{}\n'.format(log_line)
        lf = open(self.file_name, 'a')
        lf.write(log_line)
        lf.close()

    def log_event_start(self):
        out_line = 'Started: {}    Model file: {}'.format(datetime.now().replace(microsecond=0),
                                                          os.path.abspath(self.ufm))
        print('\n{}'.format(out_line))
        ef = open(self.event_file, 'a+')
        ef.write('\n{}'.format(out_line))
        ef.close()

    def log_event_end(self):
        out_line = 'Ended: {}    Model file: {}'.format(datetime.now().replace(microsecond=0)
                                                        , os.path.abspath(self.ufm))
        print('\n{}'.format(out_line))
        ef = open(self.event_file, 'a+')
        ef.write('\n{}'.format(out_line))
        ef.close()


