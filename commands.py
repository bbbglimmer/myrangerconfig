from ranger.api.commands import Command
import os
from ranger.core.loader import CommandLoader


class paste_as_root(Command):
    def execute(self):
        if self.fm.do_cut:
            self.fm.execute_console('shell sudo mv %c .')
        else:
            self.fm.execute_console('shell sudo cp -r %c .')


class toggleVCS(Command):
    def execute(self):
        self.fm.execute_console("set vcs_aware!")
        self.fm.execute_console("reload_cwd")


class mkcd(Command):
    """
    :mkcd <dirname>

    Creates a directory with the name <dirname> and enters it.
    """
    def execute(self):
        from os.path import join, expanduser, lexists
        from os import makedirs
        import re

        dirname = join(self.fm.thisdir.path, expanduser(self.rest(1)))
        if not lexists(dirname):
            makedirs(dirname)

            match = re.search('^/|^~[^/]*/', dirname)
            if match:
                self.fm.cd(match.group(0))
                dirname = dirname[match.end(0):]

            for m in re.finditer('[^/]+', dirname):
                s = m.group(0)
                if s == '..' or (s.startswith('.')
                                 and not self.fm.settings['show_hidden']):
                    self.fm.cd(s)
                else:
                    ## We force ranger to load content before calling `scout`.
                    self.fm.thisdir.load_content(schedule=False)
                    self.fm.execute_console('scout -ae ^{}$'.format(s))
        else:
            self.fm.notify("file/directory exists!", bad=True)


class fzf_select(Command):
    """
    :fzf_select
    Find a file using fzf.
    With a prefix argument to select only directories.

    See: https://github.com/junegunn/fzf
    """

    def execute(self):
        import subprocess
        import os
        from ranger.ext.get_executables import get_executables

        if 'fzf' not in get_executables():
            self.fm.notify('Could not find fzf in the PATH.', bad=True)
            return

        fd = None
        if 'fdfind' in get_executables():
            fd = 'fdfind'
        elif 'fd' in get_executables():
            fd = 'fd'

        if fd is not None:
            hidden = ('--hidden' if self.fm.settings.show_hidden else '')
            exclude = "--no-ignore-vcs --exclude '.git' --exclude '*.py[co]' --exclude '__pycache__'"
            only_directories = ('--type directory' if self.quantifier else '')
            fzf_default_command = '{} --follow {} {} {} --color=always'.format(
                fd, hidden, exclude, only_directories
            )
        else:
            hidden = ('-false' if self.fm.settings.show_hidden else r"-path '*/\.*' -prune")
            exclude = r"\( -name '\.git' -o -iname '\.*py[co]' -o -fstype 'dev' -o -fstype 'proc' \) -prune"
            only_directories = ('-type d' if self.quantifier else '')
            fzf_default_command = 'find -L . -mindepth 1 {} -o {} -o {} -print | cut -b3-'.format(
                hidden, exclude, only_directories
            )

        env = os.environ.copy()
        env['FZF_DEFAULT_COMMAND'] = fzf_default_command
        env['FZF_DEFAULT_OPTS'] = '--height=40% --layout=reverse --ansi --preview="{}"'.format('''
            (
                batcat --color=always {} ||
                bat --color=always {} ||
                cat {} ||
                tree -ahpCL 3 -I '.git' -I '*.py[co]' -I '__pycache__' {}
            ) 2>/dev/null | head -n 100
        ''')

        fzf = self.fm.execute_command('fzf --no-multi', env=env,
                                      universal_newlines=True, stdout=subprocess.PIPE)
        stdout, _ = fzf.communicate()
        if fzf.returncode == 0:
            selected = os.path.abspath(stdout.strip())
            if os.path.isdir(selected):
                self.fm.cd(selected)
            else:
                self.fm.select_file(selected)
#class fzf_select(Command):
#    """
#    :fzf_select
#
#    Find a file using fzf.
#
#    With a prefix argument select only directories.
#
#    See: https://github.com/junegunn/fzf
#    """
#    def execute(self):
#        import subprocess
#        import os.path
#        if self.quantifier:
#            # match only directories
#            command = "find -L . \( -path '*/\.*' -o -fstype 'dev' -o -fstype 'proc' \) -prune \
#            -o -type d -print 2> /dev/null | sed 1d | cut -b3- | fzf +m"
#
#        else:
#            # match files and directories
#            command = "find -L . \( -path '*/\.*' -o -fstype 'dev' -o -fstype 'proc' \) -prune \
#            -o -print 2> /dev/null | sed 1d | cut -b3- | fzf +m"
#
#        fzf = self.fm.execute_command(command,
#                                      universal_newlines=True,
#                                      stdout=subprocess.PIPE)
#        stdout, stderr = fzf.communicate()
#        if fzf.returncode == 0:
#            fzf_file = os.path.abspath(stdout.rstrip('\n'))
#            if os.path.isdir(fzf_file):
#                self.fm.cd(fzf_file)
#            else:
#                self.fm.select_file(fzf_file)
#

