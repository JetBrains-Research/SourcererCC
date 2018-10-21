"""
Created on Nov 8, 2016

@author: saini
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import os
import subprocess
import sys


class ScriptControllerException(Exception):
    pass


def full_file_path(string):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), string)


def full_script_path(string, param=""):
    if len(param) == 0:
        return os.path.join(os.path.dirname(os.path.realpath(__file__)), string)
    else:
        return os.path.join(os.path.dirname(os.path.realpath(__file__)), string) + " " + param


def run_command(cmd, out_file, err_file):
    print("running new command {}".format(" ".join(cmd)))
    with open(out_file, "w") as out, open(err_file, "w") as err:
        p = subprocess.Popen(cmd, stdout=out.fileno(), stderr=err.fileno(), universal_newlines=True)
        p.communicate()
    return p.returncode


class ScriptController(object):
    """
    Aim of this class is to run the scripts for SourcererCC with a single command
    """
    # exit codes
    EXIT_SUCCESS = 0
    EXIT_FAILURE = 1
    # states
    STATE_EXECUTE_1 = 0
    STATE_INIT = 1
    STATE_INDEX = 2
    STATE_MOVE_INDEX = 3
    STATE_EXECUTE_2 = 4
    STATE_SEARCH = 5

    def __init__(self, parameters):
        self.params = {}
        self.params.update(parameters)
        self.script_meta_file_name = full_file_path("scriptinator_metadata.scc")
        self.current_state = ScriptController.STATE_EXECUTE_1  # default state
        self.previous_run_state = self.load_previous_state()

    def execute(self):
        self.prepare_for_init()
        self.init()
        self.index()
        self.move_index()
        self.prepare_for_search()
        self.search()
        print("SUCCESS: Search Completed on all nodes")

    def search(self):
        if self.previous_run_state > ScriptController.STATE_SEARCH:
            return_code = ScriptController.EXIT_SUCCESS
        else:
            command = full_script_path("runnodes.sh", "search {nodes}".format(nodes=self.params["num_nodes_search"]))
            command_params = command.split()
            return_code = run_command(
                command_params, full_file_path("Log_search.out"),
                full_file_path("Log_search.err"))
        self.current_state = ScriptController.STATE_EXECUTE_1  # go back to EXE 1 state

        if return_code != ScriptController.EXIT_SUCCESS:
            raise ScriptControllerException(
                "One or more nodes failed during Step Search."
                " Check Log_search.log for more details."
                " grep for FAILED in the log file"
            )

        self.flush_state()

    def prepare_for_search(self):
        if self.previous_run_state > ScriptController.STATE_EXECUTE_2:
            return_code = ScriptController.EXIT_SUCCESS
            # execute command to create the dir structure
        else:
            command = full_script_path("execute.sh", "{nodes}".format(
                nodes=self.params["num_nodes_search"]))
            command_params = command.split()
            return_code = run_command(
                command_params,
                full_file_path("Log_execute_{nodes}.out".format(nodes=self.params["num_nodes_search"])),
                full_file_path("Log_execute_{nodes}.err".format(nodes=self.params["num_nodes_search"]))
            )
        self.current_state += 1

        if return_code != ScriptController.EXIT_SUCCESS:
            raise ScriptControllerException("error in execute.sh script while preparing for the search step.")

        self.flush_state()

    def move_index(self):
        if self.previous_run_state > ScriptController.STATE_MOVE_INDEX:
            return_code = ScriptController.EXIT_SUCCESS
        else:
            # execute move indexes
            command = full_script_path("move-index.sh")
            command_params = command.split()
            return_code = run_command(
                command_params, full_file_path("Log_move_index.out"),
                full_file_path("Log_move_index.err"))
        self.current_state += 1

        if return_code != ScriptController.EXIT_SUCCESS:
            raise ScriptControllerException("error in move-index.sh script.")

        self.flush_state()

    def index(self):
        # execute index
        if self.previous_run_state > ScriptController.STATE_INDEX:
            return_code = ScriptController.EXIT_SUCCESS
        else:
            command = full_script_path("runnodes.sh", "index 1")
            command_params = command.split()
            return_code = run_command(
                command_params, full_file_path("Log_index.out"), full_file_path("Log_index.err"))
        self.current_state += 1

        if return_code != ScriptController.EXIT_SUCCESS:
            raise ScriptControllerException("error during indexing.")

        self.flush_state()

    def init(self):
        # execute the init command
        if self.previous_run_state > ScriptController.STATE_INIT:
            return_code = ScriptController.EXIT_SUCCESS
        else:
            if self.previous_run_state == ScriptController.STATE_INIT:
                # last time the execution failed at init step.
                # We need to replace the existing gtpm index  from the backup
                command = full_script_path("restore-gtpm.sh")
                command_params = command.split()
                run_command(
                    command_params, full_file_path("Log_restore_gtpm.out"),
                    full_file_path("Log_restore_gtpm.err")
                )
            else:
                # take backup of existing gtpmindex before starting init
                command = full_script_path("backup-gtpm.sh")
                command_params = command.split()
                run_command(
                    command_params,
                    full_file_path("Log_backup_gtpm.out"),
                    full_file_path("Log_backup_gtpm.err")
                )
            # run the init step
            command = full_script_path("runnodes.sh", "init 1")
            command_params = command.split()
            return_code = run_command(command_params, full_file_path("Log_init.out"), full_file_path("Log_init.err"))
        self.current_state += 1

        if return_code != ScriptController.EXIT_SUCCESS:
            raise ScriptControllerException("error during init.")

        self.flush_state()

    def prepare_for_init(self):
        # execute command
        print("previous run state {s}".format(s=self.previous_run_state))
        if self.previous_run_state > ScriptController.STATE_EXECUTE_1:
            return_code = ScriptController.EXIT_SUCCESS
        else:
            command = full_script_path('execute.sh', "1")
            command_params = command.split()
            return_code = run_command(
                command_params, full_file_path("Log_execute_1.out"), full_file_path("Log_execute_1.err"))
        self.current_state += 1

        if return_code != ScriptController.EXIT_SUCCESS:
            raise ScriptControllerException("error in execute.sh script while preparing for init step.")

        self.flush_state()

    def flush_state(self):
        print("current state: ", str(self.current_state))
        with open(self.script_meta_file_name, "w") as f:
            print("flushing current state", str(self.current_state))
            f.write("{line}\n".format(line=self.current_state))

    def load_previous_state(self):
        print("loading previous run state")
        if os.path.isfile(self.script_meta_file_name):
            with open(self.script_meta_file_name, "r") as f:
                return int(f.readline())
        else:
            print("{f} doesn't exist, creating one with state EXECUTE_1".format(f=self.script_meta_file_name))
            return ScriptController.STATE_EXECUTE_1


if __name__ == '__main__':
    num_nodes = 2
    if len(sys.argv) > 1:
        num_nodes = int(sys.argv[1])
    print("search will be carried out with {num} nodes".format(num=num_nodes))
    params = {"num_nodes_search": num_nodes}

    controller = ScriptController(params)
    controller.execute()
