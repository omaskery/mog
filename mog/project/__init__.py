"""
this package provides the general "project management" functionality within mog
"""


import datetime
import json
import os


class Project(object):
    """Represents a mog project"""

    def __init__(self, path):
        self._basepath = os.path.abspath(path)
        project_file_path = ProjectFile.path_from_base(self._basepath)
        self._projectfile = ProjectFile.load_from(project_file_path)

    @property
    def project_file(self):
        return self._projectfile

    @staticmethod
    def already_exists(path):
        if os.path.isdir(path) and ProjectFile.exists_within(path):
            return True
        return False

    @staticmethod
    def create_new(path, name, gm_project_path):
        os.makedirs(path)
        project_file_path = ProjectFile.path_from_base(path)
        project_file = ProjectFile.create_new(name, gm_project_path)
        project_file.save_to(project_file_path)
        return Project(path)


class ProjectFile(object):
    """Convenience utility that represents the project file in a mog project directory"""

    def __init__(self):
        self._blob = {}

    @property
    def project_name(self):
        return self._blob['name']

    @property
    def gamemaker_project_path(self):
        return self._blob['gm-proj']

    @property
    def project_creation_time(self):
        return self._blob['creation-time']

    @staticmethod
    def path_from_base(basepath):
        return os.path.join(basepath, ".mog-project")

    @staticmethod
    def create_new(name, gm_project_path):
        project_file = ProjectFile()
        project_file._blob['name'] = name
        project_file._blob['gm-proj'] = gm_project_path
        project_file._blob['creation-time'] = str(datetime.datetime.now())
        return project_file

    @staticmethod
    def exists_within(basepath):
        return os.path.isfile(ProjectFile.path_from_base(basepath))

    @staticmethod
    def load_from(filepath):
        result = None
        with open(filepath, 'r') as file:
            result = ProjectFile()
            result._blob = json.load(file)
        return result

    def save_to(self, filepath):
        with open(filepath, 'w') as file:
            json.dump(self._blob, file)
