#!/usr/bin/env python3

import datetime as dt
from argparse import ArgumentParser
import sys
import os
import re
import json
import zipfile


# Gets file name from file path with archive name
#
# @param file_path path to file in archive
# @return path to file in project
def get_file_name(file_path):
    result = re.sub(r"\.zip/[a-zA-Z0-9-.]+-master/", "/tree/master/", file_path.strip("\"").replace("--", "/"))
    result = re.sub(r"/.*/([^/]+/[^/]+/tree/master/)", r"\1", result)
    return result


# Reads lines from specified file
#
# @param filename file to read
# @return generator yielding lines
def get_file_lines(filename):
    with open(filename, "r", encoding="utf-8") as file_descr:
        for line in file_descr:
            yield line.strip("\n")


# Unoptimized merging results to find all files (y) similar to (x)
#
# @param pairs pairs from results file
# @return map (x): [all (y) similar to (x)]
def merge_results(pairs):
    res = {}
    for x, y in pairs:
        if not x in res:
            res[x] = [y]
        else:
            res[x].append(y)
    return res


# Parse results from results file
#
# @param results_file file with SourcererCC results
# @return map where keys are (block/file id) and value
# is list of ids which are clones of that block
def get_results(results_file):
    results_pairs = []
    for line in get_file_lines(results_file):
        _, code_id_1, _, code_id_2 = line.split(",")
        results_pairs.append((code_id_1, code_id_2))
    results = merge_results(results_pairs)
    return results


# Gets list of files in specified path with given extension
#
# @param path where to find files
# @param extension extension to filter files
# @return set of files with that extension in that directory
# (or that file if it is file with that extension)
def filter_files(path, extension):
    res = set()
    if os.path.isdir(path):
        filtered_files = filter(lambda x: x.endswith(extension), os.listdir(path))
        res.update(map(lambda x: os.path.join(path, x), filtered_files))
    elif os.path.isfile(path):
        res.add(path)
    else:
        print("ERROR: '{}' not found!".format(path))
        sys.exit()
    return res


# Gets project info from bookkeeping files
#
# @param bookkeeping_files_path path to bookkeeping file or directory
# @return list of maps {
#     project_id: project_id
#     project_path: path_to_project_archive
# }
def get_projects_info(bookkeeping_files_path):
    files = filter_files(bookkeeping_files_path, ".projs")
    projects_info = []
    for bookkeeping_file in files:
        for line in get_file_lines(bookkeeping_file):
            project_info = {
                "project_id": line.split(",")[0],
                "project_path": line.split(",")[1]
            }
            projects_info.append(project_info)
    return projects_info


# Parse stats
#
# @param stats_files_path file or directory with stats
# @param blocks_mode True if stats were made by tokenizer in block mode
# @return map where keys are block/file ids and values are maps such as
# in parse_file_line or parse_block_line functions
def get_stats_info(stats_files_path, blocks_mode):
    def parse_file_line(line_parts):
        return {
            "project_id": line_parts[0],
            "file_path": line_parts[2],
            "file_hash": line_parts[3],
            "file_size": line_parts[4],
            "lines": line_parts[5],
            "LOC": line_parts[6],
            "SLOC": line_parts[7]
        }
    def parse_block_line(line_parts):
        return {
            "project_id": line_parts[0],
            "block_hash": line_parts[2],
            "block_lines": line_parts[3],
            "block_LOC": line_parts[4],
            "block_SLOC": line_parts[5],
            "start_line": int(line_parts[6]),
            "end_line": int(line_parts[7])
        }
    files = filter_files(stats_files_path, ".stats")
    stats_info = {}
    for stats_file in files:
        for line in get_file_lines(stats_file):
            line_parts = line.split(",")
            stats = {}
            if blocks_mode:
                code_type = line_parts[0]
                code_id = line_parts[2]
                if code_type == "f":
                    stats = parse_file_line(line_parts[1:])
                elif code_type == "b":
                    stats = parse_block_line(line_parts[1:])
                    stats["relative_id"] = code_id[:5]
                    stats["file_id"] = code_id[5:]
            else:
                code_id = line_parts[1]
                stats = parse_file_line(line_parts)
            if code_id in stats_info:
                print("[NOTIFY] intersection on id {}".format(code_id))
                print("old: {}".format(stats_info[code_id]))
                print("new: {}".format(stats))
            stats_info[code_id] = stats
    return stats_info


# Reads specified lines of file from archive
#
# @param zip_file_path project zip archive
# @param start_line first line number of code to read
# @param end_line last line number of code to read, -1 for all lines
# @param source_file path to file to read
# @return lines of file joined with "\n"
def get_lines(zip_file_path, start_line, end_line, source_file):
    result = ""
    with zipfile.ZipFile(zip_file_path, "r") as repo:
        for code_file in repo.infolist():
            if source_file != code_file.filename:
                continue
            with repo.open(code_file) as f:
                result = f.read().decode("utf-8").split("\n")
    if end_line == -1:
        return "\n".join(result[start_line - 1:])
    return "\n".join(result[start_line - 1 : end_line])


