#!/usr/bin/python

from getopt import getopt
from sys import argv
from os import getloadavg, listdir, statvfs
from multiprocessing import cpu_count
from contextlib import closing
from subprocess import Popen, PIPE

script_usage = """
collector.py COMMAND -s <HOST NAME> -u <USER> -k <PATH TO SSH KEY> [-r]

Options:
    -s --server==      Server name
    -u --username=     Login to remote server
    -k --key=          SSH key for remote server
    -h --help          Help
    -r --remote        Remote execution
    """


def parse_commandline_args():
    """
    Parses and validates command line arguments.
    """
    try:
        opts, args = getopt(argv[1:], "hrs:u:k:", ["help", "remote", "server=", "username=", "key="])
    except Exception as e:
        print str(e)
        print script_usage
        exit(2)

    else:
        res = dict([(opt.lstrip('-')[0], arg) for opt, arg in opts])

        if 'h' in res:
            print script_usage
            exit()

        return (res.get('s', None),
                res.get('u', None),
                res.get('k', None),
                'r' in res)


class ApplicationException(BaseException):
    pass


class RemoteApplicationException(BaseException):
    pass


class RemoteCollector:

    def collect(self):
        try:
            result = ""
            load = self.__get_load()
            result += "Average load:\n" + load

            block_devices = self.__get_block_device_names()
            result += "\n\nBlock devices:\n" + block_devices

            cpu_count = self.__cpu_count()
            result += "\n\nCores count:\n" + cpu_count

            mount_points = self.__get_mount_points()
            result += "\n\nDevices mounted at:\n"
            for s in mount_points:
                result += s + "\n"

            free_space = self.__get_free_space()
            result += "\n\nSpace available on root device:\n" + free_space

            packages = self.__get_packages()
            result += "\n\nInstalled packages:\n"
            for s in packages:
                result += s

            print(result)
            pass
        except BaseException as e:
            raise RemoteApplicationException(e.message)
        pass

    def __get_load(self):
        return str(getloadavg())

    def __get_block_device_names(self):
        devices = listdir('/sys/block/')
        devices = [dev for dev in devices if "ram" not in dev and "loop" not in dev]
        return str(devices)

    def __cpu_count(self):
        return str(cpu_count())

    def __get_mount_points(self):
        with closing(open('/proc/mounts', 'r')) as a:
            return a.readlines()

    def __get_free_space(self):
        st = statvfs('/')
        return str(st.f_bavail * st.f_frsize/1024/1024) + " MB"

    def __get_packages(self):

        process = Popen("rpm -qa | less > /tmp/packages_installed", shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        process.communicate()

        with closing(open("/tmp/packages_installed")) as a:
            return a.readlines()


class Uploader:
    """
    This class is used for uploading current script to remote server and getting information about remote server
    """

    def __init__(self, host, login, ssh_key=None):

        if host is None or len(host) < 4:
            raise ApplicationException("Can't connect to server. Host name is required")
        if login is None:
            raise ApplicationException("Can't connect to server. User name is required")

        if ssh_key is None:
            raise ApplicationException("Can't connect to server because credentials hasn't been provided")

        self.host = host
        self.login = login
        self.ssh_key = ssh_key

        from paramiko import SSHClient, AutoAddPolicy
        self.ssh_client = SSHClient()
        self.ssh_client.set_missing_host_key_policy(AutoAddPolicy())
        self.ssh_client.connect(self.host, username=self.login, key_filename=self.ssh_key)
        pass

    def __get_arguments(self):
        if self.ssh_key is not None:
            return "-i " + self.ssh_key

        raise ApplicationException("Credentials not found")
        pass

    def upload(self):
        with closing(self.ssh_client.open_sftp()) as sender:
            sender.put("./collector.py", remotepath="/tmp/collector.py")
        pass

    def prnt(self):
        stdin, stdout, stderr = self.ssh_client.exec_command("python /tmp/collector.py -r")
        stdin.flush()

        data = stdout.read()

        print("RESULTS:\n\n\n")
        print(data)
        pass


if __name__ == "__main__":
    host, user, key, is_remote = parse_commandline_args()

    try:
        if not is_remote:
            o = Uploader(host=host, login=user, ssh_key=key)
            o.upload()
            o.prnt()
        else:
            o = RemoteCollector()
            o.collect()

    except BaseException as e:
        print(e.message)
        exit(1)
    pass
