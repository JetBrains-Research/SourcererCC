import datetime as dt
import zipfile
import re
import collections
import hashlib
import os
from configparser import ConfigParser

from .utils import *


MULTIPLIER = 50000000

N_PROCESSES = 2
PROJECTS_BATCH = 20

dirs_config = {}
dirs_config["bookkeeping_folder"] = 'bookkeeping_projs'
dirs_config["tokens_file"] = 'files_tokens'
FILE_projects_list = "project-list.txt"
language_config = {}

file_count = 0


def read_config(config_filename):
    global N_PROCESSES, PROJECTS_BATCH
    global dirs_config
    global language_config
    global init_file_id
    global init_proj_id
    global FILE_projects_list

    config = ConfigParser()

    # parse existing file
    try:
        config.read(os.path.join(os.path.dirname(os.path.abspath(__file__)), config_filename))
    except IOError:
        print('ERROR - config.ini not found')
        sys.exit()

    # Get info from config.ini into global variables
    N_PROCESSES = config.getint('Main', 'N_PROCESSES')
    PROJECTS_BATCH = config.getint('Main', 'PROJECTS_BATCH')
    dirs_config["stats_folder"] = config.get('Folders/Files', 'PATH_stats_file_folder')
    dirs_config["bookkeeping_folder"] = config.get('Folders/Files', 'PATH_bookkeeping_proj_folder')
    dirs_config["tokens_file"] = config.get('Folders/Files', 'PATH_tokens_file_folder')

    # Reading Language settings
    language_config["separators"] = config.get('Language', 'separators').strip('"').split(' ')
    language_config["comment_inline"] = re.escape(config.get('Language', 'comment_inline'))
    language_config["comment_inline_pattern"] = language_config["comment_inline"] + '.*?$'
    language_config["comment_open_tag"] = re.escape(config.get('Language', 'comment_open_tag'))
    language_config["comment_close_tag"] = re.escape(config.get('Language', 'comment_close_tag'))
    language_config["comment_open_close_pattern"] = language_config["comment_open_tag"] + '.*?' + language_config["comment_close_tag"]
    language_config["file_extensions"] = config.get('Language', 'File_extensions').split(' ')
    FILE_projects_list = config.get("Main", "FILE_projects_list")

    # Reading config settings
    init_file_id = config.getint('Config', 'init_file_id')
    init_proj_id = config.getint('Config', 'init_proj_id')
    return language_config


def tokenize_files(file_string):
    times = {}
    file_hash, hash_time = hash_measuring_time(file_string)
    times["hash_time"] = hash_time

    lines = count_lines(file_string)
    file_string = "".join([s for s in file_string.splitlines(True) if s.strip()])
    loc = count_lines(file_string)

    file_string, regex_time = remove_comments(file_string, language_config)
    times["regex_time"] = regex_time

    file_string = "".join([s for s in file_string.splitlines(True) if s.strip()]).strip()
    sloc = count_lines(file_string, False)

    final_stats = (file_hash, lines, loc, sloc)
    # Rather a copy of the file string here for tokenization
    file_string_for_tokenization = file_string

    # Transform separators into spaces (remove them)
    start_time = dt.datetime.now()
    tokens_bag, total_tokens, unique_tokens = tokenize_string(file_string_for_tokenization, language_config)
    times["string_time"] = (dt.datetime.now() - start_time).microseconds

    tokens, tokens_time = format_tokens(tokens_bag)
    times["tokens_time"] = tokens_time

    tokens_hash, hash_time = hash_measuring_time(tokens)
    times["hash_time"] += hash_time

    final_tokens = (total_tokens, unique_tokens, tokens_hash, "@#@" + tokens)
    return final_stats, final_tokens, times


def process_file_contents(file_string, proj_id, file_id, container_path, file_path, file_bytes, FILE_tokens_file, FILE_stats_file):
    print(f"[INFO] Started process_file_contents on {file_path}")
    global file_count
    file_count += 1

    (final_stats, final_tokens, file_times) = tokenize_files(file_string)
    (file_hash, lines, LOC, SLOC) = final_stats
    (tokens_count_total, tokens_count_unique, tokens_hash, tokens) = final_tokens
    file_path = os.path.join(container_path, file_path)
    start_time = dt.datetime.now()
    FILE_stats_file.write(f'{proj_id},{file_id},"{file_path}","{file_hash}",{file_bytes},{lines},{LOC},{SLOC}\n')
    FILE_tokens_file.write(f'{proj_id},{file_id},{tokens_count_total},{tokens_count_unique}, {tokens_hash}{tokens}\n')
    file_times["write_time"] = (dt.datetime.now() - start_time).microseconds

    return file_times


def process_one_project(process_num, proj_id, proj_path, base_file_id, FILE_tokens_file, FILE_bookkeeping_proj, FILE_stats_file):
    print(f"[INFO] Starting  project <{proj_id},{proj_path}> (process {process_num})")
    p_start = dt.datetime.now()

    if not os.path.isfile(proj_path):
        print(f"[WARNING] Unable to open project <{proj_id},{proj_path}> (process {process_num})")
        return
    times = process_zip_ball(process_num, proj_id, proj_path, base_file_id, FILE_tokens_file, FILE_bookkeeping_proj, FILE_stats_file, language_config, process_file_contents)
    zip_time, file_time, string_time, tokens_time, write_time, hash_time, regex_time = (-1, -1, -1, -1, -1, -1, -1)
    if times is not None:
        zip_time = times["zip_time"]
        file_time = times["file_time"]
        string_time = times["string_time"]
        tokens_time = times["tokens_time"]
        write_time = times["write_time"]
        hash_time = times["hash_time"]
        regex_time = times["regex_time"]

    FILE_bookkeeping_proj.write(f'{proj_id},"{proj_path}"\n')

    p_elapsed = dt.datetime.now() - p_start
    print(f"[INFO] Project finished <{proj_id},{proj_path}> (process {process_num}))")
    print(f"[INFO]  ({process_num}): Total: {p_elapsed} ms")
    print(f"[INFO]      Zip: {zip_time} ms")
    print(f"[INFO]      Read: {file_time} ms")
    print(f"[INFO]      Separators: {string_time} ms")
    print(f"[INFO]      Tokens: {tokens_time} ms")
    print(f"[INFO]      Write: {write_time} ms")
    print(f"[INFO]      Hash: {hash_time} ms")
    print(f"[INFO]      regex: {regex_time} ms")
