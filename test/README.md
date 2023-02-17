# Testing

Testing is generally done by running 'tox' from the repository's root directory

To run testing from the command line to test code in local repo:

$ export PYTHONPATH=$HOME/gitlab/nvcl_kit
$ python -m unittest test_reader.py
$ python3 -m unittest test_reader.TestNVCLReader.test_borehole_data

Use 'tox' to test the packaged 'pypi' version

