

# -*- coding: utf-8 -*-
# @Time : 2019/11/26 11:22
# @Author : sxw
import struct
import json
import warnings


def read_dat(path):
    """
    :param path:读取dat文件路径
    :return: {通道ID1:
                    {'sampling_frequency': 采样频率, 'sampling_time': 采样时间,
                    'channel_type': 通道类型, 'signal_data': 采集的原始数据list
                    'rotating_speed': 每秒转速list
                    },
              通道ID2:
                    {.....}
            }
    """
    data_dict, channel_dict = {}, {}
    with open(path, 'rb') as f:
        # channelSize(int)
        struct.unpack("i", f.read(4))[0]

        # count(int)
        struct.unpack("i", f.read(4))[0]
        # equipNo(char)
        f.read(12).decode()
        # time(char)数组
        f.read(10).decode()
        # json_size(int)
        json_size = struct.unpack("i", f.read(4))[0]
        # json串
        json_string = f.read(json_size).decode()
        json_string_dict = eval(json_string[:-2].replace('false', "False")
                                .replace('true', "True").replace('null', "None"))

        # json.dump(json_string_dict, open('D:/jsonstamp.json', 'w+'))   # 保存json串
        json_string_dict_groups_list = json_string_dict['groups']
        json_string_dict_channelsettings_list = json_string_dict['ChannelSettings']

        # print(json_string_dict["channelRMSPkPk2pk"])
        # 通道设置字典 {通道ID1:通道的单位, }
        channelsettings_dict = {}
        for channelsetting in json_string_dict_channelsettings_list:
            channel_id = channelsetting["channelId"]
            sensor_engineering_unit = channelsetting["sensorEngineeringUnit"]
            channelsettings_dict[channel_id] = sensor_engineering_unit
        # 转速字典 {通道ID1:每秒钟的转速list, }
        # print(channelsettings_dict)

        # 解析测点名称
        point_dict = {}
        for channelsetting in json_string_dict_channelsettings_list:
            channel_id = channelsetting["channelId"]
            channelName = channelsetting["channelName"]
            point_dict[channel_id] = channelName

        rotating_speed_dict = {}
        # 通道类型字典 {通道ID1:通道类型1, 通道ID2:通道类型1}

        for json_string_dict_groups in json_string_dict_groups_list:
            group_channel_type = json_string_dict_groups['ChannelType']
            group_channel_name = json_string_dict_groups['name']

            # print(group_channel_name)
            channel_dict[group_channel_name] = group_channel_type
            if group_channel_type == 'TACHOMETER':
                # tachometer_channelname_list.append(group_channel_name)

                assert json_string_dict_groups['channels'][4]['name'] == "SpeedProfileSpeed"
                json_string_dict_groups['channels'][4].get('data', None)
                # rotating_speed_dict[group_channel_name] = json_string_dict_groups['channels'][4].get('data', None)
                rotating_speed_dict[group_channel_name] = None
        # # 循环读出原始数据内容
        reconut_flag = 1
        while True:
            # count
            second_binary = f.read(4)
            if len(second_binary) == 4:
                second_time = struct.unpack("i", second_binary)[0]

                # 通道类型
                current_channel = f.read(15).decode()
                # wave_size
                wave_size = struct.unpack("i", f.read(4))[0]
                # print(second_time, current_channel, wave_size)
                # 判断键相通道是否重新计数写入时间戳
                if reconut_flag and \
                        data_dict.get(current_channel, {'sampling_time': 0}).get("sampling_time") == (second_time - 1):
                    # buf2
                    try:
                        data_dict[current_channel]["sampling_frequency"] = wave_size
                        data_dict[current_channel]["sampling_time"] = second_time
                        data_dict[current_channel]['channel_type'] = channel_dict[current_channel]
                        # data_dict[current_channel]['point_name'] = group_channel_name
                        data_dict[current_channel]['trigge r_time'] = json_string_dict['triggerEvent']['triggerTime']
                    except KeyError:
                        data_dict[current_channel] = {
                            "sampling_frequency": wave_size,
                            'sampling_time': second_time,
                            'channel_type': channel_dict[current_channel]
                        }
                    counts = 1
                    while counts <= wave_size:
                        data_point, = struct.unpack("f", f.read(4))

                        try:
                            data_dict[current_channel]['signal_data'].append(data_point)
                        except KeyError:
                            data_dict[current_channel]['signal_data'] = [data_point]
                        counts += 1
                else:
                    reconut_flag = 0
                    counts = 1
                    per_second_timestamp = []
                    while counts <= wave_size:
                        time_stamp_point, = struct.unpack("f", f.read(4))
                        per_second_timestamp.append(time_stamp_point)
                        counts += 1
                    try:
                        data_dict[current_channel]['time_stamp'].append(per_second_timestamp)
                    except KeyError:
                        pass
                        #data_dict[current_channel]['time_stamp'] = [per_second_timestamp]
            else:
                break
        for channel_id in data_dict.keys():
            data_dict[channel_id]['channel_type'] = channel_dict[channel_id]
            data_dict[channel_id]['sensor_engineering_unit'] = channelsettings_dict[channel_id]
            data_dict[channel_id]['channel_name'] = point_dict[channel_id]

            # 对键相信号字典加入每秒转速值

            if channel_id in rotating_speed_dict.keys():
                if rotating_speed_dict[channel_id] is None:
                    rotating_speed_dict[channel_id] = []
                    # print(data_dict[channel_id])
                    if 'time_stamp' in data_dict[channel_id].keys():
                        for second_timestap in data_dict[channel_id]['time_stamp']:
                            if len(second_timestap) > 1:
                                second_rotating_speed_list = \
                                    [pow(second_timestap[i + 1] - second_timestap[i], -1) * 60
                                     for i in range(len(second_timestap) - 1)]
                                second_rotating_speed = sum(second_rotating_speed_list) / len(
                                    second_rotating_speed_list)
                            else:
                                second_rotating_speed = 0
                                # raise ValueError('low rotating speed')
                                warnings.warn("low rotating speed")
                            rotating_speed_dict[channel_id].append(second_rotating_speed)
                data_dict[channel_id]['rotating_speed'] = rotating_speed_dict[channel_id]
        return data_dict  ## 返回时间戳和通道字典


# if __name__ == '__main__':
#     import matplotlib.pyplot as plt
#
#     # signal_dict = read_dat('D:\\数据\\转子实验台\\2019-12-4-8K\\LEVEL-50294D208524011-50294D208524-1576116135.dat').get('50294D208524014')
#     signal_dict = read_dat(
#         r'\\192.168.1.203\homes\王之敏\新建文件夹 (3)\诊断报告数据\50294D208409\2021-03-22_16-13-19.dat')  # .get('50294D208505012')
#
#     # signal_dict = read_dat('D:\\数据\宝钢数据\\宝钢现场\\TIME_INTERVAL-50294D208505011-50294D208505-1574051418.dat').get('50294D208505011')
#     # json.dump(signal_dict, open('jsonstamp.json', 'w+'))
