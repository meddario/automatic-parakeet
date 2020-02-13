#!/usr/bin/python

# see https://nvbn.github.io/2017/10/11/iterm2-ssh-color/

import sys
import subprocess
import os
import json
import errno


def get_host():
    for arg in sys.argv[1:]:
        if not arg.startswith('-'):
            return arg


def str_to_colors(s):
    hash = 0
    for c in s:
        hash = ord(c) + ((hash << 5) - hash)
    values = []
    for i in range(3):
        values.append((hash >> (i * 8)) & 0xff)
    return values


def generate_seqs(colors):
    seq = '\033]6;1;bg;{};brightness;{}\a'
    names = ['red', 'green', 'blue']
    for name, v in zip(names, colors):
        yield seq.format(name, v)


def merge_two_dicts(x, y):
    z = x.copy()   # start with x's keys and values
    z.update(y)    # modifies z with y's keys and values & returns None
    return z


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


class GitUtils(object):
    def __init__(self):
        self.repo_root = None

    def is_inside_work_tree(self):
        try:
            repo_check = subprocess.check_output(
                ["git", "rev-parse", "--is-inside-work-tree"], stderr=subprocess.PIPE).strip().decode('utf-8')
            inside_work_tree = (repo_check) == 'true'
        except subprocess.CalledProcessError as err:
            inside_work_tree = False
        return inside_work_tree

    def get_repo_root(self):
        if not self.is_inside_work_tree():
            return None
        self.repo_root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], stderr=subprocess.PIPE).strip().decode('utf-8')
        return self.repo_root


def update_iterm_tab_color(color):
    if os.getenv('TERM_PROGRAM') == 'iTerm.app':
        for seq in generate_seqs(color):
            sys.stdout.write(seq)


def update_vscode_peacock_config(repo_root, values):
    hexval = '#%02x%02x%02x' % tuple(values)
    config_dir = os.path.join(repo_root, '.vscode')
    config_path = os.path.join(config_dir, 'settings.json')
    additional_config = {"peacock.color": hexval}
    config = additional_config
    if os.path.exists(config_path):
        with open(config_path) as f:
            file_str = f.read()
            existing_config = json.loads(file_str)
            if existing_config.get("peacock.color") == hexval:
                return
            config = merge_two_dicts(existing_config, additional_config)
    mkdir_p(config_dir)
    with open(config_path, 'w') as f:
        f.write(json.dumps(config))


def get_config():
    config_path = os.path.join(os.path.expanduser('~'), '.workspace-utils.json')
    config = {}
    if os.path.exists(config_path):
        with open(config_path) as f:
            config_str = f.read()
            config = json.loads(config_str)
    return config


if __name__ == '__main__':
    config = get_config().get('customize_workspace')
    if config:
        git_utils = GitUtils()
        repo_root = git_utils.get_repo_root()
        if repo_root:
            colors = str_to_colors(repo_root)
            if config.get('update_iterm_tab_color'):
                update_iterm_tab_color(colors)
            if config.get('update_vscode_peacock_config'):
                update_vscode_peacock_config(repo_root, colors)
