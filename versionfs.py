#!/usr/bin/env python

#Name: Imashi Kinigama
#UPI: ikin507

from __future__ import with_statement

import logging

import os
import sys
import errno
import shutil
import filecmp
import re

from fuse import FUSE, FuseOSError, Operations, LoggingMixIn

class VersionFS(LoggingMixIn, Operations):
    def __init__(self):
        # get current working directory as place for versions tree
        self.root = os.path.join(os.getcwd(), '.versiondir')  #gets the current working directory and combines it with ".versiondir"
        # check to see if the versions directory already exists
        if os.path.exists(self.root):
            print ('Version directory already exists.')
        else:
            print ('Creating version directory.')
            os.mkdir(self.root)

    # Helpers
    # =======

    def _full_path(self, partial):
        if partial.startswith("/"):
            partial = partial[1:]    #Exclude the / sign
        path = os.path.join(self.root, partial) # Joins the root with the partial 
        return path

    # Filesystem methods
    # ==================

    def access(self, path, mode):
        # print ("access:", path, mode)
        full_path = self._full_path(path) # the path here is just the name of the directory
        if not os.access(full_path, mode):
            raise FuseOSError(errno.EACCES)

    def chmod(self, path, mode):
        # print ("chmod:", path, mode)
        full_path = self._full_path(path)
        return os.chmod(full_path, mode)    #changes the mode of path to the given numeric mode

    def chown(self, path, uid, gid):
        # print ("chown:", path, uid, gid)
        full_path = self._full_path(path)
        return os.chown(full_path, uid, gid) #changes the owner and the group id of the path

    def getattr(self, path, fh=None):
        # print ("getattr:", path)
        full_path = self._full_path(path)
        st = os.lstat(full_path)   # returns information about the file
        return dict((key, getattr(st, key)) for key in ('st_atime', 'st_ctime',
                     'st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_size', 'st_uid'))

    def readdir(self, path, fh):
        # print ("readdir:", path)
        full_path = self._full_path(path)

        dirents = ['.', '..']
        if os.path.isdir(full_path):   #Checks whether the path is the existing directory
            dirents.extend(os.listdir(full_path))
        for r in dirents:
            if(bool(re.match("(\w+).(\w+).(\d)", r))):
                continue
            yield r                   #print everything inside the directories

    def readlink(self, path):
        # print ("readlink:", path)
        pathname = os.readlink(self._full_path(path))
        if pathname.startswith("/"):
            # Path name is absolute, sanitize it.
            return os.path.relpath(pathname, self.root)   #prints the relative file path
        else:
            return pathname

    def mknod(self, path, mode, dev):
        # print ("mknod:", path, mode, dev)
        return os.mknod(self._full_path(path), mode, dev)   #create a file system node

    def rmdir(self, path):
        # print ("rmdir:", path)
        full_path = self._full_path(path)
        return os.rmdir(full_path)          #Removes the directory path so that it is empty

    def mkdir(self, path, mode):
        # print ("mkdir:", path, mode)
        return os.mkdir(self._full_path(path), mode)  # creates a new directory

    def statfs(self, path):
        # print ("statfs:", path)
        full_path = self._full_path(path)
        stv = os.statvfs(full_path)   # Get info   about the mounted file system
        return dict((key, getattr(stv, key)) for key in ('f_bavail', 'f_bfree',
            'f_blocks', 'f_bsize', 'f_favail', 'f_ffree', 'f_files', 'f_flag',
            'f_frsize', 'f_namemax'))

    def unlink(self, path):
        # print ("unlink:", path)
        return os.unlink(self._full_path(path)) # deletes a file path

    def symlink(self, name, target):
        # print ("symlink:", name, target)
        return os.symlink(target, self._full_path(name)) #creates a symbolic link pointing to the given destination

    def rename(self, old, new):
        # print ("rename:", old, new)
        return os.rename(self._full_path(old), self._full_path(new)) # renames the file 

    def link(self, target, name):
        # print ("link:", target, name)
        return os.link(self._full_path(name), self._full_path(target)) # creates a hard link or a copy of the file

    def utimens(self, path, times=None):
        # print ("utimens:", path, times)
        return os.utime(self._full_path(path), times) # sets the accessed and modified times of the file specified by the path

    # File methods
    # ============

    def open(self, path, flags):
        print ('** open:', path, '**')
        full_path = self._full_path(path)
        if(path.startswith("/")):
            if(path[1]=='.'):
                return os.open(full_path, flags)
        else:
            if(path[0]=='.'):
                return os.open(full_path, flags)
        shutil.copyfile(full_path, os.path.join(self.root,'copy.txt'))
        print("making a copy")
        return os.open(full_path, flags)

    def create(self, path, mode, fi=None):
        print ('** create:', path, '**')
        full_path = self._full_path(path)
        return os.open(full_path, os.O_WRONLY | os.O_CREAT, mode)

    def read(self, path, length, offset, fh):
        print ('** read:', path, '**')
        os.lseek(fh, offset, os.SEEK_SET)
        return os.read(fh, length)

    def write(self, path, buf, offset, fh):
        print ('** write:', path, '**')
        os.lseek(fh, offset, os.SEEK_SET)
        return os.write(fh, buf)

    def truncate(self, path, length, fh=None):
        print ('** truncate:', path, '**')
        full_path = self._full_path(path)
        with open(full_path, 'r+') as f:    #opens the file
            f.truncate(length)       #resizes the file to given number of bytes

    def flush(self, path, fh):
        print ('** flush', path, '**')
        return os.fsync(fh)    # force write of the file associated 

    def release(self, path, fh):
        print ('** release', path, '**')
        full_path = self._full_path(path)
        copy_path = os.path.join(self.root,'copy.txt')
        if(filecmp.cmp(full_path, copy_path, False)):
            os.unlink(copy_path)
            print("content was not updated")
        else:
            print("content was updated")
            if path.startswith("/"):
                path = path[1:] + "."
            latest_version = 0
            for char_seq in os.listdir(self.root):
                if((path in char_seq) and ('.swp' not in char_seq)):
                    last_version = int(char_seq[(len(char_seq)-1):])
                    if(last_version>latest_version):
                        latest_version = last_version
            if(latest_version>=6):
                os.unlink(os.path.join(self.root, path+str(6)))
                latest_version = 5
            for i in range(latest_version,0,-1):
                old_path = os.path.join(self.root, path+str(i))
                new_path = os.path.join(self.root, path+str(i+1))
                shutil.copyfile(old_path, new_path)
            if(latest_version==0):
                file_name = path+str(2)
                os.rename(copy_path, os.path.join(self.root,file_name))
            else:
                os.unlink(copy_path)
            file_name = path+str(1)
            shutil.copyfile(full_path, os.path.join(self.root,file_name))
        return os.close(fh)

    def fsync(self, path, fdatasync, fh):
        print ('** fsync:', path, '**')
        return self.flush(path, fh)   # uses the flush method defined earlier

def main(mountpoint):
    FUSE(VersionFS(), mountpoint, nothreads=True, foreground=True)

if __name__ == '__main__':
    # logging.basicConfig(level=logging.DEBUG)
    main(sys.argv[1])
