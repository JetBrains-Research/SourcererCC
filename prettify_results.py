#!/usr/bin/env python3

import datetime as dt
from argparse import ArgumentParser
import sys
import os
import re
import json
import zipfile


def get_file_name(file_path):
    result = re.sub(r"\.zip/[a-zA-Z0-9-.]+-master/", "/tree/master/", file_path.strip("\"").replace("--", "/"))
    result = re.sub(r"/.*/([^/]+/[^/]+/tree/master/)", r"\1", result)
    return result


def get_file_lines(filename):
    with open(filename, "r", encoding="utf-8") as file_descr:
        for line in file_descr:
            yield line.strip("\n")


def merge_results(pairs):
    res = {}
    for x, y in pairs:
        if not x in res:
            res[x] = [y]
        else:
            res[x].append(y)
    return res


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


def get_results(results_file):
    results_pairs = []
    for line in get_file_lines(results_file):
        code_id_1 = line.split(",")[1]
        code_id_2 = line.split(",")[3]
        results_pairs.append((code_id_1, code_id_2))
    results = merge_results(results_pairs)
    return results


def get_lines(zip_file_path, start_line, end_line, source_file):
    result = ""
    with zipfile.ZipFile(zip_file_path, "r") as repo:
        for code_file in repo.infolist():
            if source_file != code_file.filename:
                continue
            with repo.open(code_file) as f:
                result = f.read().decode("utf-8").split("\n")
    return "\n".join(result[start_line - 1 : end_line])


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
                "content": get_lines(repo_zip_filename, 1, int(stats[code_id]["SLOC"]), source_file)
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


def print_projects_list(bookkeeping_files):
    projects_info = get_projects_info(bookkeeping_files)
    print(json.dumps(projects_info, indent=4))


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
