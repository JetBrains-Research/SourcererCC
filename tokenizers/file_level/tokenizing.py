import datetime as dt
import zipfile
import re
import collections
import hashlib
import os
from configparser import ConfigParser

MULTIPLIER = 50000000

N_PROCESSES = 2
PROJECTS_BATCH = 20

dirs_config = {}
dirs_config["bookkeeping_folder"] = 'bookkeeping_projs'
dirs_config["tokens_file"] = 'files_tokens'
FILE_projects_list = "project-list.txt"
language_config = {}

file_count = 0


def read_config():
    global N_PROCESSES, PROJECTS_BATCH
    global dirs_config
    global language_config
    global init_file_id
    global init_proj_id
    global FILE_projects_list

    config = ConfigParser()

    # parse existing file
    try:
        config.read(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.ini'))
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


def count_lines(string, count_empty = True):
    result = string.count('\n')
    if not string.endswith('\n') and (count_empty or string != ""):
        result += 1
    return result


def md5_hash(string):
    m = hashlib.md5()
    m.update(string.encode("utf-8"))
    return m.hexdigest()


def tokenize_files(file_string):
    times = {}
    h_time = dt.datetime.now()
    file_hash = md5_hash(file_string)
    times["hash_time"] = (dt.datetime.now() - h_time).microseconds

    lines = count_lines(file_string)
    file_string = "".join([s for s in file_string.splitlines(True) if s.strip()])

    loc = count_lines(file_string)

    start_time = dt.datetime.now()
    # Remove tagged comments
    file_string = re.sub(language_config["comment_open_close_pattern"], '', file_string, flags=re.DOTALL)
    # Remove end of line comments
    file_string = re.sub(language_config["comment_inline_pattern"], '', file_string, flags=re.MULTILINE)
    times["regex_time"] = (dt.datetime.now() - start_time).microseconds

    file_string = "".join([s for s in file_string.splitlines(True) if s.strip()]).strip()
    sloc = file_string.count('\n')
    if file_string != '' and not file_string.endswith('\n'):
        sloc += 1
    final_stats = (file_hash, lines, loc, sloc)
    # Rather a copy of the file string here for tokenization
    file_string_for_tokenization = file_string

    # Transform separators into spaces (remove them)
    start_time = dt.datetime.now()
    for x in language_config["separators"]:
        file_string_for_tokenization = file_string_for_tokenization.replace(x, ' ')
    times["string_time"] = (dt.datetime.now() - start_time).microseconds

    # Create a list of tokens
    file_string_for_tokenization = file_string_for_tokenization.split()
    # Total number of tokens
    tokens_count_total = len(file_string_for_tokenization)
    # Count occurrences
    file_string_for_tokenization = collections.Counter(file_string_for_tokenization)
    # Converting Counter to dict because according to StackOverflow is better
    file_string_for_tokenization = dict(file_string_for_tokenization)
    # Unique number of tokens
    tokens_count_unique = len(file_string_for_tokenization)

    # SourcererCC formatting
    start_time = dt.datetime.now()
    tokens = '@#@'
    tokens += ','.join(['{}@@::@@{}'.format(k, v) for k, v in file_string_for_tokenization.items()])
    times["tokens_time"] = (dt.datetime.now() - start_time).microseconds

    start_time = dt.datetime.now()
    tokens_hash = md5_hash(tokens)
    times["hash_time"] += (dt.datetime.now() - start_time).microseconds

    final_tokens = (tokens_count_total, tokens_count_unique, tokens_hash, tokens)
    return final_stats, final_tokens, times


def process_file_contents(file_string, proj_id, file_id, container_path, file_path, file_bytes, FILE_tokens_file, FILE_stats_file):
    global file_count

    file_count += 1
    (final_stats, final_tokens, file_times) = tokenize_files(file_string)
    (file_hash, lines, LOC, SLOC) = final_stats
    (tokens_count_total, tokens_count_unique, token_hash, tokens) = final_tokens
    file_path = os.path.join(container_path, file_path)
    start_time = dt.datetime.now()
    FILE_stats_file.write(f'{proj_id},{file_id},"{file_path}","{file_hash}",{file_bytes},{lines},{LOC},{SLOC}\n')
    FILE_tokens_file.write(f'{proj_id},{file_id},{tokens_count_total},{tokens_count_unique}, {tokens_hash}{tokens}\n')
    file_times["write_time"] = (dt.datetime.now() - start_time).microseconds

    return file_times


def process_zip_ball(process_num, zip_file, proj_id, proj_path, base_file_id, FILE_tokens_file, FILE_bookkeeping_proj, FILE_stats_file):
    times = {
        "zip_time": 0,
        "file_time": 0,
        "string_time": 0,
        "tokens_time": 0,
        "write_time": 0,
        "hash_time": 0,
        "regex_time": 0
    }
    print(f"[INFO] Attempting to process_zip_ball {zip_file}")
    with zipfile.ZipFile(proj_path, 'r') as my_file:
        for code_file in my_file.infolist():
            if not os.path.splitext(code_file.filename)[1] in language_config["file_extensions"]:
                continue

            file_id = process_num * MULTIPLIER + base_file_id + file_count
            file_bytes = str(code_file.file_size)
            file_path = code_file.filename
            full_code_file_path = os.path.join(proj_path, file_path)

            z_time = dt.datetime.now()
            try:
                my_zip_file = my_file.open(file_path, 'r')
            except:
                print(f"[WARNING] Unable to open file <{full_code_file_path}> (process {process_num})")
                break
            times["zip_time"] += (dt.datetime.now() - z_time).microseconds

            if my_zip_file is None:
                print(f"[WARNING] Opened file is None <{full_code_file_path}> (process {process_num})")
                break

            f_time = dt.datetime.now()
            file_string = my_zip_file.read().decode("utf-8")
            times["file_time"] += (dt.datetime.now() - f_time).microseconds

            file_times = process_file_contents(file_string, proj_id, file_id, zip_file, file_path, file_bytes, FILE_tokens_file, FILE_stats_file)
            for time_name, time in file_times.items():
                times[time_name] += time
    print("[INFO] Successfully ran process_zip_ball {zip_file}")
    return times


def process_one_project(process_num, proj_id, proj_path, base_file_id, FILE_tokens_file, FILE_bookkeeping_proj, FILE_stats_file):
    print(f"[INFO] Starting  project <{proj_id},{proj_path}> (process {process_num})")
    p_start = dt.datetime.now()
    zip_file = proj_path
    times = process_zip_ball(process_num, zip_file, proj_id, proj_path, base_file_id, FILE_tokens_file, FILE_bookkeeping_proj, FILE_stats_file)
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