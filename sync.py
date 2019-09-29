#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# SubSlider - a simple script to apply offsets to subtitles
#
# Copyright May 2nd 2012 - MB <https://somethingididnotknow.wordpress.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>
from __future__ import print_function
from datetime import timedelta, datetime
import os
import re
import sys
 
class SubSlider:
    """A simple script to apply offsets to subtitles.
 
    Subtitles can be delayed by specifying a positive offset (e.g. +12 or simply 12), or video can be delayed by specifying a negative offset (e.g. -12)"""
 
    def __init__(self, argv):
        if len(argv) < 2:
            self.usage()
        else:
            self.first_valid = 0
            self.parse_args(argv)
            self.parse_subs()
            self.fix_file()
            os.remove(self.output_temp)
            print('Success! Offset subs have been written to %s' % os.path.abspath(self.output_subs))
 
    def usage(self):
        print("""usage: subslider.py [-h] subs_file offset
 
Applies an offset to a subtitles file
 
positional arguments:
  subs_file             The input subtitles file, the one to which the offset
                        is to be applied
  offset                The offset to be applied to the input subtitles file.
                        Format is [+/-][MM:]SS[,sss] like +1:23,456 (new subs
                        will be displayed with a delay of 1 minute, 23 seconds,
                        456 milliseconds) or -100 (subs 100
                        seconds earlier) or +12,43 (subs delayed of 12 seconds
                        43 milliseconds)""")
        sys.exit(1)
 
 
    def parse_args(self, args):
        error = None
        if not os.path.isfile(args[0]):
            print('%s does not exist' % args[0])
            error = True
        else:
            self.input_subs = args[0]
            self.output_subs = '%s_offset.srt' % os.path.splitext(self.input_subs)[0]
            self.output_temp = '%s_temp.srt' % os.path.splitext(self.input_subs)[0]
        offset_ok = re.match('[\+\-]?(\d{1,2}\:)?\d+(\,\d{1,3})?$', args[1])
        if not offset_ok:
            print('%s is not a valid offset, format is [+/-][MM:]SS[,sss], see help dialog for some examples' % args[1])
            error = True
        else:
            offset = re.search('([\+\-])?((\d{1,2})\:)?(\d+)(\,(\d{1,3}))?', args[1])
            self.direction, self.minutes, self.seconds, self.millis = (offset.group(1), offset.group(3), offset.group(4), offset.group(6))
        if error:
            self.usage()
 
    def parse_subs(self):
        with open(self.input_subs, 'r') as input:
            with open(self.output_temp, 'w') as output:
                nsafe = lambda s: int(s) if s else 0
                block = 0
                date_zero = datetime.strptime('00/1/1','%y/%m/%d')
                for line in input:
                    parsed = re.search('(\d{2}:\d{2}:\d{2},\d{3}) \-\-> (\d{2}:\d{2}:\d{2},\d{3})', line)
                    if parsed:
                        block += 1
                        start, end = (self.parse_time(parsed.group(1)), self.parse_time(parsed.group(2)))
                        offset = timedelta(minutes=nsafe(self.minutes), seconds=nsafe(self.seconds), microseconds=nsafe(self.millis) * 1000)
                        if '-' == self.direction:
                            start -= offset
                            end -= offset
                        else:
                            start += offset
                            end += offset
                        offset_start, offset_end = (self.format_time(start), self.format_time(end))
                        if not self.first_valid:
                            if end > date_zero:
                                self.first_valid = block
                                if start < date_zero:
                                    offset_start = '00:00:00,000'
                        output.write('%s --> %s\n' % (offset_start, offset_end))
                    else:
                        output.write(line)
 
    def fix_file(self):
        with open(self.output_temp, 'r') as input:
            with open(self.output_subs, 'w') as output:
                start_output = False
                for line in input:
                    if re.match('\d+$', line.strip()):
                        block_num = int(line.strip())
                        if block_num >= self.first_valid:
                            if not start_output:
                                start_output = True
                            output.write('%d\r\n' % (block_num - self.first_valid + 1))
                    elif start_output:
                        output.write(line)
 
    def format_time(self, value):
        formatted = datetime.strftime(value, '%H:%M:%S,%f')
        return formatted[:-3]
 
    def parse_time(self, time):
        parsed = datetime.strptime(time, '%H:%M:%S,%f')
        return parsed.replace(year=2000)
 
if __name__ == '__main__':
    SubSlider(sys.argv[1:])
