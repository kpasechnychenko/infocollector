infocollector
=============

Collect information about remote server via SSH.

This script connects to remote server via SSH, copies itself on remote and prints information:


    - Average load
    - Block devices
    - CPU cores count
    - Devices mount points
    - Space available on root device
    - Installed packages


Usage:
    collector.py -s <host name> -u <user name> -k <path for public key>
