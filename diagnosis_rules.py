# -*- coding: utf-8 -*-
# @Time    : 2023/4/10
# @Author  : Liuxiaowei

# 传入文件格式：
"""
{
"group_name":"烧成"
"equ_name":"篦冷机F1"
"token":
"equ_params":{}
"points_data":[{
               "dtime":"2019-09-01 01:50:00.000",
               "vel_data":["value":[]],
               "impul_data":["value":[],],
               "acc_data":["value":[],],
               "dis_data":["value":[],],
               "rpm":["转速":1800,"转频":30],
               "point_id":"01"
               },
               {"point_id":"02",},
               {"point_id":"03",},
               ]
"points_info":[{"point_id":"01",
                "point_params":{}
                'point_name':'被驱动侧水平',
                'sn_info':{'hz':2560
                           'cl':4096},
                {},
                {},       
                ]
"DTime":"2023-04-21 23:50:00.000",
"sendType":1
"equ_sn":"051402M02"
"con_status":
"equ_type":"其它"}

###########################################################
mongodb中趋势存储：
trend_data
{'2f0':[1,2,...,100],
 '1倍频':[1,2,...,100],
 '2倍频':[]
 ...
}
#################################################
报警信息：alarm_message
{"电机":["电机自由侧X", "电机负荷侧"]
 "风机":["风机自由侧", "风机负荷侧"]
}



"""""
from feature_function import *
# 篦冷风机
conclusion_return = pd.read_excel(r'F:\Aaxiaowei\算法组\雪工资料\主泵机理模型梳理20220715(1).xlsx')

class Bilengji_Dianji:

    def __int__(self, json1, alarm_message, trend_data):
        self.point_data = json1["point_data"]
        self.point_info = json1['points_info']
        self.alarm_channel1 = alarm_message["电机"][0]
        self.alarm_channel2 = alarm_message["电机"][1]

        self.data1 = self.point_data[self.alarm_channel1]['vel_data']['value']
        self.frequency_1 = self.point_info[self.alarm_channel1]['sn_info']['hz']
        self.data2 = self.point_data[self.alarm_channel2]['vel_data']['value']
        self.frequency_2 = self.point_info[self.alarm_channel2]['sn_info']['hz']
        self.data1_trend = trend_data[alarm_message["电机"][0]]
        self.data2_trend = trend_data[alarm_message["电机"][0]]

    def dingziyichang(self):
        if ((get_HS(self.data1, 100, 1)/get_HS((self.data1, 30, 1)))>= 1 or Numaverage(self.data1_trend) >= 0.8) or \
                (get_HS(self.data2, 100, 1)/get_HS((self.data1, 30, 1)) >= 1 or Numaverage(self.data2_trend) >= 0.8):

            return dict(故障模式=str(conclusion_return.iloc[0]["故障模式"]),
                        机理现象=str(conclusion_return.iloc[0]["机理现象"]),
                        机理原因=str(conclusion_return.iloc[0]["机理原因"]))

    def qixipianxin(self):
        if (get_HS(self.data1, 100, 1)/get_HS((self.data1, 30, 1)) >= 1 or Numaverage(self.data1_trend)) \
                    (get_HS(self.data1, 100, 1)/get_HS((self.data1, 30, 1)) >= 1 or Numaverage(self.data2_trend)):

            return dict(故障模式=str(conclusion_return.iloc[1]["故障模式"]),
                        机理现象=str(conclusion_return.iloc[1]["机理现象"]),
                        机理原因=str(conclusion_return.iloc[1]["机理原因"]))









