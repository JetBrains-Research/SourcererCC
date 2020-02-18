from configparser import ConfigParser
import datetime as dt
import os
import re
import sys
from typing import List, Tuple, Union
import zipfile

from .function_extractor import FunctionExtractor
from .utils import count_lines, hash_measuring_time, remove_comments, tokenize_string, format_tokens

# TODO: fix style.


def read_language_config(config):
    result = {}
    result["separators"] = config.get('Language', 'separators').strip('"').split(' ')
    result["comment_inline"] = re.escape(config.get('Language', 'comment_inline'))
    result["comment_open_tag"] = re.escape(config.get('Language', 'comment_open_tag'))
    result["comment_close_tag"] = re.escape(config.get('Language', 'comment_close_tag'))
    result["extensions"] = config.get('Language', 'File_extensions').split(' ')

    result["comment_inline_pattern"] = result["comment_inline"] + '.*?$'
    result["comment_open_close_pattern"] = result["comment_open_tag"] + '.*?' + result["comment_close_tag"]
    return result


def read_inner_config(config):
    result = {}
    # Get info from config.ini into global variables
    result["N_PROCESSES"] = config.getint('Main', 'N_PROCESSES')
    result["PROJECTS_BATCH"] = config.getint('Main', 'PROJECTS_BATCH')
    result["FILE_projects_list"] = config.get('Main', 'FILE_projects_list')
    # Reading config settings
    result["init_file_id"] = config.getint('Config', 'init_file_id')
    result["init_proj_id"] = config.getint('Config', 'init_proj_id')
    # flag before proj_id
    result["proj_id_flag"] = config.getint('Config', 'init_proj_id')
    return result


def read_dirs_config(config):
    result = {}
    result["stats_folder"] = config.get('Folders/Files', 'PATH_stats_folder')
    result["bookkeeping_folder"] = config.get('Folders/Files', 'PATH_bookkeeping_folder')
    result["tokens_folder"] = config.get('Folders/Files', 'PATH_tokens_folder')
    return result


