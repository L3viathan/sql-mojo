import subprocess
import contextlib


@contextlib.contextmanager
def pager(command="less", options=None):
    # Pager Options:
    # -F: Quit less if the entire content can be displayed on the first
    #     page.
    # -R: Display raw control characters.
    # -S: Disable line wrapping.
    # -X: Avoid clearing the screen on de-initialization. This in
    #     combination with the -F option allows a content sensitive
    #     triggering of less.
    command_list = [command]
    if options:
        command_list.extend([options])
    pager = subprocess.Popen(command_list, stdin=subprocess.PIPE)

    yield FakeTTY(pager.stdin)

    pager.stdin.close()
    pager.wait()


class FakeTTY:
    """ Can be passed to shortcuts.print_formatted_text without triggering
    assertion errors.
    """

    def __init__(self, stdout):
        self.stdout = stdout

    def get_size(self):
        return "No one actually cares, haha"

    def isatty(self):
        return True

    @property
    def encoding(self):
        return "utf-8"

    def __getattr__(self, name):
        return getattr(self.stdout, name)
