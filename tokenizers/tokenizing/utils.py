import hashlib
import os
import zipfile
import datetime as dt
import re
import collections


def process_zip_ball(process_num, proj_id, zip_file, base_file_id, language_config, callback, out_files, inner_config, file_count):
    print(f"[INFO] Started zip ball {zip_file}")
    times = {
        "zip_time": 0,
        "file_time": 0,
        "string_time": 0,
        "tokens_time": 0,
        "write_time": 0,
        "hash_time": 0,
        "regex_time": 0
    }
    try:
        with zipfile.ZipFile(zip_file, 'r') as my_file:
            for code_file in my_file.infolist():
                if not os.path.splitext(code_file.filename)[1] in language_config["file_extensions"]:
                    continue

                file_id = process_num * inner_config["MULTIPLIER"] + base_file_id + file_count
                file_bytes = str(code_file.file_size)
                file_path = code_file.filename
                full_code_file_path = os.path.join(zip_file, file_path)

                z_time = dt.datetime.now()
                try:
                    my_zip_file = my_file.open(file_path, 'r')
                except Exception as e:
                    print(f"[WARNING] Unable to open file <{full_code_file_path}> (process {process_num})")
                    print(e)
                    continue
                times["zip_time"] += (dt.datetime.now() - z_time).microseconds

                if my_zip_file is None:
                    print(f"[WARNING] Opened file is None <{full_code_file_path}> (process {process_num})")
                    continue

                file_string = ""
                f_time = dt.datetime.now()
                try:
                    file_string = my_zip_file.read().decode("utf-8")
                except:
                    print(f"[WARNING] File {file_path} can't be read")
                times["file_time"] += (dt.datetime.now() - f_time).microseconds

                file_times = callback(file_string, proj_id, file_id, zip_file, file_path, file_bytes, out_files[0], out_files[2])
                for time_name, time in file_times.items():
                    times[time_name] += time
    except zipfile.BadZipFile as e:
        print(f"[ERROR] Incorrect zip file {zip_file}")

    print(f"[INFO] Successfully ran process_zip_ball {zip_file}")
    return times

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
