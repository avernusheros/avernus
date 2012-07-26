import os


def get_ui_file(filename):
    current_rep = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_rep, filename)
