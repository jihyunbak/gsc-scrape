# utils.py

import csv
import time
import os
import re

def read_csv(csvfilename):
    ''' read from a csv file '''
    all_mol_address = []
    with open(csvfilename, newline='') as f:
        reader = csv.reader(f)
        headers = next(f) # skip header
        for row in reader:
            all_mol_address.append(row)
    return all_mol_address

def make_dir(dir):
    ''' create directory if not already exists '''
    mydirobj = os.path.dirname(dir)
    if not os.path.exists(mydirobj):
        os.makedirs(mydirobj)

def isfile(filename):
    return os.path.isfile(filename)

def timer(old_time=None):
    new_time = time.time()
    if old_time is None:
        elapsed = 0
    else:
        elapsed = new_time - old_time
    return elapsed, new_time

def wait(dt):
    time.sleep(dt)

def search_string_between(search_from, front, back, extract_pattern=True):
    ''' find string between two substrings '''
    result = re.search('%s(.*)%s' % (front, back), search_from)
    if extract_pattern:
        return result.group(1)
    else:
        return result
