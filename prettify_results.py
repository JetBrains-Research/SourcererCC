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


def squash_edges(edges):
    """Transforms list of edges into sparse graph.
    For example [(1, 2), (1, 3), (2, 3)] is transformed to
    {1: [2, 3], 2: [3]}

    Return map {(x): [all (y) similar to (x)]}

    Arguments:
    edges -- edges list
    """
    result = {vertex: [] for vertex, _ in edges}
    for parent, child in edges:
        result[parent].append(child)
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
    results = squash_edges(results_pairs)
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


def get_blocks_info(stats_files_path):
    """Parse stats.

    Return map where keys are block/file ids and values are maps such as
    in parse_file_line or parse_block_line functions

    Arguments:
    stats_files_path -- file or directory with stats
    """
    files = filter_files(stats_files_path, ".stats")
    stats_info = {}
    for stats_file in files:
        for line in get_file_lines(stats_file):
            line_parts = line.split(",")
            if line.startswith("b"):
                block_id = line_parts[2]
                stats_info[block_id] = {
                    "project_id": line_parts[1],
                    "block_hash": line_parts[3],
                    "block_lines": line_parts[4],
                    "block_LOC": line_parts[5],
                    "block_SLOC": line_parts[6],
                    "start_line": int(line_parts[7]),
                    "end_line": int(line_parts[8]),
                    "relative_id": block_id[:5],
                    "file_id": block_id[5:]
                }
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
            with repo.open(code_file) as code_file:
                result = code_file.read().decode("utf-8").split("\n")
    return "\n".join(result[start_line - 1 : end_line])

def split_zip_file_path(file_path):
    ext_index = file_path.index(".zip") + len(".zip")
    return file_path[:ext_index], file_path[ext_index + 1:]


def transform_results(results_file, blocks_map):
    """Transform results pairs using stats.

    Return map with results parameters in following format:
        "{{full_file_path}}": {
            clones: [
                file: "{{full_file_path}}",
                start_line: {{first_line_of_block}},
                end_line: {{last_line_of_block}},
                content: "{{block_content}}"
            ],
            start_line: {{first_line_of_block}},
            end_line: {{last_line_of_block}},
            content: "{{block_content}}"
        }

    Arguments:
    results_file -- file with SourcererCC results
    blocks_map -- map in format:
        {{block_id}}: {
            "file": "{{filename}}",
            "start_line": {{start_line}},
            "end_line": {{end_line}},
            "content": "{{code_content}}"
        }
    """
    full_results = {}
    results = get_results(results_file)
    print(f"results:\n{json.dumps(results, indent=4)}")
    for code_id, code_id_list in results.items():
        full_results[blocks_map[code_id]["file"]] = {
            "clones": list(map(lambda x: blocks_map[x], code_id_list))
        }
        for key in ["start_line", "end_line", "content"]:
            full_results[blocks_map[code_id]["file"]][key] = blocks_map[code_id][key]
    return full_results


def results_to_map(results_file, stats_files):
    """Transform results pairs using stats.

    Return map with results parameters in following format:
        "{{full_file_path}}": {
            clones: [
                file: "{{full_file_path}}",
                start_line: {{first_line_of_block}},
                end_line: {{last_line_of_block}},
                content: "{{block_content}}"
            ],
            start_line: {{first_line_of_block}},
            end_line: {{last_line_of_block}},
            content: "{{block_content}}"
        }

    Arguments:
    results_file -- file with SourcererCC results
    stats_files -- file or folder with stats (*.stats) files
    """
    stats = get_blocks_info(stats_files)
    formatted_titles = {}
    for block_id, code_stat in stats.items():
        file_path = stats[code_stat["file_id"]]["file_path"]
        filename = get_file_name(file_path)
        repo_zip_filename, source_file = split_zip_file_path(file_path.strip("\""))
        start_line = code_stat["start_line"]
        end_line = code_stat["end_line"]
        code_content = get_lines(repo_zip_filename, start_line, end_line, source_file)
        formatted_titles[block_id] = {
            "file": filename,
            "start_line": start_line,
            "end_line": end_line,
            "content": code_content
        }
    return transform_results(results_file, formatted_titles)


# Print SourcererCC results conveniently
#
# statsFiles -- file or directory with blocks and files stats(.stats)
# resultsFile -- file with results paris (first project id, first block/file,
#     second project id, second block/file id) usually it is results.pairs
if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-r", "--resultsFile", dest="results_file",\
        default=False, help="File with results of SourcererCC (results.pairs).")
    parser.add_argument("-s", "--statsFiles", dest="stats_files",\
        default=False, help="File or folder with stats files (*.stats).")

    if len(sys.argv) == 1:
        print("No arguments were passed. Try running with '--help'.")
        sys.exit(0)

    options = parser.parse_args(sys.argv[1:])
    results_file = options.results_file
    stats_files = options.stats_files

    if not results_file:
        print("No results files specified. Exiting")
        sys.exit(0)

    if not stats_files:
        print("No stats files specified. Exiting")
        sys.exit(0)

    p_start = dt.datetime.now()
    print("Starting prettify_results with parameters:")
    print(f"    stats_files: {stats_files}")
    print(f"    results_file: {results_file}")

    results_map = results_to_map(options.results_file, options.stats_files)
    print(json.dumps(results_map, indent=4))

    print(f"Processed printing in {dt.datetime.now() - p_start}")
