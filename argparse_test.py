#!/usr/bin/env python3

"""
argparse tutorial/learning

https://docs.python.org/2/howto/argparse.html#id1

Lesson #1: don't name this file 'argparse.py'

"""

import argparse

# Parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("sort_key", help="Sort Key")
parser.add_argument("entry_count", type=int, help="Number of entries returned")
parser.add_argument("sort_order", help="Sort order")
args = parser.parse_args()
print("Args:\n\tSort key: {}\n\tEntry count: {}\n\tSort order: {}\n".format(
    args.sort_key, args.entry_count, args.sort_order))

# import argparse
# parser = argparse.ArgumentParser()
# parser.add_argument("square", help="display a square of a given number",
#                     type=int)
# args = parser.parse_args()
# print(args.square**2)