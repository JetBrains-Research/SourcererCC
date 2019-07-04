#!/usr/bin/env python3
"""This module print results of SourcererCC in nicer way when ran.
Other functions are used to transform SourcererCC output to json format for
further processing."""

import datetime as dt
from argparse import ArgumentParser
import sys
import os
import re
import json
import zipfile


def get_file_name(file_path):
    """Get file name from path of archive.

    Arguments:
    file_path -- path to file in archive
    """
    full_path = file_path.strip("\"").replace("--", "/")
    result = re.sub(r"\.zip/[a-zA-Z0-9-.]+-master/", "/tree/master/", full_path)
    result = re.sub(r"/.*/([^/]+/[^/]+/tree/master/)", r"\1", result)
    return result


def get_file_lines(filename):
    """Read lines from specified file. Return generator yielding lines.

    Arguments:
    filename -- file to read
    """
    with open(filename, "r", encoding="utf-8") as file_descr:
        for line in file_descr:
            yield line.strip("\n")


def merge_results(pairs):
    """Merge results to find all files (y) similar to (x).

    Return map {(x): [all (y) similar to (x)]}

    Arguments:
    pairs -- pairs from results file
    """
    result = {}
    for x, y in pairs:
        if not x in result:
            result[x] = [y]
        else:
            result[x].append(y)
    return result


def get_results(results_file):
    """Parse results from results file.

    Return map where keys are (block/file id) and value
    is list of ids which are clones of that block

    Arguments:
    results_file -- file with SourcererCC results
    """
    results_pairs = []
    for line in get_file_lines(results_file):
        _, code_id_1, _, code_id_2 = line.split(",")
        results_pairs.append((code_id_1, code_id_2))
    results = merge_results(results_pairs)
    return results


def filter_files(path, extension):
    """Get list of files in specified path with given extension.
    Return set of files with that extension in that directory
    (or that file if it is file with that extension)

    Arguments:
    path -- where to find files
    extension -- extension to filter files
    """
    res = set()
    if os.path.isdir(path):
        files_list = filter(lambda x: x.endswith(extension), os.listdir(path))
        res.update(map(lambda x: os.path.join(path, x), files_list))
    elif os.path.isfile(path):
        res.add(path)
    else:
        print("ERROR: '{}' not found!".format(path))
        sys.exit()
    return res


def get_projects_info(bookkeeping_files_path):
    """Get project info from bookkeeping files.
    Return list of maps {
        project_id: project_id
        project_path: path_to_project_archive
    }

    Arguments:
    bookkeeping_files_path -- path to bookkeeping file or directory
    """
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


def get_stats_info(stats_files_path, blocks_mode):
    """Parse stats.

    Return map where keys are block/file ids and values are maps such as
    in parse_file_line or parse_block_line functions

    Arguments:
    stats_files_path -- file or directory with stats
    blocks_mode -- True if stats were made by tokenizer in block mode
    """
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


def get_lines(zip_file_path, start_line, end_line, source_file):
    """Read specified lines of file from archive.

    Arguments:
    zip_file_path -- project zip archive
    start_line -- first line number of code to read
    end_line -- last line number of code to read, -1 for all lines
    source_file -- path to file to read
    """
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


def print_results(results_file, stats_files, blocks_mode):
    """Print nice formatted results.

    Return map with results parameters in following format:
        in file mode:
            "full_file_path": {
                clones: [
                    file: "full_file_path"
                    SLOC: source_lines_of_code
                    content: "file_content"
                ]
                SLOC: source_lines_of_code
                content: "file_content"
            }
        in block mode:
            "full_file_path": {
                clones: [
                    file: "full_file_path"
                    start_line: first_line_of_block
                    end_line: last_line_of_block
                    content: "block_content"
                ]
                start_line: first_line_of_block
                end_line: last_line_of_block
                content: "block_content"
            }

    Arguments:
    results_file -- file with SourcererCC results
    stats_files -- file or directory with stats files
    blocks_mode -- True if tokenizer ran in block mode
    """
    stats = get_stats_info(stats_files, blocks_mode)
    results = get_results(results_file)
    full_results = {}
    formatted_titles = {}
    if blocks_mode:
        for code_id, code_stat in stats.items():
            if "start_line" in code_stat:
                file_path = stats[code_stat["file_id"]]["file_path"]
                filename = get_file_name(file_path)
                start_line = code_stat["start_line"]
                end_line = code_stat["end_line"]
                repo_zip_filename = file_path[1:-1]
                ext_index = repo_zip_filename.index(".zip")
                source_file = repo_zip_filename[ext_index + 5:]
                repo_zip_filename = repo_zip_filename[:ext_index + 4]
                code_content = get_lines(repo_zip_filename, start_line, end_line, source_file)
                formatted_titles[code_id] = {
                    "file": filename,
                    "start_line": start_line,
                    "end_line": end_line,
                    "content": code_content
                }
    else:
        for code_id, code_stat in stats.items():
            filename = get_file_name(code_stat["file_path"])
            repo_zip_filename = code_stat["file_path"][1:-1]
            ext_index = repo_zip_filename.index(".zip")
            source_file = repo_zip_filename[ext_index + 5:]
            repo_zip_filename = repo_zip_filename[:ext_index + 4]
            code_content = get_lines(repo_zip_filename, 1, -1, source_file)
            formatted_titles[code_id] = {
                "file": get_file_name(code_stat["file_path"]),
                "SLOC": code_stat["SLOC"],
                "content": code_content
            }
    print("results:")
    for code_id, code_id_list in results.items():
        print(f"{code_id}: {code_id_list}")
    for code_id, code_id_list in results.items():
        print(f"code_id: {code_id}")
        print(f"code_id_list: {code_id_list}")
        print("formatted_titles:")
        for a, b in formatted_titles.items():
            print(f"{a}: {{")
            for x, y in b.items():
                if len(y) < 100:
                    print(f"{x}: {y},")
            print("}")
        full_results[formatted_titles[code_id]["file"]] = {
            "clones": list(map(lambda x: formatted_titles[x], code_id_list))
        }
        if blocks_mode:
            for key in ["start_line", "end_line", "content"]:
                full_results[formatted_titles[code_id]["file"]][key] = formatted_titles[code_id][key]
        else:
            for key in ["SLOC", "content"]:
                full_results[formatted_titles[code_id]["file"]][key] = formatted_titles[code_id][key]
    return full_results


def print_projects_list(bookkeeping_files):
    """Print project list from bookkeeping files.

    Arguments:
    bookkeeping_files -- file or directory with bookkeeping files
    """
    projects_info = get_projects_info(bookkeeping_files)
    print(json.dumps(projects_info, indent=4))


# Print SourcererCC results conveniently
#
# block-mode -- must be True if tokenizer ran in block mode
# bookkeepingFiles -- file or directory with bookkeeping files(.projs)
# statsFiles -- file or directory with blocks and files stats(.stats)
# resultsFile -- file with results paris (first project id, first block/file,
# second project id, second block/file id) usually it is results.pairs
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
        json_string = print_results(options.results_file, options.stats_files, options.blocks_mode)
        print(json.dumps(json_string, indent=4))
    elif options.bookkeeping_files:
        print_projects_list(options.bookkeeping_files)

    print("Processed printing in {}".format(dt.datetime.now() - p_start))