class Tokenizer():
    def __init__(self, config_filename):
        config = ConfigParser()
        try:
            config.read(config_filename)
        except IOError:
            print(f"[ERROR] - Config file {config_filename} is not found")
            sys.exit(1)

        self.language_config = read_language_config(config)
        self.inner_config = read_inner_config(config)
        self.inner_config["MULTIPLIER"] = 50000000
        self.dirs_config = read_dirs_config(config)
        self.file_count = 0
        self._lang = None

    @property
    def lang(self) -> str:
        """
        Programming language (based on heuristics).
        # TODO: replace with proper language classification.
        :return:  language.
        """
        if self._lang is None:
            if ".java" in self.language_config["extensions"]:
                self._lang = "java"
                return self._lang
            elif ".cs" in self.language_config["extensions"]:
                self._lang = "csharp"
                return self._lang
            cpp_extensions = ".cpp .h .C .hpp .c++ .cxx .CPP".split()
            for extension in cpp_extensions:
                if extension in self.language_config["extensions"]:
                    self._lang = "cpp"
                    return self._lang
            c_extensions = ".c .h .cc".split()
            for extension in c_extensions:
                if extension in self.language_config["extensions"]:
                    self._lang = "c"
                    return self._lang
        return self._lang

    def get_configs(self):
        return self.language_config, self.inner_config, self.dirs_config

    def get_file_count(self):
        return self.file_count

    def increase_file_count(self, files_number):
        self.file_count += files_number

    def get_lines_stats(self, string):
        def is_line_empty(line):
            return line.strip() == ""
        def remove_lines(string, predicate):
            return "\n".join(filter(lambda s: not predicate(s), string.splitlines()))

        lines = count_lines(string)

        string_lines = remove_lines(string, is_line_empty)
        loc = count_lines(string_lines)

        string_lines, remove_comments_time = remove_comments(string_lines, self.language_config)
        code = remove_lines(string_lines, is_line_empty)
        sloc = count_lines(code, False)

        return code, lines, loc, sloc, remove_comments_time


    def process_tokenizer(self, string):
        string_hash, hash_time = hash_measuring_time(string)

        string, lines, loc, sloc, remove_comments_time = self.get_lines_stats(string)

        # get tokens bag
        tokens_bag, tokens_count_total, tokens_count_unique = tokenize_string(string, self.language_config)
        tokens, format_time = format_tokens(tokens_bag)  # make formatted string with tokens

        tokens_hash, hash_delta_time = hash_measuring_time(tokens)
        hash_time += hash_delta_time

        return (string_hash, lines, loc, sloc), (tokens_count_total, tokens_count_unique, tokens_hash, tokens), {
            "tokens_time": format_time,
            "hash_time": hash_time,
            "string_time": remove_comments_time
        }

    def parse_blocks(self, content: Union[bytes, str]) -> Tuple[List[Tuple[int, int]], List[bytes], List[str]]:
        """
        Parse source code and extract functions, start & end lines,
        :param content: content of file.
        :return: 3 lists: each element in first list contains start and end line number,
                          second list contains function bodies,
                          third list should contain function names/metadata.
        """
        try:
            block_linenos, blocks = FunctionExtractor.get_functions(content=content, lang=self.lang)
            # TODO: add functionality to extract function metadata
            return block_linenos, blocks, "FIXME"
        except Exception:
            # dummy fix to make pipeline resistant to bugs :)
            return None, None, None

    def tokenize_blocks(self, file_string, file_path):
        times = {
            "zip_time": 0,
            "file_time": 0,
            "string_time": 0,
            "tokens_time": 0,
            "hash_time": 0,
            "regex_time": 0
        }

        block_linenos, blocks, function_name = self.parse_blocks(file_string)
        if block_linenos is None:
            print(f"[INFO] Incorrect file {file_path}")
            return None, None, None

        file_hash, hash_time = hash_measuring_time(file_string)
        file_string, lines, LOC, SLOC, re_time = self.get_lines_stats(file_string)
        times["regex_time"] += re_time

        blocks_data = []
        for i, block_string in enumerate(blocks):
            (start_line, end_line) = block_linenos[i]

            stats, block_tokens, tokenizer_times = self.process_tokenizer(block_string)
            block_stats = (stats, start_line, end_line)

            for time_name, time in tokenizer_times.items():
                times[time_name] += time
            blocks_data.append((block_tokens, block_stats, function_name[i]))
        times["hash_time"] += hash_time
        return (file_hash, lines, LOC, SLOC), blocks_data, times


    def process_file_contents(self, file_string, proj_id, file_id, container_path, file_path, file_bytes, out_files):
        (tokens_file, _, stats_file) = out_files

        self.file_count += 1

        file_path = os.path.join(container_path, file_path)
        (final_stats, blocks_data, times) = self.tokenize_blocks(file_string, file_path)

        if (final_stats is None) or (blocks_data is None) or (times is None):
            return {}

        if len(blocks_data) > 90000:
            print(f"[WARNING] File {file_path} has {len(blocks_data)} blocks, more than 90000. Range MUST be increased")
            return {}

        # file stats start with a letter 'f'
        (file_hash, lines, LOC, SLOC) = final_stats
        stats_file.write(f'f,{proj_id},{file_id},"{file_path}","","{file_hash}",{file_bytes},{lines},{LOC},{SLOC}\n')

        start_time = dt.datetime.now()
        try:
            for relative_id, block_data in enumerate(blocks_data, 10000):
                (block_tokens, blocks_stats, experimental_value) = block_data
                block_id = f"{relative_id}{file_id}"

                (tokens_count_total, tokens_count_unique, token_hash, tokens) = block_tokens
                (stats, start_line, end_line) = blocks_stats
                (block_hash, block_lines, block_LOC, block_SLOC) = stats

                # Adjust the blocks stats written to the files, file stats start with a letter 'b'
                stats_file.write(f'b,{proj_id},{block_id},"{block_hash}",{block_lines},{block_LOC},{block_SLOC},{start_line},{end_line}\n')
                tokens_file.write(f'{proj_id},{block_id},{tokens_count_total},{tokens_count_unique},{experimental_value.replace(",", ";")},{token_hash}@#@{tokens}\n')
        except Exception as e:
            print("[WARNING] Error on step3 of process_file_contents")
            print(e)
        times["write_time"] = (dt.datetime.now() - start_time).microseconds
        return times


    def print_times(self, project_info, elapsed, times):
        print(f"[INFO] Finished {project_info}")
        print(f"[INFO] Total: {elapsed} ms")
        for time_name, time in times.items():
            print(f"[INFO]      {time_name}: {time} ms")


    def process_zip_ball(self, process_num, proj_id, zip_file, base_file_id, out_files):
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
                    if not os.path.splitext(code_file.filename)[1] in self.language_config["extensions"]:
                        continue

                    file_id = process_num * self.inner_config["MULTIPLIER"] + base_file_id + self.file_count
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

                    file_times = self.process_file_contents(file_string, proj_id, file_id, zip_file, file_path, file_bytes, out_files)
                    for time_name, time in file_times.items():
                        times[time_name] += time
        except zipfile.BadZipFile as _:
            print(f"[ERROR] Incorrect zip file {zip_file}")

        return times


    def process_one_project(self, process_num, proj_id, proj_path, base_file_id, out_files):
        proj_id_flag = self.inner_config["proj_id_flag"]

        project_info = f"project <id: {proj_id}, path: {proj_path}> (process {process_num})"
        print(f"[INFO] Starting  {project_info}")

        start_time = dt.datetime.now()
        proj_id = f"{proj_id_flag}{proj_id}"
        if not os.path.isfile(proj_path):
            print(f"[WARNING] Unable to open {project_info}")
            return
        times = self.process_zip_ball(process_num, proj_id, proj_path, base_file_id, out_files)
        _, bookkeeping_file, _ = out_files
        bookkeeping_file.write(f'{proj_id},"{proj_path}"\n')

        elapsed_time = dt.datetime.now() - start_time
        self.print_times(project_info, elapsed_time, times)
