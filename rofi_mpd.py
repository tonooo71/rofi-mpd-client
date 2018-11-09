#!/usr/bin/python

import subprocess
import sys
import musicpd


# appearance
rofi_appearance = [
    '-font',    'Monospace Bold 12',
    '-width',   '60',
    '-padding', '10',
    '-lines',   '8',
    '-columns', '2'
]


class rofi_options:
    def __init__(self, client):
        self.client = client
        self.top_dir = ''
        self.sel_row = 1
        self.mesg = ''
        self.options = ['rofi', '-selected-row', '1', '-mesg', '',
                        '-i', '-dmenu', '-p', '~/Music/']+rofi_appearance

    def gen_options(self, top_dir=''):
        self.top_dir = top_dir
        self.sel_row = 2
        self.mesg = ''
        # self.set_row()
        if self.client.status()['state'] != 'stop' and self.client.playlistinfo():
            self.set_mesg()
        self.options[2] = str(self.sel_row)
        self.options[4] = self.mesg
        if self.client.playlistinfo():
            if self.client.status()['state'] != 'stop':
                pos = int(self.client.status()['song'])+1
                end = self.client.status()['playlistlength']
                self.options[4] += f'  [{pos}/{end}]'
            else:
                end = self.client.status()['playlistlength']
                self.options[4] += f'  [Playlist: {end}]'
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
            if not top_dir:
                self.prefix += ' Next\n'
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
            self.prefix = ' Playlist mode\n Clear Playlist\n' + self.prefix

    def set_indexes(self):
        indexes_dic = self.client.lsinfo(self.top_dir)
        count = 1
        for i in indexes_dic:
            if 'directory' in i:
                self.indexes += f'   {i["directory"].split("/")[-1]}\n'
            elif 'title' in i:
                self.indexes += f'   {count}. {i["title"]}\n'
                count += 1
            elif 'file' in i:
                self.indexes += f'   {count}. {i["file"].split("/")[-1]}\n'
                count += 1


class rofi_playlist:
    def __init__(self, client):
        self.client = client
        self.prefix = ''  # for back index, delete mode, pause, back
        self.indexes = ''  # playlist
        self.playlist = ''  # None: default, Title: detail

    def gen_index(self):
        self.set_prefix()
        self.set_indexes()

    def set_prefix(self):
        if not self.playlist:
            self.prefix = ' Go Back to Main menu\n'
        else:
            self.prefix = ' Go Back\n'
            self.prefix += ' Add this playlist\n'

    def set_indexes(self):
        if not self.playlist:
            self.indexes = 'Stored playlists----------\n'
            for i in self.client.listplaylists():
                self.indexes += f'  {i["playlist"]}\n'
            current_song = 'GORNG'  # tmp
            try:
                current_song = self.client.currentsong()["title"]
            except:
                pass
            self.indexes += 'Playlist------------------\n'
            for i, j in enumerate(self.client.playlistinfo()):
                if current_song == j["title"]:
                    self.indexes += f'  {j["title"]} - {j["artist"]}\n'
                else:
                    self.indexes += f' {i+1} {j["title"]} - {j["artist"]}\n'
        else:
            self.indexes = f'Playlist: {self.playlist}\n'
            for i, j in enumerate(self.client.listplaylistinfo(self.playlist)):
                self.indexes += f' {i+1} {j["title"]}\n'


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
            if tmp == ' Go Back':
                if '/' in current_dir:
                    current_dir = current_dir[:current_dir.rfind('/')]
                else:
                    current_dir = ''
            elif tmp == ' Add all':
                client.add(current_dir)
            # Go to Playlist mode
            elif tmp == ' Playlist mode':
                playlist = rofi_playlist(client)
                while 1:
                    option.gen_options()
                    option.options[8] = f'[Playlist mode]{playlist.playlist}'
                    if playlist.playlist:
                        option.options[2] = '1'
                    rofi = subprocess.Popen(option.options, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
                    playlist.gen_index()
                    select = playlist.prefix + playlist.indexes
                    tmp = rofi.communicate(select.encode())[0].decode().rstrip()
                    if not tmp:
                        sys.exit()
                    else:
                        if tmp == ' Go Back to Main menu':
                            break
                        elif tmp == ' Go Back':
                            playlist.playlist = ''
                        elif tmp == ' Add this playlist':
                            client.load(playlist.playlist)
                        elif '' in tmp:
                            playlist.playlist = tmp.split()[-1]
                        else:
                            pass
            elif tmp == ' Clear Playlist':
                client.clear()
            elif tmp == ' Play':
                if not client.playlistinfo():
                    pass
                else:
                    client.play()
            elif tmp == ' Pause':
                client.pause()
            elif tmp == ' Next':
                client.next()
            elif '' in tmp:  # TODO: add functions
                pass
            else:
                if current_dir:
                    current_dir += '/' + tmp[4:]
                else:
                    current_dir = tmp[4:]


if __name__ == '__main__':
    main()
