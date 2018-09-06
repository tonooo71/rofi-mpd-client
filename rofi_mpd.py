#!/usr/bin/python

import subprocess
import sys
import musicpd


# appearance
rofi_appearance = [
    '-font',    'Monospace Bold 12',
    '-width',   '60',
    '-padding', '40',
    '-lines',   '8',
    '-columns', '2'
]


class rofi_options:
    def __init__(self, client):
        self.client = client
        self.top_dir = ''
        self.sel_row = 1
        self.mesg = ''
        self.options = ['rofi', '-selected-row', '0',
                        '-mesg', '', '-i', '-dmenu', '-p', '~/Music/']+rofi_appearance

    def gen_options(self, top_dir):
        self.top_dir = top_dir
        self.sel_row = 1
        self.mesg = ''
        self.set_row()
        if self.client.status()['state'] != 'stop' and self.client.playlistinfo():
            self.set_mesg()
        self.options[2] = str(self.sel_row)
        self.options[4] = self.mesg
        if self.client.playlistinfo() and self.client.status()['state'] != 'stop':
            add = '  ['+str(int(self.client.status()['song'])+1)+'/'+self.client.status()['playlistlength']+']'
            self.options[4] += add
        self.options[8] = '~/Music/' + self.top_dir

    def set_row(self):
        if self.top_dir:
            self.sel_row += 1

    def set_mesg(self):
        song_dic = self.client.currentsong()
        if self.client.status()['state'] == 'play':
            self.mesg += '  '
        elif self.client.status()['state'] == 'pause':
            self.mesg += '  '
        try:
            album = song_dic['album']
            song = song_dic['title']
            artist = song_dic['artist']
            self.mesg += song+' ('+album+'/'+artist+')'
        except:
            self.mesg += song_dic['file'].split('/')[-1]


class rofi_index:
    def __init__(self, client):
        self.client = client
        self.top_dir = ''
        self.prefix = ''  # for play/pause, back, add all
        self.indexes = ''  # music

    def gen_index(self, top_dir):
        self.top_dir = top_dir
        if self.client.status()['state'] == 'play':
            self.prefix = ' Pause\n'
        else:
            self.prefix = ' Play\n'
        self.indexes = ''
        self.set_prefix()
        self.set_indexes()

    def set_prefix(self):
        if self.top_dir:
            self.prefix += ' Go Back\n'
            self.prefix += ' Add all\n'
        else:
            self.prefix = ' Clear Playlist\n' + self.prefix

    def set_indexes(self):
        indexes_dic = self.client.lsinfo(self.top_dir)
        count = 1
        for i in indexes_dic:
            if 'directory' in i:
                self.indexes += '   ' + i['directory'].split('/')[-1] + '\n'
            elif 'title' in i:
                self.indexes += '   ' + str(count) + '. ' + i['title'] + '\n'
                count += 1
            elif 'file' in i:
                self.indexes += '   ' + str(count) + '. ' + i['file'].split('/')[-1] + '\n'
                count += 1


def main():
    client = musicpd.MPDClient()
    client.connect('localhost', 6600)
    option = rofi_options(client)
    index = rofi_index(client)
    current_dir = ''
    while 1:
        option.gen_options(current_dir)
        rofi = subprocess.Popen(option.options, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
        index.gen_index(current_dir)
        select = index.prefix + index.indexes
        tmp = rofi.communicate(select.encode())[0].decode().rstrip()
        if not tmp:
            break
        else:
            if ' Go Back' == tmp:
                print(current_dir)
                if '/' in current_dir:
                    current_dir = current_dir[:current_dir.rfind('/')]
                    print(current_dir)
                else:
                    current_dir = ''
            elif ' Add all' == tmp:
                client.add(current_dir)
            elif ' Clear Playlist' == tmp:
                client.clear()
            elif ' Play' == tmp:
                if not client.playlistinfo():
                    pass
                else:
                    client.play()
            elif ' Pause' == tmp:
                client.pause()
            elif '' in tmp:
                pass
            else:
                if current_dir:
                    current_dir += '/' +tmp[4:]
                else:
                    current_dir = tmp[4:]


if __name__ == '__main__':
    main()
