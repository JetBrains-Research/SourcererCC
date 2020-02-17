#!/usr/bin/env python3

import datetime as dt
import os
import sys
from multiprocessing import Process, Queue

from block_tokenizer import Tokenizer


def process_projects(process_num, list_projects, base_file_id, threads_queue, tokenizer):
    stats_folder = dirs_config["stats_folder"]
    bookkeeping_folder = dirs_config["bookkeeping_folder"]
    tokens_folder = dirs_config["tokens_folder"]

    tokens_filename = os.path.join(tokens_folder, f'files-tokens-{process_num}.tokens')
    bookkeeping_filename = os.path.join(bookkeeping_folder, f'bookkeeping-proj-{process_num}.projs')
    stats_filename = os.path.join(stats_folder, f'files-stats-{process_num}.stats')

    print(f"[INFO] Process {process_num} starting")
    with open(tokens_filename, 'a+', encoding="utf-8") as tokens_file, \
        open(bookkeeping_filename, 'a+', encoding="utf-8") as bookkeeping_file, \
        open(stats_filename, 'a+', encoding="utf-8") as stats_file:
        out_files = (tokens_file, bookkeeping_file, stats_file)
        p_start = dt.datetime.now()
        for proj_id, proj_path in list_projects:
            if proj_path == "":
                continue
            tokenizer.process_one_project(process_num, str(proj_id), proj_path, base_file_id, out_files)

    p_elapsed = (dt.datetime.now() - p_start).seconds
    print(f"[INFO] Process {process_num} finished. {tokenizer.get_file_count()} files in {p_elapsed} s")

    # Let parent know
    threads_queue.put((process_num, tokenizer.get_file_count()))
    sys.exit(0)


def start_child(processes, threads_queue, proj_paths, batch, tokenizer):
    # This is a blocking get. If the queue is empty, it waits
    pid, n_files_processed = threads_queue.get()
    # OK, one of the processes finished. Let's get its data and kill it
    tokenizer.increase_file_count(n_files_processed)
    kill_child(processes, pid, n_files_processed, tokenizer)

    # Get a new batch of project paths ready
    paths_batch = proj_paths[:batch]
    del proj_paths[:batch]

    print(f"[INFO] Starting new process {pid}")
    p = Process(name=f"Process {pid}", target=process_projects, args=(pid, paths_batch, processes[pid][1], threads_queue, tokenizer))
    processes[pid][0] = p
    p.start()


def kill_child(processes, pid, n_files_processed, tokenizer):
    if processes[pid][0] is not None:
        processes[pid][0] = None
        processes[pid][1] += n_files_processed
        print(f"[INFO] Process {pid} finished, {n_files_processed} files processed {processes[pid][1]}. Current total: {tokenizer.get_file_count()}")


def active_process_count(processes):
    return len([p for p in processes if p[0] is not None])


if __name__ == '__main__':
    tokenizer = Tokenizer("block_config.ini")
    language_config, inner_config, dirs_config = tokenizer.get_configs()
    PATH_stats_file_folder = dirs_config["stats_folder"]
    PATH_bookkeeping_proj_folder = dirs_config["bookkeeping_folder"]
    PATH_tokens_file_folder = dirs_config["tokens_folder"]
    N_PROCESSES = inner_config["N_PROCESSES"]
    PROJECTS_BATCH = inner_config["PROJECTS_BATCH"]
    init_file_id = inner_config["init_file_id"]

    p_start = dt.datetime.now()

    proj_paths = []
    with open(inner_config["FILE_projects_list"], "r", encoding="utf-8") as f:
        proj_paths = f.read().split("\n")
    proj_paths = list(enumerate(proj_paths, start=1))
    # it will diverge the process flow on process_file()

    if any(map(lambda x: os.path.exists(dirs_config[x]), ["stats_folder", "bookkeeping_folder", "tokens_folder"])):
        missing_folders = filter(lambda x: os.path.exists(dirs_config[x]), ["stats_folder", "bookkeeping_folder", "tokens_folder"])
        for missing_folder in missing_folders:
            print(f"ERROR - Folder [{missing_folder}] already exists!")
        sys.exit(1)

    os.makedirs(PATH_stats_file_folder)
    os.makedirs(PATH_bookkeeping_proj_folder)
    os.makedirs(PATH_tokens_file_folder)

    # Multiprocessing with N_PROCESSES
    # [process, file_count]
    processes = [[None, init_file_id] for i in range(N_PROCESSES)]
    # The queue for processes to communicate back to the parent (this process)
    # Initialize it with N_PROCESSES number of (process_id, n_files_processed)
    global_queue = Queue()
    for i in range(N_PROCESSES):
        global_queue.put((i, 0))

    print("[INFO] *** Starting regular projects...")
    while len(proj_paths) > 0:
        start_child(processes, global_queue, proj_paths, PROJECTS_BATCH, tokenizer)

    print("[INFO] *** No more projects to process. Waiting for children to finish...")
    while active_process_count(processes) > 0:
        pid, n_files_processed = global_queue.get()
        kill_child(processes, pid, n_files_processed, tokenizer)

    p_elapsed = dt.datetime.now() - p_start
    print(f"[INFO] *** All done. {tokenizer.get_file_count()} files in {p_elapsed}")
