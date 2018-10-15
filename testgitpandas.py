import unittest

import os
import sys
sys.path.append(os.path.join(os.getcwd(), 'git-pandas'))
import gitpandas as gp


class TestGitPandasMethods(unittest.TestCase):
    def test_initialization(self):
        this_file_dir = os.path.dirname(os.path.abspath(__file__))
        repo = gp.ProjectDirectory(working_dir=os.path.abspath(this_file_dir))
        self.assertEqual(repo.repo_name()['repository'][0], 'repostat')