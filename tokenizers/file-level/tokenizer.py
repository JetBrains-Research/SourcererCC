#!/usr/bin/env python3

import collections
import datetime as dt
import hashlib
import os
import re
import sys
import zipfile
from configparser import ConfigParser
from multiprocessing import Process, Queue

from tokenizing import *


def process_projects(process_num, list_projects, base_file_id, global_queue):
    file_files_stats_file = os.path.join(dirs_config["stats_folder"], f'files-stats-{process_num}.stats')
    file_bookkeeping_proj_name = os.path.join(dirs_config["bookkeeping_folder"], f'bookkeeping-proj-{process_num}.projs')
    file_files_tokens_file = os.path.join(dirs_config["tokens_file"], f'files-tokens-{process_num}.tokens')

    global file_count
    file_count = 0
    with open(file_files_tokens_file, 'a+', encoding="utf-8") as FILE_tokens, open(file_bookkeeping_proj_name, 'a+', encoding="utf-8") as FILE_bookkeeping, open(file_files_stats_file, 'a+', encoding="utf-8") as FILE_stats:
        print(f"[INFO] Process {process_num} starting")
        p_start = dt.datetime.now()
        for proj_id, proj_path in list_projects:
            process_one_project(process_num, str(proj_id), proj_path, base_file_id, FILE_tokens, FILE_bookkeeping, FILE_stats)

    p_elapsed = (dt.datetime.now() - p_start).seconds
    print(f"[INFO] Process {process_num} finished. {file_count} files in {p_elapsed} sec")

    # Let parent know
    global_queue.put((process_num, file_count))
    sys.exit(0)


def start_child(processes, global_queue, proj_paths, batch):
    # This is a blocking get. If the queue is empty, it waits
    pid, n_files_processed = global_queue.get()
    # OK, one of the processes finished. Let's get its data and kill it
    kill_child(processes, pid, n_files_processed)

    # Get a new batch of project paths ready
    paths_batch = proj_paths[:batch]
    del proj_paths[:batch]

    print("Starting new process %s" % pid)
    p = Process(name=f'Process {pid}', target=process_projects, args=(pid, paths_batch, processes[pid][1], global_queue))
    processes[pid][0] = p
    p.start()


def kill_child(processes, pid, n_files_processed):
    global file_count
    file_count += n_files_processed
    if processes[pid][0] is not None:
        processes[pid][0] = None
        processes[pid][1] += n_files_processed
        print(f"Process {pid} finished, {n_files_processed} files processed (total by that process: {processes[pid][1]}). Current total: {file_count}")


def active_process_count(processes):
    return len(list(filter(lambda p: p[0] is not None, processes)))


if __name__ == '__main__':
    try:
        read_config()
    except Exception as e:
        print(e)
        sys.exit()
    p_start = dt.datetime.now()

    proj_paths = []
    with open(FILE_projects_list, "r", encoding="utf-8") as f:
        proj_paths = f.read().split("\n")
    proj_paths = list(enumerate(proj_paths, start=1))

    if os.path.exists(dirs_config["stats_folder"]) or os.path.exists(dirs_config["bookkeeping_folder"]) or os.path.exists(dirs_config["tokens_file"]):
        missing_files = filter(os.path.exists, [dirs_config["stats_folder"], dirs_config["bookkeeping_folder"], dirs_config["tokens_file"]])
        print('ERROR - Folder [' + '] or ['.join(missing_files) + '] already exists!')
        sys.exit(1)
    else:
        os.makedirs(dirs_config["stats_folder"])
        os.makedirs(dirs_config["bookkeeping_folder"])
        os.makedirs(dirs_config["tokens_file"])

    # Multiprocessing with N_PROCESSES
    # [process, file_count]
    processes = [[None, init_file_id] for i in range(N_PROCESSES)]
    # The queue for processes to communicate back to the parent (this process)
    # Initialize it with N_PROCESSES number of (process_id, n_files_processed)
    global_queue = Queue()
    for i in range(N_PROCESSES):
        global_queue.put((i, 0))

    print("*** Starting regular projects...")
    while len(proj_paths) > 0:
        start_child(processes, global_queue, proj_paths, PROJECTS_BATCH)

    print("*** No more projects to process. Waiting for children to finish...")
    while active_process_count(processes) > 0:
        pid, n_files_processed = global_queue.get()
        kill_child(processes, pid, n_files_processed)

    p_elapsed = dt.datetime.now() - p_start
    print(f"*** All done. {file_count} files in {p_elapsed}")
