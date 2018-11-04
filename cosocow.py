#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

CoSoCoW is a Command line Sonos Control Wrapper to manage a Network of Zones
by Python Console. The Wrapper uses the great SoCo library to establish an
UPnP connection to your speaker.

The MIT Licence

Copyright (C) 2018 Thomas Katemann

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

"""

import re
from soco import SoCo
import threading
from pprint import pprint
import datetime
import requests

__title__ = 'CoSoCoW'
__version__ = '1.1.0'
__author__ = 'Thomas Katemann'
__copyright__ = 'Copyright 2018 Thomas Katemann'
__license__ = 'MIT'


class CoSoCoW(object):
    def __init__(self, a_zone_ip=None):
        """

        :param a_zone_ip:
        """
        print('--- CoSoCoW Init ---')

        if a_zone_ip is not None:
            self.a_zone_ip = a_zone_ip
        else:
            # setup zone topology (stereo pair combined as sub list)
            self.a_zone_ip = [['192.168.178.24', '192.168.178.23'], '192.168.178.25']

        # control settings
        self.idx_verbosity_lvl = 3
        self.b_zone_ev_sub1_prnt = False
        self.b_zone_ev_sub2_prnt = False
        self.b_zone_ev_sub3_prnt = False
        self.b_zone_ev_sub4_prnt = False
        self.b_zone_ev_sub5_prnt = False
        self.b_print_str_type = True

        # init internal variables
        self.a_zone_soco = []
        self.a_zone_avail = []
        self.a_zone_name = []
        self.a_aux_avail_name = []
        self.a_aux_avail_src = []
        self.a_groups = []
        self.a_groups_chk = []
        self.a_group_co = []
        self.a_volume = []
        self.a_balance = []
        self.a_radio_fav = ''
        self.a_radio_fav_name = ''
        self.a_radio_fav_upd_idnew = []
        self.a_radio_fav_upd_idold = []
        self.a_radio_is_adv = [0, 0]
        self.a_mudb_upd_idnew = []
        self.a_mudb_upd_idold = []
        self.a_mudb_items = []
        self.a_mudb_items_name = []
        self.a_mudb_tracks = []
        self.a_mudb_tracks_name = []
        self.a_play_state = []
        self.a_play_track = []
        self.a_play_track_sub = []
        self.a_play_track_meta = []
        self.a_play_is_radio = []
        self.a_play_is_auxin = []
        self.a_play_is_mudb = []
        self.a_play_track_idx = []
        self.a_play_mode = []
        self.a_play_trans_state = []
        self.a_play_trans_status = []
        self.a_play_is_valid = []
        self.a_play_queue_size = []
        self.a_queue_rem_actv = []
        self.a_queue_upd_actv = []
        self.a_queue_upd_idold = []
        self.a_queue_upd_idnew = []
        self.a_queue_play_mode = []
        self.a_queue_play_list = []
        self.a_zone_ev_sub1 = []
        self.a_zone_ev_sub2 = []
        self.a_zone_ev_sub3 = []
        self.a_zone_ev_sub4 = []
        self.a_zone_ev_sub5 = []
        self.a_event2_last = []
        self.a_sleep_time_val = []
        self.b_evsub4_addturn = False
        self.b_groups_diff = False
        self.b_group_cng_actv = False
        self.ca0_cnt1 = 0
        self.ca0_b_init = True
        self.ca0_ct_init = 5

        # init event caller
        self.ev_groups = EventCall()
        self.ev_volume = EventCall()
        self.ev_balance = EventCall()
        self.ev_radio_fav = EventCall()
        self.ev_play_state = EventCall()
        self.ev_play_track = EventCall()
        self.ev_play_track_sub = EventCall()
        self.ev_play_track_idx = EventCall()
        self.ev_play_mode = EventCall()
        self.ev_queue_upd = EventCall()
        self.ev_sleep_time_val = EventCall()

        # initial method calls
        self.init_ctrl()
        self.init_arrays()
        self.get_zone_avail()
        self.get_groups()

        # initial call of cyclic threads
        self.cyclic_thread_0()
        self.cyclic_thread_1()
        self.cyclic_thread_2()

        print('--- CoSoCoW Init Finished ---')

    def __del__(self):
        """

        """
        print('close connection')

    def get_cmd_info(self, str_print, idx_verb_info):
        """
        create message in console
        :param str_print:
        :param idx_verb_info:
        """
        if self.idx_verbosity_lvl >= idx_verb_info:
            str_cur_time = str(datetime.datetime.time(datetime.datetime.now()))
            print(str_cur_time + ' ' + str_print)

    def chk_str(self, var_in, b_adapt=False):
        """
        check if variable is from type str or unicode
        :param var_in:
        :param b_adapt:
        :return:
        """
        b_print = False
        if b_print:
            print(str(var_in.__class__))

        if isinstance(var_in, str):
            return var_in
        elif str(var_in.__class__).find('unicode') is not -1:
            return var_in
        else:
            str_msg = 'var_in must be from type "str" or "unicode" but is ' + str(var_in.__class__)
            if b_adapt:
                if b_print:
                    print(str_msg)

                try:
                    var_out = str(var_in)
                except:
                    var_out = var_in.encode('utf8', 'replace').decode('utf8')

                return var_out
            else:
                raise ValueError(str_msg)

    def init_ctrl(self):
        """
        initialize SoCo
        """
        for z_ip_address in self.a_zone_ip:
            if isinstance(z_ip_address, str):
                # is single player
                z_req = SoCo(z_ip_address)
                self.a_zone_soco.append(z_req)
            else:
                # is pair
                z_req_pair = []
                for z_ip_address_sub in z_ip_address:
                    z_req = SoCo(z_ip_address_sub)
                    z_req_pair.append(z_req)
                self.a_zone_soco.append(z_req_pair)

    def init_arrays(self):
        """

        """
        num_zones = len(self.a_zone_soco)

        if len(self.a_zone_name) != num_zones:
            self.a_zone_name = [''] * num_zones

        if len(self.a_volume) != num_zones:
            self.a_volume = [0] * num_zones
        if len(self.a_balance) != num_zones:
            self.a_balance = [0] * num_zones

        if len(self.a_queue_play_list) != num_zones:
            self.a_queue_play_list = [0] * num_zones
        if len(self.a_queue_play_mode) != num_zones:
            self.a_queue_play_mode = [0] * num_zones

        if len(self.a_queue_upd_idold) != num_zones:
            self.a_queue_upd_idold = [0] * num_zones
        if len(self.a_queue_upd_idnew) != num_zones:
            self.a_queue_upd_idnew = [0] * num_zones
        if len(self.a_queue_upd_actv) != num_zones:
            self.a_queue_upd_actv = [False] * num_zones
        if len(self.a_queue_rem_actv) != num_zones:
            self.a_queue_rem_actv = [False] * num_zones

        if len(self.a_radio_fav_upd_idold) != num_zones:
            self.a_radio_fav_upd_idold = [0] * num_zones
        if len(self.a_radio_fav_upd_idnew) != num_zones:
            self.a_radio_fav_upd_idnew = [0] * num_zones

        if len(self.a_mudb_upd_idold) != num_zones:
            self.a_mudb_upd_idold = [0] * num_zones
        if len(self.a_mudb_upd_idnew) != num_zones:
            self.a_mudb_upd_idnew = [0] * num_zones

        if len(self.a_play_track) != num_zones:
            self.a_play_track = [0] * num_zones
        if len(self.a_play_track_meta) != num_zones:
            self.a_play_track_meta = [0] * num_zones
        if len(self.a_play_is_radio) != num_zones:
            self.a_play_is_radio = [0] * num_zones
        if len(self.a_play_is_auxin) != num_zones:
            self.a_play_is_auxin = [0] * num_zones
        if len(self.a_play_is_mudb) != num_zones:
            self.a_play_is_mudb = [0] * num_zones
        if len(self.a_play_track_idx) != num_zones:
            self.a_play_track_idx = [0] * num_zones
        if len(self.a_play_mode) != num_zones:
            self.a_play_mode = [0] * num_zones
        if len(self.a_play_trans_state) != num_zones:
            self.a_play_trans_state = [0] * num_zones
        if len(self.a_play_trans_status) != num_zones:
            self.a_play_trans_status = ['N/A'] * num_zones
        if len(self.a_play_is_valid) != num_zones:
            self.a_play_is_valid = [0] * num_zones
        if len(self.a_play_queue_size) != num_zones:
            self.a_play_queue_size = [0] * num_zones
        if len(self.a_play_track_sub) != num_zones:
            self.a_play_track_sub = [0] * num_zones
        if len(self.a_play_state) != num_zones:
            self.a_play_state = [0] * num_zones

        if len(self.a_event2_last) != num_zones:
            self.a_event2_last = [None] * num_zones
        if len(self.a_zone_ev_sub1) != num_zones:
            self.a_zone_ev_sub1 = [None] * num_zones
        if len(self.a_zone_ev_sub2) != num_zones:
            self.a_zone_ev_sub2 = [None] * num_zones
        if len(self.a_zone_ev_sub3) != num_zones:
            self.a_zone_ev_sub3 = [None] * num_zones
        if len(self.a_zone_ev_sub4) != num_zones:
            self.a_zone_ev_sub4 = [None] * num_zones
        if len(self.a_zone_ev_sub5) != num_zones:
            self.a_zone_ev_sub5 = [None] * num_zones

        if len(self.a_sleep_time_val) != num_zones:
            self.a_sleep_time_val = [None] * num_zones

    def cyclic_thread_0(self):
        """
        cyclic thread 0 for main tasks (ts = 100 ms)
        """
        if self.ca0_b_init:
            # init procedure
            self.ca0_b_init = False
            self.get_aux_avail_all()
        else:
            if self.ca0_cnt1 < self.ca0_ct_init:
                # post init phase
                self.ca0_cnt1 = self.ca0_cnt1 + 1

            elif self.ca0_cnt1 == self.ca0_ct_init:
                # after the post init phase
                self.get_sleep_timer(-2)
                self.get_volume(-1, True)
                self.get_balance(-1, True)
                self.ca0_cnt1 = self.ca0_cnt1 + 1
            else:
                pass

            # call always
            self.get_zone_events()
            self.get_groups()

        # cycle timer
        threading.Timer(0.1, self.cyclic_thread_0).start()

    def cyclic_thread_1(self):
        """
        cyclic thread 1: for updating queue, music db and favorites (ts = 100 ms)
        """
        num_zones = len(self.a_zone_soco)
        for idx in range(num_zones):

            # Update Queue
            if self.a_queue_upd_idnew[idx] != self.a_queue_upd_idold[idx]:
                self.get_play_queue(idx)
                self.a_queue_upd_idold[idx] = self.a_queue_upd_idnew[idx]
                self.a_queue_upd_actv[idx] = False

            # Update favorite radios
            if self.a_radio_fav_upd_idnew[idx] != self.a_radio_fav_upd_idold[idx]:
                self.get_radio_fav()
                self.a_radio_fav_upd_idold[idx] = self.a_radio_fav_upd_idnew[idx]

            # Update music db
            if self.a_mudb_upd_idold[idx] != self.a_mudb_upd_idnew[idx]:
                self.get_mudb_list(0)
                self.a_mudb_upd_idold[idx] = self.a_mudb_upd_idnew[idx]

        threading.Timer(0.1, self.cyclic_thread_1).start()

    def cyclic_thread_2(self):
        """
        cyclic thread 2: for sleep timer count (ts = 1 sec)
        """
        self.get_sleep_timer()
        threading.Timer(1, self.cyclic_thread_2).start()

    def get_zone(self, idx_zone=-1):
        """

        :param idx_zone:
        :return:
        """
        if idx_zone == -1:
            # All zones
            z_out = []
            num_zones = len(self.a_zone_soco)
            for idx in range(num_zones):
                if self.a_zone_avail[idx]:
                    if isinstance(self.a_zone_soco[idx], list):
                        z_out.append(self.a_zone_soco[idx][0])
                    else:
                        z_out.append(self.a_zone_soco[idx])
                else:
                    z_out.append(None)
        else:
            if self.a_zone_avail[idx_zone]:
                z_req = self.a_zone_soco[idx_zone]
                if isinstance(z_req, list):
                    z_out = z_req[0]
                else:
                    z_out = z_req
            else:
                z_out = None

        return z_out

    def get_zone_co_idx(self, idx_zone=-1):
        """
        get index of zone coordinator for required zone

        :param idx_zone: index of required zone
        :return:
        """
        if idx_zone == -1:
            z_out = self.a_group_co
        else:
            z_out = self.a_group_co[idx_zone]
        return z_out

    def get_zone_avail(self):
        self.a_zone_name = []
        self.a_zone_avail = []
        for z_req in self.a_zone_soco:
            if isinstance(z_req, list):
                try:
                    for z_req_sub in z_req:
                        s_sp_info = z_req_sub.get_speaker_info()
                        str_zone_name = s_sp_info.get('zone_name')
                        str_player = s_sp_info.get('model_name')
                        self.get_cmd_info(str(z_req_sub) + ' : ' + str_zone_name,2)
                        self.get_cmd_info(str(z_req_sub) + ' : ' + str_player, 2)
                        #model_name
                    self.a_zone_name.append(str_zone_name)
                    self.a_zone_avail.append(True)
                except (OSError, ValueError):
                    self.a_zone_name.append('')
                    self.a_zone_avail.append(False)
                    print('Zone not Avail: ' + str(z_req))

            else:
                try:
                    s_sp_info = z_req.get_speaker_info()
                    str_zone_name = s_sp_info.get('zone_name')
                    str_player = s_sp_info.get('model_name')
                    self.get_cmd_info(str(z_req) + ' : ' + str_zone_name, 2)
                    self.get_cmd_info(str(z_req) + ' : ' + str_player, 2)
                    self.a_zone_name.append(str_zone_name)
                    self.a_zone_avail.append(True)
                except (OSError, ValueError):
                    self.a_zone_name.append('')
                    self.a_zone_avail.append(False)
                    print('Zone not Avail: ' + str(z_req))
        return self.a_zone_avail

    def get_groups(self):
        """
        get current group setup
        :return:
        """
        num_zones = len(self.a_zone_soco)
        self.a_groups = []
        self.a_group_co = [0] * num_zones

        for idx_zone1 in range(num_zones):
            a_grp_cur = []

            z_req1 = self.get_zone(idx_zone1)
            if z_req1 is not None:
                # if zone avail, loop over zones
                for idx_zone2 in range(num_zones):

                    z_req2 = self.get_zone(idx_zone2)
                    if z_req2 is not None:
                        if z_req1 in self.get_zone(idx_zone2).group.members:
                            # is grouped
                            a_grp_cur.append(idx_zone2)

                        if self.get_zone(idx_zone1).group.coordinator == z_req2:
                            # get coordinator
                            self.a_group_co[idx_zone1] = idx_zone2

                    else:
                        pass
            else:
                pass

            self.a_groups.append(a_grp_cur)

        self.ev_groups(self.a_groups, self.a_group_co)
        return [self.a_groups, self.a_group_co]

    def set_group(self, str_action, idx_main_zone, idx_join_zone=0):
        """
        set required group setup
        :param str_action:
        :param idx_main_zone:
        :param idx_join_zone:
        """
        z_req_main = self.get_zone(idx_main_zone)
        z_req_join = self.get_zone(idx_join_zone)
        if str_action == 'Join':
            # z_req_join joins z_req_main
            self.get_cmd_info(' # Join Grp: ' + str(idx_join_zone) + ' -> ' + str(idx_main_zone), 2)
            z_req_join.join(z_req_main)
            self.get_cmd_info(' # Join Grp: done', 2)
        elif str_action == 'UnJoin':
            # z_req_main unjoin from its group
            self.get_cmd_info(' # UnJoin Grp: ' + str(idx_main_zone), 2)
            z_req_main.unjoin()
            self.get_cmd_info(' # UnJoin Grp: done', 2)
        elif str_action == 'CngCo':
            # z_req_main unjoin from its group
            if self.a_groups[idx_main_zone].count(idx_join_zone) > 0:
                if self.a_group_co[idx_main_zone] != idx_join_zone:
                    self.get_cmd_info(' # Change Grp Co: ' + str(idx_main_zone) + ' -> ' + str(idx_join_zone), 2)
                    self.b_group_cng_actv = True
                    z_req_coo = self.get_zone(self.a_group_co[idx_main_zone])
                    z_req_coo.unjoin()
                    z_req_coo.join(z_req_join)
                    self.b_group_cng_actv = False
                    self.get_cmd_info(' # Change Grp Co: done', 2)

    def get_radio_fav(self, idx_zone=0):
        """
        get favorite radio stations
        :param idx_zone:
        :return:
        """
        z_req = self.get_zone(idx_zone)
        if z_req is None:
            return  # Not available

        a_radio_fav = z_req.music_library.get_favorite_radio_stations()
        # get names of radios
        a_radio_fav_name = []
        for itRadio in a_radio_fav:
            strTitle = itRadio.title
            a_radio_fav_name.append(strTitle)
        # if favorite list has changed
        if self.a_radio_fav != a_radio_fav:
            self.get_cmd_info(' :3 get_radio_fav: new radios', 2)
            self.a_radio_fav = a_radio_fav
            self.a_radio_fav_name = a_radio_fav_name
            self.ev_radio_fav(idx_zone, a_radio_fav_name)
        else:
            self.get_cmd_info(' :3 get_radio_fav: NO new radios', 2)

    def get_mudb_tracks(self, idx_zone, idx_db_type, idx_item):
        """
        get tracks from selected music db source type item
        :param idx_zone:
        :param idx_db_type:
        :param idx_item:
        """
        z_req = self.get_zone(idx_zone)
        self.a_mudb_tracks = z_req.music_library.get_tracks(self.a_mudb_items[idx_db_type][idx_item], 1000)
        self.a_mudb_tracks_name = []
        for mudb_track in self.a_mudb_tracks:
            self.a_mudb_tracks_name.append(mudb_track.title)

    def get_mudb_list(self, idx_zone):
        """
        get music db source type items
        :param idx_zone:
        """
        z_req = self.get_zone(idx_zone)

        self.a_mudb_items = []
        self.a_mudb_items_name = []

        for idx_db_type in range(3):
            art1 = None
            if idx_db_type == 0:
                self.get_cmd_info(' :3 get Music DB Artists', 2)
                art1a = z_req.music_library.get_artists(0, 1000)
                art1b = z_req.music_library.get_artists(1000, 1000)
                art1 = art1a + art1b

            if idx_db_type == 1:
                self.get_cmd_info(' :3 get Music DB Album', 2)
                art1 = z_req.music_library.get_albums(0, 1000)

            if idx_db_type == 2:
                self.get_cmd_info(' :3 get Music DB Genre', 2)
                art1 = z_req.music_library.get_genres(0, 1000)

            self.a_mudb_items.append(art1)
            art_list = list()
            for idx1 in range(0, len(art1)):
                art_list.append(art1[idx1].title)
            self.a_mudb_items_name.append(art_list)

    def add_mudb_queue_item(self, idx_zone=0, idx_type=0, idx_item=0):
        """
        add music db item to play queue
        :param idx_zone:
        :param idx_type:
        :param idx_item:
        """
        z_req = self.get_zone(idx_zone)
        z_req.add_to_queue(self.a_mudb_items[idx_type][idx_item])

    def rem_mudb_queue_item(self, idx_zone=0, idx_type=0, idx_row=0):
        """
        remove music db item to play queue
        :param idx_zone:
        :param idx_type:
        :param idx_row:
        """
        z_req = self.get_zone(idx_zone)
        if idx_type < 0:
            z_req.clear_queue()
        else:
            self.a_queue_rem_actv[idx_zone] = True
            if isinstance(idx_row, list):
                for idx in idx_row:
                    z_req.remove_from_queue(int(idx))
                    self.get_cmd_info(' Remove Item from Queue: ' + str(idx), 2)
            else:
                if idx_row < 0:
                    idx_row = 0
                z_req.remove_from_queue(int(idx_row))
                self.get_cmd_info(' Remove Item from Queue: ' + str(idx_row), 2)
            self.a_queue_rem_actv[idx_zone] = False

    def get_aux_avail_all(self):
        """
        get all available aux sources
        """
        num_zones = len(self.a_zone_soco)
        self.a_aux_avail_name = []
        self.a_aux_avail_src = []
        for idxZ in range(num_zones):

            z_req = self.a_zone_soco[idxZ]
            if isinstance(z_req, list):
                for z_req_sub in z_req:
                    str_name, str_type = self.get_aux_avail(z_req_sub)
                    if str_type == 'AudioComponent':
                        aux_tmp = [str_name, z_req_sub]
                        self.a_aux_avail_name.append(str_name)
                        self.a_aux_avail_src.append(z_req_sub)
                        self.get_cmd_info(' :x Aux: ' + str(aux_tmp), 2)
            else:
                str_type, str_name = self.get_aux_avail(z_req)
                if str_type == 'AudioComponent':
                    aux_tmp = [str_name, z_req]
                    self.a_aux_avail_name.append(str_name)
                    self.a_aux_avail_src.append(z_req)
                    self.get_cmd_info(' :x Aux: ' + str(aux_tmp), 2)

    def get_aux_avail(self, z_cur):
        """
        get available aux source
        :param z_cur:
        :return:
        """
        base_url = 'http://{}:1400'.format(z_cur.ip_address)
        control_url = '/{}/Control'.format('AudioIn')
        h1, b1 = z_cur.deviceProperties.build_command('GetAudioInputAttributes')
        h1['SOAPACTION'] = h1.get('SOAPACTION').replace('DeviceProperties', 'AudioIn')
        b1 = b1.replace('DeviceProperties', 'AudioIn')
        response = requests.post(base_url + control_url, headers=h1, data=b1.encode('utf-8'))
        str_aux_name = self.str_split(response.text, '<CurrentName>', '</CurrentName>')
        str_aux_type = self.str_split(response.text, '<CurrentIcon>', '</CurrentIcon>')
        return str_aux_name, str_aux_type

    def set_aux_play(self, idx_zone=0, idx_aux=0):
        """
        set aux source to play from
        :param idx_zone:
        :param idx_aux:
        """
        z_req = self.get_zone(idx_zone)
        z_aux = self.a_aux_avail_src[idx_aux]

        z_req.switch_to_line_in(z_aux)
        z_req.play()

    def set_radio_play(self, idx_zone=0, str_radio=None, idx_radio=None):
        """
        set radio to play
        :param idx_zone:
        :param str_radio:
        :param idx_radio:
        :return:
        """
        idx_coo = self.get_zone_co_idx(idx_zone)
        z_req = self.get_zone(idx_coo)

        if idx_radio is not None:
            str_radio = self.a_radio_fav_name[idx_radio]
            str_radio = ''.join(e for e in str_radio if e.isalnum() or e == ' ')

        elif str_radio is not None:
            if str_radio in self.a_radio_fav_name:
                idx_radio = self.a_radio_fav_name.index(str_radio)
            else:
                self.get_cmd_info(' :x Can not find radio: ' + str_radio, 2)
                return

        str_uri_play = self.a_radio_fav[idx_radio].get_uri()
        try:
            z_req.play_uri(str_uri_play, "", str_radio)
            self.get_cmd_info(' :x set_radio: ' + str_radio, 2)
        except:
            self.get_cmd_info(' :x Can not play radio: ' + str_radio, 2)

    def set_queue_track_play(self, idx_zone=0, idx_row=1):
        """
        set track from queue to play
        :param idx_zone:
        :param idx_row:
        """
        self.get_cmd_info('PlayQueue:' + str(idx_zone) + ' T:' + str(idx_row), 2)
        z_req = self.get_zone(idx_zone)
        trans_info = z_req.get_current_transport_info()
        str_trans_state = trans_info['current_transport_state']
        if str_trans_state != 'TRANSITIONING':
            try:
                z_req.play_from_queue(idx_row)
            except:
                self.get_cmd_info('set_queue_track_play: Can not play!', 2)
        else:
            self.get_cmd_info('set_queue_track_play: Just in TRANSITIONING', 2)

    def set_play_start_stop(self, idx_zone=0, idx_play=-1):
        """
        set music playing start or stop
        :param idx_zone: index of required zone
        :param idx_play: index to select play or pause
        :rtype: no return object
        """
        idx_co = self.get_zone_co_idx(idx_zone)
        z_req = self.get_zone(idx_co)

        if idx_play == -1:
            trans_info = z_req.get_current_transport_info()
            str_trans_state = trans_info['current_transport_state']
            if str_trans_state != 'TRANSITIONING':
                if str_trans_state == 'PLAYING':
                    z_req.pause()
                else:
                    try:
                        z_req.play()
                    except:
                        self.get_cmd_info('set_play_start_stop: Can not play!', 2)
            else:
                self.get_cmd_info('set_play_start_stop: Just in TRANSITIONING', 2)

        elif idx_play == 0:
            z_req.pause()
        elif idx_play == 1:
            try:
                z_req.play()
            except:
                self.get_cmd_info('set_play_start_stop: Can not play!', 2)

    def set_play_track_next(self, idx_zone=0, str_dir='Next'):
        """
        set next track to play
        :param idx_zone:
        :param str_dir:
        """
        if self.a_play_is_mudb[idx_zone]:
            # mudb is playing
            self.get_cmd_info(' : Change track to: ' + str(idx_zone) + ': ' + str(str_dir), 2)

            z_req = self.get_zone(idx_zone)
            if str_dir == 'Next':
                if int(self.a_play_track_idx[idx_zone]) < self.a_play_queue_size[idx_zone] \
                        or (self.a_play_mode[idx_zone].find('NOREPEAT') == -1
                            and self.a_play_mode[idx_zone] != 'NORMAL'):

                    z_req.next()

            elif str_dir == 'Prev':
                if int(self.a_play_track_idx[idx_zone]) > 1 \
                        or (self.a_play_mode[idx_zone].find('NOREPEAT') == -1
                            and self.a_play_mode[idx_zone] != 'NORMAL'):

                    z_req.previous()

    def get_volume(self, idx_zone=-1, b_init=False):
        """
        get volume from speaker
        :param idx_zone:
        :param b_init:
        :return:
        """
        if idx_zone == -1:
            # all zones
            num_zones = len(self.a_zone_soco)
            for idx_z_cur in range(num_zones):
                z_req = self.get_zone(idx_z_cur)

                if z_req is None:
                    d_vol_cur = -1  # zone not available
                else:
                    if isinstance(z_req, list):
                        d_vol_cur = z_req[0].volume
                    else:
                        d_vol_cur = z_req.volume

                if d_vol_cur != self.a_volume[idx_z_cur] or b_init:
                    self.a_volume[idx_z_cur] = d_vol_cur
                    self.ev_volume(idx_z_cur, d_vol_cur)  # call external method
                    self.get_cmd_info(' :1 get_volume: Z' + str(idx_z_cur) + ': ' + str(d_vol_cur), 2)

            return self.a_volume

        else:
            # specific zone
            z_req = self.get_zone(idx_zone)
            if z_req is None:
                return -1  # zone not available

            if isinstance(z_req, list):
                d_vol_cur = z_req[0].volume
            else:
                d_vol_cur = z_req.volume

            if d_vol_cur != self.a_volume[idx_zone]:
                self.a_volume[idx_zone] = d_vol_cur
                self.get_cmd_info(' :1 get_volume: Z' + str(idx_zone) + ': ' + str(d_vol_cur), 2)

            return self.a_volume[idx_zone]

    """ set volume of zone """

    def set_volume(self, idx_zone, str_action, value):
        """
        set volume to speaker
        :param idx_zone:
        :param str_action:
        :param value:
        :return:
        """
        # chanage volume
        if str_action == 'equal':
            # print('# Volume Equal')
            z_req_all = self.get_zone(-1)
            for z_req in z_req_all:
                if z_req is not None:
                    z_req.volume = value
        else:
            z_req = self.get_zone(idx_zone)
            if z_req is None:
                return  # zone not available

            if str_action == 'up':
                # print('# Volume Up')
                z_req.volume = z_req.volume + value

            elif str_action == 'dn':
                # print('# Volume Down')
                value = -1 * value
                z_req.volume = z_req.volume + value

            elif str_action == 'value':
                # print('# Volume Down')
                z_req.volume = value

    def get_balance(self, idx_zone=-1, b_init=False):
        """
        get balance from speaker
        :param idx_zone:
        :param b_init:
        :return:
        """
        if idx_zone == -1:
            # all zones
            num_zones = len(self.a_zone_soco)
            for idx_z_cur in range(num_zones):
                z_req = self.get_zone(idx_z_cur)
                if z_req is None:
                    d_cur_bal_val = -111  # zone not available
                else:

                    if isinstance(z_req, list):
                        d_cur_vol_left = z_req[0].renderingControl.GetVolume([('InstanceID', 0), ('Channel', 'LF')])
                        d_cur_vol_right = z_req[0].renderingControl.GetVolume([('InstanceID', 0), ('Channel', 'RF')])
                    else:
                        d_cur_vol_left = z_req.renderingControl.GetVolume([('InstanceID', 0), ('Channel', 'LF')])
                        d_cur_vol_right = z_req.renderingControl.GetVolume([('InstanceID', 0), ('Channel', 'RF')])

                    d_cur_vol_left_val = int(d_cur_vol_left['CurrentVolume'])
                    d_cur_vol_right_val = int(d_cur_vol_right['CurrentVolume'])
                    d_cur_bal_val = d_cur_vol_right_val - d_cur_vol_left_val

                if d_cur_bal_val != self.a_balance[idx_z_cur] or b_init:
                    self.a_balance[idx_z_cur] = d_cur_bal_val
                    self.ev_balance(idx_z_cur, d_cur_bal_val)  # call external method
                    self.get_cmd_info(' :1 get_balance: Z' + str(idx_z_cur) + ': ' + str(d_cur_bal_val), 2)

            return self.a_balance

    """ set balance of zone """

    def set_balance(self, idx_zone, str_action, value=5):
        """
        set balance to speaker
        :param idx_zone:
        :param str_action:
        :param value:
        :return:
        """
        # chanage balance
        z_req = self.get_zone(idx_zone)
        if z_req is None:
            return  # zone not available

        d_cur_vol_left = z_req.renderingControl.GetVolume([('InstanceID', 0), ('Channel', 'LF')])
        d_cur_vol_right = z_req.renderingControl.GetVolume([('InstanceID', 0), ('Channel', 'RF')])
        d_cur_vol_left_val = int(d_cur_vol_left['CurrentVolume'])
        d_cur_vol_right_val = int(d_cur_vol_right['CurrentVolume'])

        if str_action == 'left':
            # print('# Balance Left')
            if d_cur_vol_left_val >= d_cur_vol_right_val:
                d_cur_vol_left_val = 100
                d_cur_vol_right_val = d_cur_vol_right_val - value
            else:
                d_cur_vol_right_val = 100
                d_cur_vol_left_val = d_cur_vol_left_val + value

        elif str_action == 'right':
            # print('# Balance Right')
            if d_cur_vol_left_val <= d_cur_vol_right_val:
                d_cur_vol_right_val = 100
                d_cur_vol_left_val = d_cur_vol_left_val - value
            else:
                d_cur_vol_left_val = 100
                d_cur_vol_right_val = d_cur_vol_right_val + value

        elif str_action == 'equal':
            # print('# Balance Equal')
            d_cur_vol_left_val = 100
            d_cur_vol_right_val = 100

        d_cur_vol_left_val = max(0, min(d_cur_vol_left_val, 100))
        d_cur_vol_right_val = max(0, min(d_cur_vol_right_val, 100))
        z_req.renderingControl.SetVolume([('InstanceID', 0), ('Channel', 'LF'), ('DesiredVolume', int(d_cur_vol_left_val))])
        z_req.renderingControl.SetVolume([('InstanceID', 0), ('Channel', 'RF'), ('DesiredVolume', int(d_cur_vol_right_val))])

    def get_play_queue(self, idx_zone):
        """
        get current play queue list
        :param idx_zone:
        """
        z_req = self.get_zone(idx_zone)

        self.get_cmd_info(' :3 Read Queue' + str(idx_zone), 2)

        if self.a_play_mode[idx_zone] != self.a_queue_play_mode[idx_zone]:
            self.get_cmd_info(' :3 PlayMode change to: ' + self.a_play_mode[idx_zone], 2)
            self.a_queue_play_mode[idx_zone] = self.a_play_mode[idx_zone]

        idx_start = 0
        idx_end = 1000
        queue = list()
        num_queue_size = int(z_req.queue_size)
        idx1000 = int(num_queue_size / 1000)
        for idx2 in range(idx1000 + 1):
            queue.append(z_req.get_queue(idx_start + 1000 * idx2, idx_end + 1000 * idx2))

        queuelist = list()
        for idx1 in range(0, len(queue)):
            for idx2 in range(0, len(queue[idx1])):
                queuelist.append(queue[idx1][idx2].title)

        self.get_cmd_info(' :3 Read Queue' + str(idx_zone) + ' done', 2)

        if self.a_play_queue_size[idx_zone] != num_queue_size:
            self.a_play_queue_size[idx_zone] = num_queue_size
            self.get_cmd_info(' :3 a_play_queue_size: ' + str(idx_zone) + ': ' + str(num_queue_size), 2)

        if self.a_queue_play_list[idx_zone] != queuelist:
            self.a_queue_play_list[idx_zone] = queuelist

            self.ev_queue_upd(idx_zone, queuelist)

            cur_track_idx = self.a_play_track_idx[idx_zone]
            self.ev_play_track_idx(idx_zone, int(cur_track_idx))  # call external method
        else:
            self.get_cmd_info(' :3 No Queue change', 2)

    def get_play_status(self, idx_zone=0, event_var=None):
        """
        get status of current play activity
        :param idx_zone:
        :param event_var:
        :return:
        """

        # get zone coordinator
        idx_coo = self.get_zone_co_idx(idx_zone)

        if idx_coo != idx_zone:
            self.get_cmd_info(' :2 get_play_status: Z' + str(idx_zone) + '  Not the Coord: C:' + str(idx_coo), 2)
            return

        z_req = self.get_zone(idx_coo)

        if event_var is None:
            return
        if 'transport_state' not in event_var.keys():
            return

        obj_trans_state = event_var['transport_state']
        str_trans_state = self.chk_str(obj_trans_state)

        if 'transport_status' in event_var.keys():
            obj_trans_status = event_var['transport_status']
            str_trans_status = self.chk_str(obj_trans_status)
        else:
            str_trans_status = None

        b_is_mudb = False
        b_is_aux_in = z_req.is_playing_line_in

        obj_cur_track_meta = event_var['current_track_meta_data']
        if obj_cur_track_meta == '':
            str_cur_track_meta = ''
        else:
            str_cur_track_meta = self.chk_str(obj_cur_track_meta.title, True)

        # name of track source (e.g. radio name, playlist)
        obj_cur_play_src = event_var['enqueued_transport_uri_meta_data']
        if obj_cur_play_src == '':
            # no source found in this obj
            if obj_cur_track_meta == '':
                str_cur_play_src = '- No Music -'
            else:
                if b_is_aux_in:
                    str_cur_play_src = str_cur_track_meta  # line in name
                else:
                    str_cur_play_src = 'Music Source Lost'
        else:
            str_cur_play_src = self.chk_str(obj_cur_play_src.title, True)

        if not str_cur_play_src == '- No Music -':
            b_track_is_valid = True  # FIXME
        else:
            b_track_is_valid = True

        if str_trans_status is not None and str_trans_status == 'ERROR_CANT_REACH_SERVER':
            str_cur_play_src = 'ERROR_CANT_REACH_SERVER'

        # check if is radio
        obj_cur_play_uri = event_var['enqueued_transport_uri']
        b_is_radio = re.match(r'^x-sonosapi-stream:', obj_cur_play_uri) is not None

        # track display name (e.g artist + song title)
        track_info = z_req.get_current_track_info()
        if b_is_aux_in:
            # aux in name
            str_track_disp_name = str_cur_track_meta
        else:
            if b_is_radio:
                # if radio use track_info as source
                str_track_disp_name = self.chk_str(track_info['artist']) + ' - ' + self.chk_str(track_info['title'])
            else:
                # if mudb track
                str_track_disp_name = str_cur_track_meta
                b_is_mudb = True

        if str_track_disp_name.count('ref=tunein&') > 0 and False:
            self.a_radio_is_adv[idx_coo] = self.get_volume(idx_coo)
            str_track_disp_name = 'ADVERT'
            self.set_volume(idx_coo, 'value', 0)
            self.get_volume(idx_coo)

        else:
            if self.a_radio_is_adv[idx_coo] > 0 and False:
                self.set_volume(idx_coo, 'value', self.a_radio_is_adv[idx_coo])
                self.a_radio_is_adv[idx_coo] = 0
                self.get_volume(idx_coo)

        try:
            int_cur_track_idx = int(event_var['current_track'])
        except:
            int_cur_track_idx = -1

        str_cur_play_mode = self.chk_str(event_var['current_play_mode'])

        # get groups
        a_cur_group = self.a_groups[idx_coo]
        for idx_z_grp in a_cur_group:

            # current track sub
            if str_track_disp_name != self.a_play_track_sub[idx_z_grp]:

                if self.b_print_str_type:
                    str_print_disp = ' :2 a_play_track_sub: ' + str(a_cur_group) + ': ' \
                                     + str_track_disp_name + ' : ' + str(str_track_disp_name.__class__)
                else:
                    str_print_disp = ' :2 a_play_track_sub: ' + str(a_cur_group) + ': ' + str_track_disp_name

                if idx_coo == idx_z_grp:
                    self.get_cmd_info(str_print_disp, 2)
                else:
                    if self.b_groups_diff:
                        self.get_cmd_info(str_print_disp, 2)

                self.a_play_track_sub[idx_z_grp] = str_track_disp_name
                self.ev_play_track_sub(idx_z_grp, str_track_disp_name)

            # current track
            if str_cur_play_src != self.a_play_track[idx_z_grp]:

                if self.b_print_str_type:
                    str_print_src = ' :2 a_play_track: ' + str(a_cur_group) + ': ' \
                                     + str_cur_play_src + ' : ' + str(str_cur_play_src.__class__)
                else:
                    str_print_src = ' :2 a_play_track: ' + str(a_cur_group) + ': ' + str_cur_play_src

                if idx_coo == idx_z_grp:
                    self.get_cmd_info(str_print_src, 2)
                else:
                    if self.b_groups_diff:
                        self.get_cmd_info(str_print_src, 2)

                self.a_play_track[idx_z_grp] = str_cur_play_src
                self.ev_play_track(idx_z_grp, str_cur_play_src)

            # current track meta
            if str_cur_track_meta != self.a_play_track_meta[idx_z_grp]:

                if self.b_print_str_type:
                    str_print_meta = ' :2 a_play_track_meta: ' + str(a_cur_group) + ': ' \
                                     + str_cur_track_meta + ' : ' + str(str_cur_track_meta.__class__)
                else:
                    str_print_meta = ' :2 a_play_track_meta: ' + str(a_cur_group) + ': ' + str_cur_track_meta

                if idx_coo == idx_z_grp:
                    self.get_cmd_info(str_print_meta, 2)

                self.a_play_track_meta[idx_z_grp] = str_cur_track_meta

            # is radio
            if b_is_radio != self.a_play_is_radio[idx_z_grp]:
                if idx_coo == idx_z_grp:
                    self.get_cmd_info(' :2 a_play_is_radio: ' + str(a_cur_group) + ': ' + str(b_is_radio), 2)
                self.a_play_is_radio[idx_z_grp] = b_is_radio

            # is Aux in
            if b_is_aux_in != self.a_play_is_auxin[idx_z_grp]:
                if idx_coo == idx_z_grp:
                    self.get_cmd_info(' :2 a_play_is_auxin: ' + str(a_cur_group) + ': ' + str(b_is_aux_in), 2)
                self.a_play_is_auxin[idx_z_grp] = b_is_aux_in

            # is mudb
            if b_is_mudb != self.a_play_is_mudb[idx_z_grp]:
                if idx_coo == idx_z_grp:
                    self.get_cmd_info(' :2 a_play_is_mudb: ' + str(a_cur_group) + ': ' + str(b_is_mudb), 2)
                self.a_play_is_mudb[idx_z_grp] = b_is_mudb

            # current track index
            if int_cur_track_idx != self.a_play_track_idx[idx_z_grp]:
                if idx_coo == idx_z_grp:
                    self.get_cmd_info(' :2 a_play_track_idx: '
                                      + str(a_cur_group) + ': ' + str(int_cur_track_idx), 2)
                else:
                    if self.b_groups_diff:
                        self.get_cmd_info(' :2 a_play_track_idx NotCo: '
                                          + str(idx_z_grp) + ': ' + str(int_cur_track_idx), 2)
                self.a_play_track_idx[idx_z_grp] = int_cur_track_idx

                if not self.a_play_is_radio[idx_z_grp] \
                        and not self.a_play_is_auxin[idx_z_grp] \
                        and not self.a_queue_upd_actv[idx_z_grp]:
                    if self.b_group_cng_actv is False and (idx_coo == idx_z_grp or self.b_groups_diff):
                        # mark current track
                        self.get_cmd_info(' :2 Select Track: '
                                          + str(idx_z_grp) + ': ' + str(int_cur_track_idx), 2)
                        val1 = int(int_cur_track_idx)
                        self.ev_play_track_idx(idx_z_grp, val1)  # call external method

            # current track index
            if str_cur_play_mode != self.a_play_mode[idx_z_grp]:
                if idx_coo == idx_z_grp:
                    self.get_cmd_info(' :2 a_play_mode: ' + str(a_cur_group) + ': ' + str_cur_play_mode, 2)
                self.a_play_mode[idx_z_grp] = str_cur_play_mode
                self.ev_play_mode(idx_z_grp, str_cur_play_mode)

            # current transport state
            if str_trans_state != self.a_play_trans_state[idx_z_grp]:
                if idx_coo == idx_z_grp:
                    self.get_cmd_info(' :2 a_play_trans_state: ' + str(a_cur_group) + ': ' + str_trans_state, 2)
                self.a_play_trans_state[idx_z_grp] = str_trans_state

            # current transport status
            if str_trans_status != self.a_play_trans_status[idx_z_grp] and str_trans_status is not None:
                if idx_coo == idx_z_grp:
                    self.get_cmd_info(' :2 a_play_trans_status: ' + str(a_cur_group) + ': ' + str_trans_status, 2)
                self.a_play_trans_status[idx_z_grp] = str_trans_status

            # current play valid
            if b_track_is_valid != self.a_play_is_valid[idx_z_grp]:
                if idx_coo == idx_z_grp:
                    self.get_cmd_info(' :2 a_play_is_valid: ' + str(a_cur_group) + ': ' + str(b_track_is_valid), 2)
                self.a_play_is_valid[idx_z_grp] = b_track_is_valid

            if self.a_play_is_valid[idx_z_grp]:
                if self.a_play_is_radio[idx_z_grp]:
                    str_track_idx_disp = '\nRADIO'
                elif self.a_play_is_auxin[idx_z_grp]:
                    # is radio or aux
                    str_track_idx_disp = '\nAUX'
                else:
                    str_track_idx_disp = '\nPL' + str(self.a_play_track_idx[idx_z_grp])

                if self.a_play_trans_state[idx_z_grp] == 'PLAYING':
                    cur_play_state = 'PLAY' + str_track_idx_disp
                elif self.a_play_trans_state[idx_z_grp] == 'PAUSED_PLAYBACK':
                    cur_play_state = 'PAUSE' + str_track_idx_disp
                else:
                    cur_play_state = 'STOP'

                if self.a_play_state[idx_z_grp] != cur_play_state:
                    # print cur_play_state
                    self.a_play_state[idx_z_grp] = cur_play_state
                    self.ev_play_state(idx_z_grp, cur_play_state)  # call external method

    def get_zone_events(self):
        """
        receive events from the zone player
        """
        num_zones = len(self.a_zone_soco)

        # detect change of groups
        if self.b_evsub4_addturn is True:
            self.get_groups()
            if self.a_groups != self.a_groups_chk:
                self.b_groups_diff = True  # if groups have changed
                self.get_cmd_info(' # CurGroups: ' + str(self.a_groups) + ' Co: ' + str(self.a_group_co), 2)
                for idx in self.a_group_co:
                    self.get_play_status(idx, self.a_event2_last[idx])
                self.a_groups_chk = self.a_groups
                self.b_groups_diff = False
                self.b_evsub4_addturn = False

        # loop over zones
        for idx in range(num_zones):

            # get Zones
            z_req = self.get_zone(idx)

            # if zone is not available
            if z_req is None:
                continue

            try:
                # 1 renderingControl
                if self.a_zone_ev_sub1[idx] is None or not self.a_zone_ev_sub1[idx].is_subscribed:
                    self.a_zone_ev_sub1[idx] = z_req.renderingControl.subscribe()
                if not self.a_zone_ev_sub1[idx].events.empty():
                    event = self.a_zone_ev_sub1[idx].events.get(timeout=0.5)
                    b_is_avail1 = True
                else:
                    b_is_avail1 = False
            except:
                b_is_avail1 = False

            if b_is_avail1:
                self.get_cmd_info('### E1 Z:' + str(idx) + ' Sound', 4)

                event_var = event.variables
                if self.b_zone_ev_sub1_prnt:
                    pprint(event_var)
                    print('\n')

                self.get_volume()
                self.get_balance()

            if True:
                # 3 contentDirectory
                try:
                    if self.a_zone_ev_sub3[idx] is None or not self.a_zone_ev_sub3[idx].is_subscribed:
                        self.a_zone_ev_sub3[idx] = z_req.contentDirectory.subscribe()
                    if not self.a_zone_ev_sub3[idx].events.empty():
                        event = self.a_zone_ev_sub3[idx].events.get(timeout=0.5)
                        b_is_avail3 = True
                    else:
                        b_is_avail3 = False
                except:
                    b_is_avail3 = False

                if b_is_avail3:
                    self.get_cmd_info('### E3 Z:' + str(idx) + ' Queue', 4)

                    event_var = event.variables
                    if self.b_zone_ev_sub3_prnt:
                        pprint(event_var)

                    if 'container_update_i_ds' in event_var.keys():
                        container_update_i_ds = event_var['container_update_i_ds']
                        if self.a_queue_upd_idnew[idx] != container_update_i_ds:
                            if self.a_queue_rem_actv[idx] == False and self.b_group_cng_actv == False:
                                # no queue update while queue item removing or group change is active
                                self.a_queue_upd_actv[idx] = True
                                self.get_cmd_info(' :3 a_queue_upd_idnew: ' + container_update_i_ds, 3)
                                self.a_queue_upd_idnew[idx] = container_update_i_ds
                            else:
                                self.get_cmd_info(' :3 Queue update: suppressed', 3)

                    if 'favorites_update_id' in event_var.keys():
                        favorites_update_id = event_var['favorites_update_id']
                        if self.a_radio_fav_upd_idnew[idx] != favorites_update_id:
                            self.get_cmd_info(' :3 a_radio_fav_upd_idnew: ' + favorites_update_id, 3)
                            self.a_radio_fav_upd_idnew[idx] = favorites_update_id

                    if 'share_list_update_id' in event_var.keys():
                        share_list_update_id = event_var['share_list_update_id']
                        if self.a_mudb_upd_idnew[idx] != share_list_update_id:
                            self.get_cmd_info(' :3 a_mudb_upd_idnew: ' + share_list_update_id, 3)
                            self.a_mudb_upd_idnew[idx] = share_list_update_id

            if True:
                # 2 avTransport
                try:
                    if self.a_zone_ev_sub2[idx] is None or not self.a_zone_ev_sub2[idx].is_subscribed:
                        self.a_zone_ev_sub2[idx] = z_req.avTransport.subscribe()
                    if not self.a_zone_ev_sub2[idx].events.empty():
                        event2 = self.a_zone_ev_sub2[idx].events.get(timeout=0.5)
                        b_is_avail2 = True
                    else:
                        b_is_avail2 = False
                except:
                    b_is_avail2 = False

                if b_is_avail2:
                    self.get_cmd_info('### E2 Z:' + str(idx) + ' Track', 4)

                    event_var = event2.variables
                    if self.b_zone_ev_sub2_prnt:
                        pprint(event_var)
                        print('\n')

                    if 'sleep_timer_generation' in event_var.keys():
                        sleep_timer_generation = event_var['sleep_timer_generation']
                        self.get_sleep_timer(idx)

                        self.get_cmd_info(' :3 sleep_timer_generation: ' + sleep_timer_generation, 2)
                    if 'transport_state' in event_var.keys():
                        self.a_event2_last[idx] = event_var
                        self.get_play_status(idx, event_var)

            if True:
                # 4 zoneGroupTopology
                try:
                    if self.a_zone_ev_sub4[idx] is None or not self.a_zone_ev_sub4[idx].is_subscribed:
                        self.a_zone_ev_sub4[idx] = z_req.zoneGroupTopology.subscribe()
                    if not self.a_zone_ev_sub4[idx].events.empty():
                        event = self.a_zone_ev_sub4[idx].events.get(timeout=0.5)
                        b_is_avail4 = True
                    else:
                        b_is_avail4 = False
                except:
                    b_is_avail4 = False

                if b_is_avail4:
                    self.get_cmd_info('### E4 Z:' + str(idx) + ' Zone', 4)

                    event_var = event.variables
                    if self.b_zone_ev_sub4_prnt:
                        pprint(event_var)
                        print('\n')

                    self.get_groups()
                    self.b_evsub4_addturn = True

            if True:
                # 5 deviceProperties
                try:
                    if self.a_zone_ev_sub5[idx] is None or not self.a_zone_ev_sub5[idx].is_subscribed:
                        self.a_zone_ev_sub5[idx] = z_req.deviceProperties.subscribe()
                    if not self.a_zone_ev_sub5[idx].events.empty():
                        event = self.a_zone_ev_sub5[idx].events.get(timeout=0.5)
                        b_is_avail5 = True
                    else:
                        b_is_avail5 = False
                except:
                    b_is_avail5 = False

                if b_is_avail5:
                    self.get_cmd_info('### E5 Z:' + str(idx) + ' Prop', 4)

                    event_var = event.variables
                    if self.b_zone_ev_sub5_prnt:
                        pprint(event_var)
                        print('\n')

    def set_play_mode(self, idx_zone=0, idx_mode=0):
        """
        set required play mode
        :param idx_zone:
        :param idx_mode:
        :return:
        """
        idx_coo = self.get_zone_co_idx(idx_zone)
        z_req = self.get_zone(idx_coo)

        if self.a_play_is_radio[idx_coo] or self.a_play_is_auxin[idx_coo]:
            return
        if idx_mode == 0:
            z_req.avTransport.SetPlayMode([('InstanceID', 0), ('NewPlayMode', 'NORMAL')])
        elif idx_mode == 1:
            z_req.avTransport.SetPlayMode([('InstanceID', 0), ('NewPlayMode', 'SHUFFLE')])
        elif idx_mode == 2:
            z_req.avTransport.SetPlayMode([('InstanceID', 0), ('NewPlayMode', 'SHUFFLE_NOREPEAT')])
        elif idx_mode == 3:
            z_req.avTransport.SetPlayMode([('InstanceID', 0), ('NewPlayMode', 'REPEAT_ALL')])

    def get_sleep_timer(self, idx_zone=-1):
        """
        get current sleep timer status
        :param idx_zone:
        :return:
        """
        num_zones = len(self.a_zone_soco)
        # init
        if idx_zone == -2:

            for idxZ in range(num_zones):
                idx_coo = self.get_zone_co_idx(idxZ)
                z_req = self.get_zone(idx_coo)
                d_cur_sleep_time = z_req.get_sleep_timer()
                if d_cur_sleep_time is None:
                    self.a_sleep_time_val[idx_coo] = d_cur_sleep_time
                    self.ev_sleep_time_val(idx_coo, d_cur_sleep_time)
                else:
                    self.a_sleep_time_val[idx_coo] = d_cur_sleep_time
                    str_time = self.timestamp4sec(d_cur_sleep_time)
                    self.ev_sleep_time_val(idx_coo, str_time)

        # check
        if idx_zone == -1:

            for idxZ in range(num_zones):
                idx_coo = self.get_zone_co_idx(idxZ)
                if self.a_sleep_time_val[idx_coo] is not None:

                    z_req = self.get_zone(idx_coo)
                    d_cur_sleep_time = z_req.get_sleep_timer()
                    if d_cur_sleep_time is None:
                        self.a_sleep_time_val[idx_coo] = d_cur_sleep_time
                        self.ev_sleep_time_val(idx_coo, d_cur_sleep_time)
                    else:
                        self.a_sleep_time_val[idx_coo] = d_cur_sleep_time
                        str_time = self.timestamp4sec(d_cur_sleep_time)
                        self.ev_sleep_time_val(idx_coo, str_time)
        else:

            idx_coo = self.get_zone_co_idx(idx_zone)
            z_req = self.get_zone(idx_coo)
            d_cur_sleep_time = z_req.get_sleep_timer()
            if d_cur_sleep_time is None:
                self.a_sleep_time_val[idx_coo] = d_cur_sleep_time
                self.ev_sleep_time_val(idx_coo, d_cur_sleep_time)
            else:
                self.a_sleep_time_val[idx_coo] = d_cur_sleep_time
            return d_cur_sleep_time

    def set_sleep_timer(self, idx_zone=0, d_time=60):
        """
        set sleep timer value
        :param idx_zone:
        :param d_time:
        """
        idx_coo = self.get_zone_co_idx(idx_zone)
        z_req = self.get_zone(idx_coo)
        d_cur_sleep_time = z_req.get_sleep_timer()

        if d_cur_sleep_time is None:
            z_req.set_sleep_timer(d_time * 60)
        else:
            z_req.set_sleep_timer(None)

    def timestamp4sec(self, d_time_sec):
        """
        make a time stamp with format hh:mm:ss
        :param d_time_sec:
        :return:
        """
        m, s = divmod(d_time_sec, 60)
        h, m = divmod(m, 60)

        return "%d:%02d:%02d" % (h, m, s)

    def str_split(self, str_base, str_sp1, str_sp2):
        """
        get string between two other strings
        :param str_base:
        :param str_sp1:
        :param str_sp2:
        :return:
        """
        str_base1 = str_base.split(str_sp1)
        str_base2 = str_base1[1].split(str_sp2)
        return str_base2[0]


class EventCall(list):

    def __call__(self, *args, **kwargs):
        for f in self:
            f(*args, **kwargs)

    def __repr__(self):
        return "Event(%s)" % list.__repr__(self)

    def num_ev(self):
        return len(self)

    def is_linked(self):
        if len(self) > 0:
            return True
        else:
            return False
