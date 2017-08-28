#!/bin/env python3
'''
Perform an PXE-boot of arch-linux on a local network

Sources:
    https://wiki.archlinux.org/index.php/PXE
'''

import os
import argparse
import http.server
import socketserver
import shutil

CONFIG = '''port=0
interface={}
bind-interfaces
dhcp-range={}
dhcp-boot=/arch/boot/syslinux/lpxelinux.0
dhcp-option-force=209,boot/syslinux/archiso.cfg
dhcp-option-force=210,/arch/
dhcp-option-force=66,{}
enable-tftp
tftp-root={}
'''


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Serve archlinux over pxe.')
    parser.add_argument('--interface', help='interface to serve on, default is enp0s25', default='enp0s25')
    parser.add_argument('--iso', help='iso to server', required=True)
    parser.add_argument('--mount_path', help='iso to server, default is /mnt/archiso', default='/mnt/archiso')
    parser.add_argument('--ip', help='own ip, default is 10.0.0.1', default='10.0.0.1')
    parser.add_argument('--dhcp_range', help='start of the dhcp-range, default is 10.0.0.50,10.0.0.150,12h', default='10.0.0.50,10.0.0.150,12h')

    args = parser.parse_args()

    real_config = CONFIG.format(
            args.interface,
            args.dhcp_range,
            args.ip,
            args.mount_path
            )

    # Check requirements
    print('[*] Checking requirements')
    if not shutil.which('dnsmasq'):
        raise Exception('Please install dnsmasq')

    # Prepare files and dirs
    print('[*] Preparing files and dirs')
    shutil.move('/etc/dnsmasq.conf', '/etc/dnsmasq.conf.bak')
    f = open('/etc/dnsmasq.conf', 'w')
    f.write(real_config)
    f.close()

    os.makedirs(args.mount_path, exist_ok=True)
    os.system('mount -o loop,ro {} {}'.format(args.iso, args.mount_path))

    # Stop annoying services
    print('[*] Stopping some services')
    os.system('systemctl stop NetworkManager.service')
    
    # Configure network
    print('[*] Configureing network')
    os.system('ifconfig {} {} netmask 255.255.255.0'.format(args.interface, args.ip))

    # Start dnsmasq
    print('[*] Starting dns and http-server')
    os.system('service dnsmasq start')
    
    # start webserver
    PORT = 80
    handler = http.server.SimpleHTTPRequestHandler
    os.chdir(args.mount_path)
    
    print("[*] Serving at port {} at {}".format(PORT, os.getcwd()))
    print("[*] Press ctrl+c to stop")

    os.system('python3 -m http.server 80')
    
    # Cleanup
    print('[*] Cleaning up')
    ## dnsmasq
    os.system('service dnsmasq stop')
    shutil.move('/etc/dnsmasq.conf.bak', '/etc/dnsmasq.conf')

    ## other services
    os.system('systemctl start NetworkManager.service')
        
    ## umount image
    os.chdir('/tmp/')
    os.system('umount {}'.format(args.mount_path))