#class compress(Command):
#    def execute(self):
#        """ Compress marked files to current directory """
#        cwd = self.fm.thisdir
#        marked_files = cwd.get_selection()
#
#        if not marked_files:
#            return
#
#        def refresh(_):
#            cwd = self.fm.get_directory(original_path)
#            cwd.load_content()
#
#        original_path = cwd.path
#        parts = self.line.split()
#        au_flags = parts[1:]
#
#        descr = "compressing files in: " + os.path.basename(parts[1])
#        obj = CommandLoader(args=['apack'] + au_flags + \
#                [os.path.relpath(f.path, cwd.path) for f in marked_files], descr=descr, read=True)
#
#        obj.signal_bind('after', refresh)
#        self.fm.loader.add(obj)
#
#    def tab(self, tabnum):
#        """ Complete with current folder name """
#
#        extension = ['.zip', '.tar.gz', '.rar', '.7z']
#        return [
#            'compress ' + os.path.basename(self.fm.thisdir.path) + ext
#            for ext in extension
#        ]
#
#
#class extracthere(Command):
#    def execute(self):
#        """ Extract copied files to current directory """
#        copied_files = tuple(self.fm.copy_buffer)
#
#        if not copied_files:
#            return
#
#        def refresh(_):
#            cwd = self.fm.get_directory(original_path)
#            cwd.load_content()
#
#        one_file = copied_files[0]
#        cwd = self.fm.thisdir
#        original_path = cwd.path
#        au_flags = ['-X', cwd.path]
#        au_flags += self.line.split()[1:]
#        au_flags += ['-e']
#
#        self.fm.copy_buffer.clear()
#        self.fm.cut_buffer = False
#        if len(copied_files) == 1:
#            descr = "extracting: " + os.path.basename(one_file.path)
#        else:
#            descr = "extracting files from: " + os.path.basename(
#                one_file.dirname)
#        obj = CommandLoader(args=['aunpack'] + au_flags \
#                + [f.path for f in copied_files], descr=descr, read=True)
#
#        obj.signal_bind('after', refresh)
#        self.fm.loader.add(obj)




class compress(Command):
    def execute(self):
        """ Compress marked files to current directory """
        cwd = self.fm.thisdir
        marked_files = cwd.get_selection()

        if not marked_files:
            return

        def refresh(_):
            cwd = self.fm.get_directory(original_path)
            cwd.load_content()

        original_path = cwd.path
        parts = self.line.split()
        au_flags = parts[1:]

        descr = "compressing files in: " + os.path.basename(parts[1])
        obj = CommandLoader(args=['apack'] + au_flags + \
                [os.path.relpath(f.path, cwd.path) for f in marked_files], descr=descr)

        obj.signal_bind('after', refresh)
        self.fm.loader.add(obj)

    def tab(self):
        """ Complete with current folder name """

        extension = ['.zip', '.tar.gz', '.rar', '.7z']
        return ['compress ' + os.path.basename(self.fm.thisdir.path) + ext for ext in extension]



class extracthere(Command):
    def execute(self):
        """ Extract copied files to current directory """
        copied_files = tuple(self.fm.copy_buffer)

        if not copied_files:
            return

        def refresh(_):
            cwd = self.fm.get_directory(original_path)
            cwd.load_content()

        one_file = copied_files[0]
        cwd = self.fm.thisdir
        original_path = cwd.path
        au_flags = ['-X', cwd.path]
        au_flags += self.line.split()[1:]
        au_flags += ['-e']

        self.fm.copy_buffer.clear()
        self.fm.cut_buffer = False
        if len(copied_files) == 1:
            descr = "extracting: " + os.path.basename(one_file.path)
        else:
            descr = "extracting files from: " + os.path.basename(one_file.dirname)
        obj = CommandLoader(args=['aunpack'] + au_flags \
                + [f.path for f in copied_files], descr=descr)

        obj.signal_bind('after', refresh)
        self.fm.loader.add(obj)




