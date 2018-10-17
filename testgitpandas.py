import unittest

import os
import sys
sys.path.append(os.path.join(os.getcwd(), 'git-pandas'))
import gitpandas as gp
from tools import Timeit
from test import get_total_changes_timeline
import pygit2
import git
import pandas
from io import StringIO

class TestGitPandasMethods(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repostat_repo_dir = os.path.dirname(os.path.abspath(__file__))

    @Timeit("Fetching history using subprocess call")
    def git_subprocess_history_fetch(self):
        os.chdir(self.repostat_repo_dir)
        return get_total_changes_timeline()

    @Timeit("Fetching history using pygit2 lib")
    def pygit2_history_fetching(self):
        self.pg_repo = pygit2.Repository(self.repostat_repo_dir)

        history = {}
        child_commit = self.pg_repo.head.peel()
        timestamps = []
        while len(child_commit.parents) != 0:
            # taking [0]-parent is equivalent of '--first-parent -m' options
            parent_commit = child_commit.parents[0]
            st = self.pg_repo.diff(parent_commit, child_commit).stats
            history[child_commit.author.time] = {'files': st.files_changed,
                                                 'ins': st.insertions,
                                                 'del': st.deletions}
            timestamps.append(child_commit.author.time)
            child_commit = parent_commit
        # initial commit does not have parent, so we take diff to empty tree
        st = child_commit.tree.diff_to_tree(swap=True).stats
        history[child_commit.author.time] = {'files': st.files_changed,
                                             'ins': st.insertions,
                                             'del': st.deletions}
        timestamps.append(child_commit.author.time)

        lines_count = 0
        lines_added = 0
        lines_removed = 0
        timestamps.reverse()
        for t in timestamps:
            lines_added += history[t]['ins']
            lines_removed += history[t]['del']
            lines_count += history[t]['ins'] - history[t]['del']
            history[t]['lines'] = lines_count
        return history, lines_added, lines_removed, lines_count

    @Timeit("Fetching history using gitpandas lib")
    def gitpandas_history_fetching(self):
        self.gp_repo = gp.Repository(self.repostat_repo_dir)
        self.gp_repo.commit_history(branch='gitpandas')

    @Timeit("Fetching history using 'feststelltaste' approach (GitPython + pandas)")
    def feststelltaste_history_fetching(self):
        git_log = git.Repo(self.repostat_repo_dir, odbt=git.GitCmdObjectDB).git.log('--numstat', '--pretty=format:\t\t\t%h\t%at\t%aN')
        commits_raw = pandas.read_csv(StringIO(git_log),
                                  sep='\t',
                                  header=None,
                                  names=['additions', 'deletions', 'filename', 'sha', 'timestamp', 'author']
                                  )
        commits_raw[['additions', 'deletions', 'filename']] \
            .join(commits_raw[['sha', 'timestamp', 'author']].fillna(method='ffill')).dropna()

    def test_performance(self):
        self.git_subprocess_history_fetch()
        self.pygit2_history_fetching()
        self.feststelltaste_history_fetching()
        self.gitpandas_history_fetching()
