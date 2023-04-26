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
               "vel_data":["value":[]],    # 振动值
               "impul_data":["value":[],],  # 冲击值
               "acc_data":["value":[],],    # 加速度值
               "dis_data":["value":[],],    # 位移值
               "rpm":["转速":1800,"转频":30],
               "bpf":["value":[]] # 叶片通过频率
               "dbpf":["value":[]] # ???
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
 'HRS': []
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
        self.alarm_channel1 = alarm_message["电机"][0] # 水平1
        self.alarm_channel2 = alarm_message["电机"][1] # 竖直1
        self.alarm_channel3 = alarm_message["电机"][2]  # 水平1
        self.alarm_channel4 = alarm_message["电机"][3]  # 竖直2

        self.data1 = self.point_data[self.alarm_channel1]['vel_data']['value']  #
        self.frequency_1 = self.point_info[self.alarm_channel1]['sn_info']['hz']
        self.data2 = self.point_data[self.alarm_channel2]['vel_data']['value']
        self.frequency_2 = self.point_info[self.alarm_channel2]['sn_info']['hz']
        self.data3 = self.point_data[self.alarm_channel3]['vel_data']['value']  #
        self.frequency_3 = self.point_info[self.alarm_channel3]['sn_info']['hz']
        self.data4 = self.point_data[self.alarm_channel4]['vel_data']['value']
        self.frequency_4 = self.point_info[self.alarm_channel4]['sn_info']['hz']

        self.data1_trend = trend_data[alarm_message["电机"][0]]
        self.data2_trend = trend_data[alarm_message["电机"][1]]
        self.data3_trend = trend_data[alarm_message["电机"][2]]
        self.data4_trend = trend_data[alarm_message["电机"][3]]

        self.twosf0 = json1["twosf0"] # 旋转磁场超越转子速度[f0/P- (1-s)f0/P] ×2P= 2sf0。
        self.fs = json1["fs"] # 采样频率
        self.rpm = json1["rpm"]["转速"] #
        self.bpf = json1["bpf"]["value"] # 叶片通过频率
        self.dbpf = json1["dbpf"]["value"] # ????

    def dingziyichang(self):  # 1,电机定子异常故障
        if ((get_HS(self.data1, self.fs, 100, 1)/get_HS(self.data1, self.fs, 50, 1)) >= 1 or Numaverage(self.data1_trend) >= 0.8) or \
                (get_HS(self.data2, self.fs, 100, 1)/get_HS(self.data2, self.fs, 50, 1) >= 1 or Numaverage(self.data2_trend) >= 0.8) or \
                (get_HS(self.data3, self.fs, 100, 1)/get_HS(self.data3, self.fs, 50, 1) >= 1 or Numaverage(self.data3_trend) >= 0.8) or \
                (get_HS(self.data4, self.fs, 100, 1)/get_HS(self.data4, self.fs, 50, 1) >= 1 or Numaverage(self.data4_trend) >= 0.8) :

            return dict(故障模式=str(conclusion_return.iloc[0]["故障模式"]),
                        机理现象=str(conclusion_return.iloc[0]["机理现象"]),
                        机理原因=str(conclusion_return.iloc[0]["机理原因"]))

    def qixipianxin(self): # 2, 电机气隙动态偏心
        if (get_HCR(self.data1, self.fs, self.twosf0, 100, 5) >= 0.5 or get_HS(self.data1, self.fs, self.twosf0, 5) / get_HS(self.data1, self.fs, 50, 1) >= 1) or \
                (get_HCR(self.data2, self.fs, self.twosf0, 100, 5) >= 0.5 or get_HS(self.data2, self.fs, self.twosf0,
                                                                                    5) / get_HS(self.data2, self.fs, 50, 1) >= 1) or \
                (get_HCR(self.data3, self.fs, self.twosf0, 100, 5) >= 0.5 or get_HS(self.data3, self.fs, self.twosf0,
                                                                                5) / get_HS(self.data3, self.fs, 50, 1) >= 1) or \
                (get_HCR(self.data4, self.fs, self.twosf0, 100, 5) >= 0.5 or get_HS(self.data4, self.fs, self.twosf0,
                                                                                    5) / get_HS(self.data4, self.fs, 50, 1) >= 1):

            return dict(故障模式=str(conclusion_return.iloc[1]["故障模式"]),
                        机理现象=str(conclusion_return.iloc[1]["机理现象"]),
                        机理原因=str(conclusion_return.iloc[1]["机理原因"]))

    def zhuanzitongtiaoduanlie(self): # 3 电机转子铜条断裂
        if (get_HCR(self.data1, self.fs, self.twosf0, 100, 5) >= 0.5 or Numaverage(amplitude(self.data1, self.fs, 50)) >= 0.8) or \
                (get_HCR(self.data2, self.fs, self.twosf0, 100, 5) >= 0.5 or Numaverage(amplitude(self.data2, self.fs, 50)) >= 0.8) or \
                (get_HCR(self.data3, self.fs, self.twosf0, 100, 5) >= 0.5 or Numaverage(amplitude(self.data3, self.fs, 50)) >= 0.8) or \
                (get_HCR(self.data4, self.fs, self.twosf0, 100, 5) >= 0.5 or Numaverage(amplitude(self.data4, self.fs, 50)) >= 0.8) :
            return dict(故障模式=str(conclusion_return.iloc[2]["故障模式"]),
                        机理现象=str(conclusion_return.iloc[2]["机理现象"]),
                        机理原因=str(conclusion_return.iloc[2]["机理原因"]))

    def zhuanzitongtiaosongdonghuotuoluo(self): # 4 电机转子铜条松动或脱落
        if (get_HCR(self.data1, self.fs, self.twosf0, 50, 5) >= 0.5 or Numaverage(amplitude(self.data1, self.fs, 50)) >= 0.8) or \
                (get_HCR(self.data2, self.fs, self.twosf0, 50, 5) >= 0.5 or Numaverage(amplitude(self.data2, self.fs, 50)) >= 0.8) or \
                (get_HCR(self.data3, self.fs, self.twosf0, 50, 5) >= 0.5 or Numaverage(amplitude(self.data3, self.fs, 50)) >= 0.8) or \
                (get_HCR(self.data4, self.fs, self.twosf0, 50, 5) >= 0.5 or Numaverage(amplitude(self.data4, self.fs, 50)) >= 0.8):
            return dict(故障模式=str(conclusion_return.iloc[3]["故障模式"]),
                        机理现象=str(conclusion_return.iloc[3]["机理现象"]),
                        机理原因=str(conclusion_return.iloc[3]["机理原因"]))


    def zhuanzibupingheng(self): # 5 转子不平衡
        if (get_VIB(self.data1, self.fs, self.rpm, "xampl")[0] / get_VIB(self.data1, self.fs, self.rpm, "acc_rms") >= 0.4 or Numaverage(self.data1_trend["1倍频"]) >= 0.8) or \
                (get_VIB(self.data2, self.fs, self.rpm, "xampl")[0] / get_VIB(self.data2, self.fs, self.rpm, "acc_rms") >= 0.4 or Numaverage(self.data2_trend["1倍频"]) >= 0.8) or \
                (get_VIB(self.data3, self.fs, self.rpm, "xampl")[0] / get_VIB(self.data3, self.fs, self.rpm, "acc_rms") >= 0.4 or Numaverage(self.data3_trend["1倍频"]) >= 0.8) or \
                (get_VIB(self.data4, self.fs, self.rpm, "xampl")[0] / get_VIB(self.data4, self.fs, self.rpm, "acc_rms") >= 0.4 or Numaverage(self.data4_trend["1倍频"]) >= 0.8):
            return dict(故障模式=str(conclusion_return.iloc[4]["故障模式"]),
                        机理现象=str(conclusion_return.iloc[4]["机理现象"]),
                        机理原因=str(conclusion_return.iloc[4]["机理原因"]))

    def zhouwaduizhongbuliang(self): # 7 轴瓦对中不良
        if (get_VIB(self.data1, self.fs, self.rpm, "xampl")[1] / get_VIB(self.data1, self.fs, self.rpm, "xampl")[0] >= 1.0 or Numaverage(self.data1_trend["2倍频"]) >= 0.8) or \
                (get_VIB(self.data2, self.fs, self.rpm, "xampl")[1] / get_VIB(self.data2, self.fs, self.rpm, "xampl")[0] >= 1.0 or Numaverage(self.data2_trend["2倍频"]) >= 0.8) or \
                (get_VIB(self.data3, self.fs, self.rpm, "xampl")[1] / get_VIB(self.data3, self.fs, self.rpm, "xampl")[0] >= 1.0 or Numaverage(self.data3_trend["2倍频"]) >= 0.8) or \
                (get_VIB(self.data4, self.fs, self.rpm, "xampl")[1] / get_VIB(self.data4, self.fs, self.rpm, "xampl")[0] >= 1.0 or Numaverage(self.data4_trend["2倍频"]) >= 0.8):
            return dict(故障模式=str(conclusion_return.iloc[6]["故障模式"]),
                        机理现象=str(conclusion_return.iloc[6]["机理现象"]),
                        机理原因=str(conclusion_return.iloc[6]["机理原因"]))

    def zhuanzhourewanqu(self): # 8 转轴（热）弯曲  ###这里有轴向位置。暂时忽略
        if (get_VIB(self.data1, self.fs, self.rpm, "xampl")[1] / get_VIB(self.data1, self.fs, self.rpm, "xampl")[0] >= 1.0 or Numaverage(self.data1_trend["2倍频"]) >= 0.8) or \
                (get_VIB(self.data2, self.fs, self.rpm, "xampl")[1] / get_VIB(self.data2, self.fs, self.rpm, "xampl")[0] >= 1.0 or Numaverage(self.data2_trend["2倍频"]) >= 0.8) or \
                (get_VIB(self.data3, self.fs, self.rpm, "xampl")[1] / get_VIB(self.data3, self.fs, self.rpm, "xampl")[0] >= 1.0 or Numaverage(self.data3_trend["2倍频"]) >= 0.8) or \
                (get_VIB(self.data4, self.fs, self.rpm, "xampl")[1] / get_VIB(self.data4, self.fs, self.rpm, "xampl")[0] >= 1.0 or Numaverage(self.data4_trend["2倍频"]) >= 0.8):
            return dict(故障模式=str(conclusion_return.iloc[6]["故障模式"]),
                        机理现象=str(conclusion_return.iloc[6]["机理现象"]),
                        机理原因=str(conclusion_return.iloc[6]["机理原因"]))
    def xuanzhuanshisu(self): # 11 旋转失速
        if (get_HRS(self.data1, self.fs, frequency_low=9, frequency_high=999) / get_VIB(self.data1, self.fs, self.rpm, "acc_rms") >= 0.5 and Numaverage(self.data1_trend["HRS"]) >= 0.8 and get_VIB(self.data1, self.fs, self.rpm, "rms") >= 4.5) or \
                (get_HRS(self.data2, self.fs, frequency_low=9, frequency_high=999) / get_VIB(self.data2, self.fs, self.rpm, "acc_rms") >= 0.5 and Numaverage(self.data2_trend["HRS"]) >= 0.8 and get_VIB(self.data2, self.fs, self.rpm, "rms") >= 4.5) or \
                (get_HRS(self.data3, self.fs, frequency_low=9, frequency_high=999) / get_VIB(self.data3, self.fs, self.rpm, "acc_rms") >= 0.5 and Numaverage(self.data3_trend["HRS"]) >= 0.8 and get_VIB(self.data3, self.fs, self.rpm, "rms") >= 4.5) or \
                (get_HRS(self.data4, self.fs, frequency_low=9, frequency_high=999) / get_VIB(self.data4, self.fs, self.rpm, "acc_rms") >= 0.5 and Numaverage(self.data4_trend["HRS"]) >= 0.8 and get_VIB(self.data4, self.fs, self.rpm, "rms") >= 4.5):

            return dict(故障模式=str(conclusion_return.iloc[9]["故障模式"]),
                            机理现象=str(conclusion_return.iloc[9]["机理现象"]),
                            机理原因=str(conclusion_return.iloc[9]["机理原因"]))

    def qishihuodongjingganshe(self): # 汽蚀（或动静干涉）
        if (amplitude(self.data1, self.fs, self.bpf) / get_VIB(self.data1, self.fs, self.rpm, "xampl")[0] >= 1.0 or Numaverage(self.data1_trend["bpf"]) >= 0.8 or amplitude(self.data1, self.fs, self.dbpf) / get_VIB(self.data1, self.fs, self.rpm, "xampl")[0] >= 1.0 or \
                Numaverage(self.data1_trend["bpf"]) >= 0.8) or \
                (amplitude(self.data2, self.fs, self.bpf) / get_VIB(self.data2, self.fs, self.rpm, "xampl")[0] >= 1.0 or Numaverage(self.data2_trend["bpf"]) >= 0.8 or amplitude(self.data2, self.fs,self.dbpf) / get_VIB(self.data2, self.fs, self.rpm, "xampl")[0] >= 1.0 or \
                 Numaverage(self.data1_trend["bpf"]) >= 0.8):

            return dict(故障模式=str(conclusion_return.iloc[10]["故障模式"]),
                        机理现象=str(conclusion_return.iloc[10]["机理现象"]),
                        机理原因=str(conclusion_return.iloc[10]["机理原因"]))