# Prints nice formatted results
#
# @param results_file file with SourcererCC results
# @param stats_files file or directory with stats files
# @param blocks_mode True if tokenizer ran in block mode
# @return map with results parameters in following format:
#     in file mode:
#         "full_file_path": {
#             clones: [
#                 file: "full_file_path"
#                 SLOC: source_lines_of_code
#                 content: "file_content"
#             ]
#             SLOC: source_lines_of_code
#             content: "file_content"
#         }
#     in block mode:
#         "full_file_path": {
#             clones: [
#                 file: "full_file_path"
#                 start_line: first_line_of_block
#                 end_line: last_line_of_block
#                 content: "block_content"
#             ]
#             start_line: first_line_of_block
#             end_line: last_line_of_block
#             content: "block_content"
#         }
def print_results(results_file, stats_files, blocks_mode):
    stats = get_stats_info(stats_files, blocks_mode)
    results = get_results(results_file)
    full_results = {}
    formatted_titles = {}
    if blocks_mode:
        for code_id in stats.keys():
            if "start_line" in stats[code_id]:
                filename = get_file_name(stats[stats[code_id]["file_id"]]["file_path"])
                start_line = stats[code_id]["start_line"]
                end_line = stats[code_id]["end_line"]
                repo_zip_filename = stats[stats[code_id]["file_id"]]["file_path"][1:-1]
                source_file = repo_zip_filename[repo_zip_filename.index(".zip") + 5:]
                repo_zip_filename = repo_zip_filename[:repo_zip_filename.index(".zip") + 4]
                formatted_titles[code_id] = {
                    "file": filename,
                    "start_line": start_line,
                    "end_line": end_line,
                    "content": get_lines(repo_zip_filename, start_line, end_line, source_file)
                }
    else:
        for code_id in stats.keys():
            filename = get_file_name(stats[code_id]["file_path"])
            repo_zip_filename = stats[code_id]["file_path"][1:-1]
            source_file = repo_zip_filename[repo_zip_filename.index(".zip") + 5:]
            repo_zip_filename = repo_zip_filename[:repo_zip_filename.index(".zip") + 4]
            formatted_titles[code_id] = {
                "file": get_file_name(stats[code_id]["file_path"]),
                "SLOC": stats[code_id]["SLOC"],
                "content": get_lines(repo_zip_filename, 1, -1, source_file)
            }
    for code_id, code_id_list in results.items():
        full_results[formatted_titles[code_id]["file"]] = {
            "clones": list(map(lambda x: formatted_titles[x], code_id_list))
        }
        if blocks_mode:
            full_results[formatted_titles[code_id]["file"]]["start_line"] = formatted_titles[code_id]["start_line"]
            full_results[formatted_titles[code_id]["file"]]["end_line"] = formatted_titles[code_id]["end_line"]
            full_results[formatted_titles[code_id]["file"]]["content"] = formatted_titles[code_id]["content"]
        else:
            full_results[formatted_titles[code_id]["file"]]["SLOC"] = formatted_titles[code_id]["SLOC"]
            full_results[formatted_titles[code_id]["file"]]["content"] = formatted_titles[code_id]["content"]
    return full_results


# Prints project list from bookkeeping files
#
# @param bookkeeping_files file or directory with bookkeeping files
def print_projects_list(bookkeeping_files):
    projects_info = get_projects_info(bookkeeping_files)
    print(json.dumps(projects_info, indent=4))


# Print SourcererCC results in more comprehensive way than pairs of pairs of numbers
#
# @param block-mode must be True if tokenizer ran in block mode
# @param bookkeepingFiles file or directory with bookkeeping files(.projs)
# @param statsFiles file or directory with blocks and files stats(.stats)
# @param resultsFile file with results paris (first project id, first block/file, second project id, second block/file id)
# by default it is results.pairs
if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--block-mode", dest="blocks_mode", nargs="?", const=True, default=False, help="Specify if files produced in blocks-mode")
    parser.add_argument("-b", "--bookkeepingFiles", dest="bookkeeping_files", default=False, help="File or folder with bookkeeping files (*.projs).")
    parser.add_argument("-r", "--resultsFile", dest="results_file", default=False, help="File with results of SourcererCC (results.pairs).")
    parser.add_argument("-s", "--statsFiles", dest="stats_files", default=False, help="File or folder with stats files (*.stats).")

    options = parser.parse_args(sys.argv[1:])

    if len(sys.argv) == 1:
        print("No arguments were passed. Try running with '--help'.")
        sys.exit(0)

    p_start = dt.datetime.now()

    if options.results_file:
        if not options.stats_files:
            print("No stats files specified. Exiting")
            sys.exit(0)
        res = print_results(options.results_file, options.stats_files, options.blocks_mode)
        print(json.dumps(res, indent=4))
    elif options.bookkeeping_files:
        print_projects_list(options.bookkeeping_files)

    print("Processed printing in {}".format(dt.datetime.now() - p_start))
