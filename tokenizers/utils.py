import hashlib
import os
import zipfile
import datetime as dt
import re
import collections


def remove_comments(string, language_config):
    start_time = dt.datetime.now()
    # Remove tagged comments
    result_string = re.sub(language_config["comment_open_close_pattern"], '', string, flags=re.DOTALL)  # Remove tagged comments
    # Remove end of line comments
    result_string = re.sub(language_config["comment_inline_pattern"], '', result_string, flags=re.MULTILINE)  # Remove end of line comments
    end_time = dt.datetime.now()
    time = (end_time - start_time).microseconds
    return result_string, time


# SourcererCC tokens formatting
def format_tokens(tokens_bag):
    start_time = dt.datetime.now()
    tokens = ','.join(['{}@@::@@{}'.format(k, v) for k, v in tokens_bag.items()])
    end_time = dt.datetime.now()
    time = (end_time - start_time).microseconds
    return tokens, time


def tokenize_string(string, language_config):
    tokenized_string = string
    # Transform separators into spaces (remove them)
    for x in language_config["separators"]:
        tokenized_string = tokenized_string.replace(x, ' ')

    tokens_list = tokenized_string.split()  # Create a list of tokens
    total_tokens = len(tokens_list)  # Total number of tokens
    tokens_counter = collections.Counter(tokens_list)  # Count occurrences
    tokens_bag = dict(tokens_counter)  # Converting Counter to dict, {token: occurences}
    unique_tokens = len(tokens_bag)  # Unique number of tokens
    return tokens_bag, total_tokens, unique_tokens


def count_lines(string, count_empty = True):
    result = string.count('\n')
    if not string.endswith('\n') and (count_empty or string != ""):
        result += 1
    return result


def md5_hash(string):
    m = hashlib.md5()
    m.update(string.encode("utf-8"))
    return m.hexdigest()


def hash_measuring_time(string):
    start_time = dt.datetime.now()
    hash_value = md5_hash(string)
    end_time = dt.datetime.now()
    time = (end_time - start_time).microseconds
    return hash_value, time
