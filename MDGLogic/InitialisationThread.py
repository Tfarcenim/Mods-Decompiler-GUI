import json
import logging
import os
import shutil
import subprocess
import time

from PySide6.QtCore import QThread

from MDGLogic.AbstractMDGThread import AbstractMDGThread
from MDGUtil import FileUtils, PathUtils
from MDGUtil.SubprocessKiller import kill_subprocess
from MDGUtil.SubprocessOutsAnalyseThread import SubprocessOutsAnalyseThread


class ExceptionThread(QThread):
    """
    Class created to raise exception without interrupting process.
    For logging.
    """
    def __init__(self, e: Exception):
        super().__init__()
        self.e = e

    def run(self) -> None:
        raise self.e


class InitialisationThread(AbstractMDGThread):
    def run(self) -> None:
        decomp_cmd = self.serialized_widgets['decomp_cmd_line_edit']['text']
        cache_enabled = self.serialized_widgets['cache_check_box']['isChecked']

        self.progress.emit(20, 'Clearing tmp folder')
        FileUtils.clear_tmp_folders()
        logging.info('Cleared tmp folders.')

        self.progress.emit(40, 'Clearing result folder')
        if cache_enabled:
            FileUtils.create_folder(PathUtils.RESULT_FOLDER_PATH)
            if not self.serialized_widgets['deobf_check_box']['isChecked']:
                FileUtils.remove_folder(PathUtils.DEOBFUSCATED_MODS_PATH)
            if not self.serialized_widgets['decomp_check_box']['isChecked']:
                FileUtils.remove_folder(PathUtils.DECOMPILED_MODS_PATH)
            for file in os.listdir(PathUtils.RESULT_FOLDER_PATH):
                # remove all except ['deobfuscated_mods', 'decompiled_mods']
                path = os.path.join(PathUtils.RESULT_FOLDER_PATH, file)
                if file not in ['deobfuscated_mods', 'decompiled_mods']:
                    if os.path.isfile(path):
                        os.remove(path)
                    else:
                        logging.info(f'Clearing {file}')
                        shutil.rmtree(path)

            cache_path = os.path.join(PathUtils.DECOMPILED_MODS_PATH, 'cache.json')
            if not os.path.exists(cache_path):
                FileUtils.remove_folder(PathUtils.DECOMPILED_MODS_PATH)
            try:  # remove mods decompilation of which was interrupted
                with open(cache_path, 'r') as f:
                    cache = json.loads(f.read())
                for mod in os.listdir(PathUtils.DECOMPILED_MODS_PATH):
                    mod_path = os.path.join(PathUtils.DECOMPILED_MODS_PATH, mod)
                    if mod not in cache and os.path.isdir(mod_path):
                        shutil.rmtree(mod_path)
                        logging.info(f'Found {mod} in decompiled mods.'
                                     f"But it's not in cache. Removing. "
                                     f'Maybe decompilation of it was interrupted.')
            except FileNotFoundError:
                pass

        else:
            FileUtils.clear_result_folders()
        logging.info('Cleared result folders.')

        self.progress.emit(50, 'Creating new folders')
        FileUtils.init_folders()
        logging.info('Created new folders.')

        if self.serialized_widgets['decomp_cmd_groupbox']['isEnabled']:
            self.progress.emit(80, 'Checking decompiler/decompiler cmd are correct')
            logging.info('Checking decompiler/decompiler cmd are correct')
            FileUtils.create_folder(PathUtils.TMP_DECOMPILER_TEST_PATH)
            try:
                decomp_cmd_formatted = decomp_cmd.format(path_to_jar=PathUtils.TEST_MOD_PATH,
                                                         out_path=PathUtils.TMP_DECOMPILER_TEST_PATH)
                self.cmd = subprocess.Popen(decomp_cmd_formatted, shell=True,
                                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                cmd_analyse_thread = SubprocessOutsAnalyseThread(self.cmd)
                cmd_analyse_thread.start()
                cmd_analyse_thread.join()
                assert len(os.listdir(PathUtils.TMP_DECOMPILER_TEST_PATH)) >= 1
            except Exception as e:
                thread = ExceptionThread(e)
                thread.start()
                time.sleep(0.1)
                self.critical_signal.emit('Incorrect decompiler cmd',
                                          "With this decompiler/decompiler cmd program won't work.\n"
                                          'This message indicates that {path_to_jar} is not decompiled to {out_path}.\n'
                                          'Check decompiler/decompiler cmd: path, syntax, etc. And try again.\n'
                                          'Open the lastest log for more details.\n')
                return
            logging.info('Checked decompiler/decompiler cmd are correct successfully.')

        self.progress.emit(100, 'Initialisation complete')
        logging.info('Initialisation completed.')

    def terminate(self) -> None:
        try:
            kill_subprocess(self.cmd.pid)
        except AttributeError:
            pass
        super().terminate()
