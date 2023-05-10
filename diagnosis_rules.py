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
{'X_2f0':[1,2,...,100],
 '1倍频':[1,2,...,100],
 '2倍频':[]
 'HRS': []
 'HS_1X': []  HS(水平1，1倍频，5)
 'HDS_1X': [] HDS(水平1，1倍频，5）
 'SW_X': [] 水平-涡动频率
 'BTemp': [[1,2,...,100],[1,2,...,100],[1,2,...,100],[1,2,...,100]] 轴承水温
 "bpf" : [1,2,...,100] BPF对应幅值，振动频率表现为叶片通过频率BPF
 "dbpf" : [1,2,...,100] DBPF对应幅值
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
        self.alarm_channel1 = alarm_message["电机"][0] # 电机上壳横向振动X方向
        self.alarm_channel2 = alarm_message["电机"][1] # 电机上壳横向振动Y方向
        self.alarm_channel3 = alarm_message["电机"][2]  # 电机下壳横向振动X方向
        self.alarm_channel4 = alarm_message["电机"][3]  # 电机下壳横向振动Y方向
        self.alarm_channel5 = alarm_message["电机"][4]  # 电机下壳横向振动Z方向


        self.data1 = self.point_data[self.alarm_channel1]['vel_data']['value']  #
        self.frequency_1 = self.point_info[self.alarm_channel1]['sn_info']['hz']
        self.data2 = self.point_data[self.alarm_channel2]['vel_data']['value']
        self.frequency_2 = self.point_info[self.alarm_channel2]['sn_info']['hz']
        self.data3 = self.point_data[self.alarm_channel3]['vel_data']['value']  #
        self.frequency_3 = self.point_info[self.alarm_channel3]['sn_info']['hz']
        self.data4 = self.point_data[self.alarm_channel4]['vel_data']['value']
        self.frequency_4 = self.point_info[self.alarm_channel4]['sn_info']['hz']
        self.data5 = self.point_data[self.alarm_channel5]['vel_data']['value']
        self.frequency_5 = self.point_info[self.alarm_channel5]['sn_info']['hz']

        self.data1_trend = trend_data[alarm_message["电机"][0]]
        self.data2_trend = trend_data[alarm_message["电机"][1]]
        self.data3_trend = trend_data[alarm_message["电机"][2]]
        self.data4_trend = trend_data[alarm_message["电机"][3]]
        self.data5_trend = trend_data[alarm_message["电机"][4]] # 轴向趋势

        self.twosf0 = json1["twosf0"] # 旋转磁场超越转子速度[f0/P- (1-s)f0/P] ×2P= 2sf0。
        self.fs = json1["fs"] # 采样频率
        self.rpm = json1["rpm"]["转速"] #
        self.X_1 = self.rpm / 60 # 一倍频
        self.bpf = json1["bpf"]["value"] # 叶片通过频率
        self.dbpf = json1["rbpf"]["value"] # 转子条通过频率RBPF，
        self.sw_freq = json1["swirl_frequency"] # 涡动频率


    def dingziyichang(self):  # 1,电机定子异常故障
        sign_1, sign_2, sign_3, sign_4 = 0, 0, 0, 0
        if self.data1:
            if ((get_HS(self.data1, self.fs, 100, 1)/get_HS(self.data1, self.fs, self.X_1, 1)) >= 1 or Numaverage(self.data1_trend['X_2f0']) >= 0.8):
                sign_1 = 1
            else:
                sign_1 = 0

        if self.data2:
            if ((get_HS(self.data2, self.fs, 100, 1)/get_HS(self.data2, self.fs, self.X_1, 1)) >= 1 or Numaverage(self.data2_trend['X_2f0']) >= 0.8):
                sign_2 = 1
            else:
                sign_2 = 0

        if self.data3:
            if ((get_HS(self.data3, self.fs, 100, 1)/get_HS(self.data3, self.fs, self.X_1, 1)) >= 1 or Numaverage(self.data3_trend['X_2f0']) >= 0.8):
                sign_3 = 1
            else:
                sign_3 = 0

        if self.data4:
            if ((get_HS(self.data4, self.fs, 100, 1)/get_HS(self.data4, self.fs, self.X_1, 1)) >= 1 or Numaverage(self.data4_trend['X_2f0']) >= 0.8):
                sign_4 = 1
            else:
                sign_4 = 0

        sign = sign_1 + sign_2 + sign_3 + sign_4

        if sign:
            return dict(故障模式=str(conclusion_return.iloc[0]["故障模式"]),
                        机理现象=str(conclusion_return.iloc[0]["机理现象"]),
                        机理原因=str(conclusion_return.iloc[0]["机理原因"]))
        else:
            return "电机定子正常"

    def qixipianxin(self):  # 2, 电机气隙动态偏心
        sign_1, sign_2, sign_3, sign_4 = 0, 0, 0, 0
        if self.data1:
            if (get_HCR(self.data1, self.fs, self.twosf0, 100, 5) >= 0.5 or get_HS(self.data1, self.fs, self.twosf0, 5) / get_HS(self.data1, self.fs, self.X_1, 1) >= 1):
                sign_1 = 1
            else:
                sign_1 = 0

        if self.data2:
            if (get_HCR(self.data2, self.fs, self.twosf0, 100, 5) >= 0.5 or get_HS(self.data2, self.fs, self.twosf0, 5) / get_HS(self.data2, self.fs, self.X_1, 1) >= 1):
                sign_2 = 1
            else:
                sign_2 = 0

        if self.data3:
            if (get_HCR(self.data3, self.fs, self.twosf0, 100, 5) >= 0.5 or get_HS(self.data3, self.fs, self.twosf0, 5) / get_HS(self.data3, self.fs, self.X_1, 1) >= 1):
                sign_3 = 1
            else:
                sign_3 = 0

        if self.data4:
            if (get_HCR(self.data4, self.fs, self.twosf0, 100, 5) >= 0.5 or get_HS(self.data4, self.fs, self.twosf0, 5) / get_HS(self.data4, self.fs, self.X_1, 1) >= 1):
                sign_4 = 1
            else:
                sign_4 = 0

        sign = sign_1 + sign_2 + sign_3 + sign_4
        if sign:
            return dict(故障模式=str(conclusion_return.iloc[1]["故障模式"]),
                        机理现象=str(conclusion_return.iloc[1]["机理现象"]),
                        机理原因=str(conclusion_return.iloc[1]["机理原因"]))
        else:
            return "电机气隙动态偏心正常"

    def zhuanzitongtiaoduanlie(self):  # 3 电机转子铜条断裂
        sign_1, sign_2, sign_3, sign_4 = 0, 0, 0, 0
        if self.data1:
            if (get_HCR(self.data1, self.fs, self.twosf0, 100, 5) >= 0.5 or Numaverage(self.data1_trend["1倍频"]) >= 0.8):
                sign_1 = 1
            else:
                sign_1 = 0

        if self.data2:
            if (get_HCR(self.data2, self.fs, self.twosf0, 100, 5) >= 0.5 or Numaverage(self.data2_trend["1倍频"]) >= 0.8):
                sign_2 = 1
            else:
                sign_2 = 0

        if self.data3:
            if (get_HCR(self.data2, self.fs, self.twosf0, 100, 5) >= 0.5 or Numaverage(self.data2_trend["1倍频"]) >= 0.8):
                sign_3 = 1
            else:
                sign_3 = 0

        if self.data4:
            if (get_HCR(self.data2, self.fs, self.twosf0, 100, 5) >= 0.5 or Numaverage(self.data2_trend["1倍频"]) >= 0.8):
                sign_4 = 1
            else:
                sign_4 = 0
        sign = sign_1 + sign_2 + sign_3 + sign_4
        if sign:
            return dict(故障模式=str(conclusion_return.iloc[2]["故障模式"]),
                        机理现象=str(conclusion_return.iloc[2]["机理现象"]),
                        机理原因=str(conclusion_return.iloc[2]["机理原因"]))
        else:
            return "电机转子铜条没有断裂"

    def zhuanzitongtiaosongdonghuotuoluo(self):  # 4 电机转子铜条松动或脱落
        sign_1, sign_2, sign_3, sign_4 = 0, 0, 0, 0
        if self.data1:
            if (get_HCR(self.data1, self.fs, self.twosf0, self.dbpf, 5) >= 0.5 or Numaverage(self.data1_trend["X_dbpf"]) >= 0.8):
                sign_1 = 1
            else:
                sign_1 = 0

        if self.data2:
            if (get_HCR(self.data2, self.fs, self.twosf0, self.dbpf, 5) >= 0.5 or Numaverage(self.data2_trend["X_dbpf"]) >= 0.8):
                sign_2 = 1
            else:
                sign_2 = 0

        if self.data3:
            if (get_HCR(self.data3, self.fs, self.twosf0, self.dbpf, 5) >= 0.5 or Numaverage(self.data3_trend["X_dbpf"]) >= 0.8):
                sign_3 = 1
            else:
                sign_3 = 0

        if self.data4:
            if (get_HCR(self.data4, self.fs, self.twosf0, self.dbpf, 5) >= 0.5 or Numaverage(self.data4_trend["X_dbpf"]) >= 0.8):
                sign_4 = 1
            else:
                sign_4 = 0
        sign = sign_1 + sign_2 + sign_3 + sign_4
        if sign:
            return dict(故障模式=str(conclusion_return.iloc[3]["故障模式"]),
                        机理现象=str(conclusion_return.iloc[3]["机理现象"]),
                        机理原因=str(conclusion_return.iloc[3]["机理原因"]))
        else:
            return "电机转子铜条没有松动或脱落"

    def zhuanzibupingheng(self):  # 5 转子不平衡
        sign_1, sign_2, sign_3, sign_4 = 0, 0, 0, 0
        if self.data1:
            if (get_VIB(self.data1, self.fs, self.rpm, "xampl")[0] / get_VIB(self.data1, self.fs, self.rpm, "acc_rms") >= 0.4 or Numaverage(self.data1_trend["1倍频"]) >= 0.8):
                sign_1 = 1
            else:
                sign_1 = 0

        if self.data2:
            if (get_VIB(self.data2, self.fs, self.rpm, "xampl")[0] / get_VIB(self.data2, self.fs, self.rpm, "acc_rms") >= 0.4 or Numaverage(self.data2_trend["1倍频"]) >= 0.8):
                sign_2 = 1
            else:
                sign_2 = 0

        if self.data3:
            if (get_VIB(self.data3, self.fs, self.rpm, "xampl")[0] / get_VIB(self.data3, self.fs, self.rpm, "acc_rms") >= 0.4 or Numaverage(self.data3_trend["1倍频"]) >= 0.8):
                sign_3 = 1
            else:
                sign_3 = 0

        if self.data4:
            if (get_VIB(self.data4, self.fs, self.rpm, "xampl")[0] / get_VIB(self.data4, self.fs, self.rpm, "acc_rms") >= 0.4 or Numaverage(self.data4_trend["1倍频"]) >= 0.8):
                sign_4 = 1
            else:
                sign_4 = 0
        sign = sign_1 + sign_2 + sign_3 + sign_4
        if sign:
            return dict(故障模式=str(conclusion_return.iloc[4]["故障模式"]),
                        机理现象=str(conclusion_return.iloc[4]["机理现象"]),
                        机理原因=str(conclusion_return.iloc[4]["机理原因"]))
        else:
            return "电机转子平衡"

    def zhouwaduizhongbuliang(self):  # 7 轴瓦对中不良
        sign_1, sign_2, sign_3, sign_4 = 0, 0, 0, 0
        if self.data1:
            if (get_VIB(self.data1, self.fs, self.rpm, "xampl")[1] / get_VIB(self.data1, self.fs, self.rpm, "xampl")[0] >= 1.0 or Numaverage(self.data1_trend["2倍频"]) >= 0.8):
                sign_1 = 1
            else:
                sign_1 = 0

        if self.data2:
            if (get_VIB(self.data2, self.fs, self.rpm, "xampl")[1] / get_VIB(self.data2, self.fs, self.rpm, "xampl")[0] >= 1.0 or Numaverage(self.data2_trend["2倍频"]) >= 0.8):
                sign_2 = 1
            else:
                sign_2 = 0

        if self.data3:
            if (get_VIB(self.data3, self.fs, self.rpm, "xampl")[1] / get_VIB(self.data3, self.fs, self.rpm, "xampl")[0] >= 1.0 or Numaverage(self.data3_trend["2倍频"]) >= 0.8):
                sign_3 = 1
            else:
                sign_3 = 0

        if self.data4:
            if (get_VIB(self.data4, self.fs, self.rpm, "xampl")[1] / get_VIB(self.data4, self.fs, self.rpm, "xampl")[0] >= 1.0 or Numaverage(self.data4_trend["2倍频"]) >= 0.8):
                sign_4 = 1
            else:
                sign_4 = 0
        sign = sign_1 + sign_2 + sign_3 + sign_4
        if sign:
            return dict(故障模式=str(conclusion_return.iloc[6]["故障模式"]),
                        机理现象=str(conclusion_return.iloc[6]["机理现象"]),
                        机理原因=str(conclusion_return.iloc[6]["机理原因"]))
        else:
            return "轴瓦对中正常"

    def zhuanzhourewanqu(self): # 8 转轴（热）弯曲  ###这里有轴向位置

        sign_3, sign_4, sign_5 = 0, 0, 0

        if self.data3:
            if (get_VIB(self.data3, self.fs, self.rpm, "xampl")[0] / get_VIB(self.data3, self.fs, self.rpm, "acc_rms") >= 1.0 or Numaverage(self.data3_trend["1倍频"]) >= 0.8):
                sign_3 = 1
            else:
                sign_3 = 0

        if self.data4:
            if (get_VIB(self.data4, self.fs, self.rpm, "xampl")[0] / get_VIB(self.data4, self.fs, self.rpm, "acc_rms") >= 1.0 or Numaverage(self.data4_trend["1倍频"]) >= 0.8):
                sign_4 = 1
            else:
                sign_4 = 0

        if self.data5:
            if (get_VIB(self.data5, self.fs, self.rpm, "xampl")[0] / get_VIB(self.data5, self.fs, self.rpm,
                                                                             "acc_rms") >= 1.0 or Numaverage(
                    self.data5_trend["1倍频"]) >= 0.8):
                sign_5 = 1
            else:
                sign_5 = 0

        sign = sign_3 + sign_4 + sign_5

        if (sign == 3):
            return dict(故障模式=str(conclusion_return.iloc[7]["故障模式"]),
                        机理现象=str(conclusion_return.iloc[7]["机理现象"]),
                        机理原因=str(conclusion_return.iloc[7]["机理原因"]))
        else:
            return "转轴正常"

    def xuanzhuanshisu(self):  # 11 旋转失速
        sign_1, sign_2, sign_3, sign_4 = 0, 0, 0, 0
        if self.data1:
            if (get_HRS(self.data1, self.fs, frequency_low=9, frequency_high=999) / get_VIB(self.data1, self.fs, self.rpm, "acc_rms") >= 0.5 and Numaverage(self.data1_trend["HRS"]) >= 0.8 and get_VIB(self.data1, self.fs, self.rpm, "rms") >= 4.5):
                sign_1 = 1
            else:
                sign_1 = 0

        if self.data2:
            if (get_HRS(self.data2, self.fs, frequency_low=9, frequency_high=999) / get_VIB(self.data2, self.fs, self.rpm, "acc_rms") >= 0.5 and Numaverage(self.data2_trend["HRS"]) >= 0.8 and get_VIB(self.data2, self.fs, self.rpm, "rms") >= 4.5):
                sign_2 = 1
            else:
                sign_2 = 0

        if self.data3:
            if (get_HRS(self.data3, self.fs, frequency_low=9, frequency_high=999) / get_VIB(self.data3, self.fs, self.rpm, "acc_rms") >= 0.5 and Numaverage(self.data3_trend["HRS"]) >= 0.8 and get_VIB(self.data3, self.fs, self.rpm, "rms") >= 4.5):
                sign_3 = 1
            else:
                sign_3 = 0

        if self.data4:
            if (get_HRS(self.data4, self.fs, frequency_low=9, frequency_high=999) / get_VIB(self.data4, self.fs, self.rpm, "acc_rms") >= 0.5 and Numaverage(self.data4_trend["HRS"]) >= 0.8 and get_VIB(self.data4, self.fs, self.rpm, "rms") >= 4.5):
                sign_4 = 1
            else:
                sign_4 = 0
        sign = sign_1 + sign_2 + sign_3 + sign_4
        if sign:
            return dict(故障模式=str(conclusion_return.iloc[9]["故障模式"]),
                        机理现象=str(conclusion_return.iloc[9]["机理现象"]),
                        机理原因=str(conclusion_return.iloc[9]["机理原因"]))
        else:
            return "旋转速度正常"


    def qishihuodongjingganshe(self):  # 汽蚀（或动静干涉）
        sign_1, sign_2 = 0, 0
        if self.data1:
            if (amplitude(self.data1, self.fs, self.bpf) / get_VIB(self.data1, self.fs, self.rpm, "xampl")[0] >= 1.0 or Numaverage(self.data1_trend["bpf"]) >= 0.8 or amplitude(self.data1, self.fs, self.dbpf) / get_VIB(self.data1, self.fs, self.rpm, "xampl")[0] >= 1.0 or Numaverage(self.data1_trend["dbpf"]) >= 0.8):
                sign_1 = 1
            else:
                sign_1 = 0

        if self.data2:
            if (amplitude(self.data2, self.fs, self.bpf) / get_VIB(self.data2, self.fs, self.rpm, "xampl")[0] >= 1.0 or Numaverage(self.data2_trend["bpf"]) >= 0.8 or amplitude(self.data2, self.fs,self.dbpf) / get_VIB(self.data2, self.fs, self.rpm, "xampl")[0] >= 1.0 or Numaverage(self.data1_trend["dbpf"]) >= 0.8):
                sign_2 = 1
            else:
                sign_2 = 0

        sign = sign_1 + sign_2
        if sign:
            return dict(故障模式=str(conclusion_return.iloc[10]["故障模式"]),
                        机理现象=str(conclusion_return.iloc[10]["机理现象"]),
                        机理原因=str(conclusion_return.iloc[10]["机理原因"]))
        else:
            return "电机没有汽蚀（或动静干涉）"

    def dongjingbujianmoca(self):  # 9 动静部件摩擦
        sign_1, sign_2, sign_3, sign_4 = 0, 0, 0, 0
        if self.data1:
            if (Numaverage(self.data1_trend["HS_1X"]) >= 0.8) or (Numaverage(self.data1_trend["HDS_1X"]) >= 0.8):
                sign_1 = 1
            else:
                sign_1 = 0

        if self.data2:
            if (Numaverage(self.data2_trend["HS_1X"]) >= 0.8) or (Numaverage(self.data2_trend["HDS_1X"]) >= 0.8):
                sign_2 = 1
            else:
                sign_2 = 0

        if self.data3:
            if (Numaverage(self.data3_trend["HS_1X"]) >= 0.8) or (Numaverage(self.data3_trend["HDS_1X"]) >= 0.8):
                sign_3 = 1
            else:
                sign_3 = 0

        if self.data4:
            if (Numaverage(self.data4_trend["HS_1X"]) >= 0.8) or (Numaverage(self.data4_trend["HDS_1X"]) >= 0.8):
                sign_4 = 1
            else:
                sign_4 = 0
        sign = sign_1 + sign_2 + sign_3 + sign_4
        if sign:
            return dict(故障模式=str(conclusion_return.iloc[11]["故障模式"]),
                        机理现象=str(conclusion_return.iloc[11]["机理现象"]),
                        机理原因=str(conclusion_return.iloc[11]["机理原因"]))
        else:
            return "动静部件摩擦正常"


    def zhuanzibujiansongdong(self):  # 10 转子部件松动
        sign_1, sign_2, sign_3, sign_4 = 0, 0, 0, 0
        if self.data1:
            if (get_VIB(self.data1, self.fs, self.rpm, "xampl")[1] / get_VIB(self.data1, self.fs, self.rpm, "xampl")[0]) and (Numaverage(self.data1_trend["HDS_1X"]) >= 0.8):
                sign_1 = 1
            else:
                sign_1 = 0

        if self.data2:
            if (get_VIB(self.data2, self.fs, self.rpm, "xampl")[1] / get_VIB(self.data2, self.fs, self.rpm, "xampl")[0]) and (Numaverage(self.data2_trend["HDS_1X"]) >= 0.8):
                sign_2 = 1
            else:
                sign_2 = 0

        if self.data3:
            if (get_VIB(self.data3, self.fs, self.rpm, "xampl")[1] / get_VIB(self.data3, self.fs, self.rpm, "xampl")[0]) and (Numaverage(self.data3_trend["HDS_1X"]) >= 0.8):
                sign_3 = 1
            else:
                sign_3 = 0

        if self.data4:
            if (get_VIB(self.data4, self.fs, self.rpm, "xampl")[1] / get_VIB(self.data4, self.fs, self.rpm, "xampl")[0]) and (Numaverage(self.data4_trend["HDS_1X"]) >= 0.8):
                sign_4 = 1
            else:
                sign_4 = 0
        sign = sign_1 + sign_2 + sign_3 + sign_4
        if sign:
            return dict(故障模式=str(conclusion_return.iloc[12]["故障模式"]),
                        机理现象=str(conclusion_return.iloc[12]["机理现象"]),
                        机理原因=str(conclusion_return.iloc[12]["机理原因"]))
        else:
            return "转子部件没有松动"

    def zhuanzizhichengbujiansongdong(self):  # 13 转子支承部件松动
        sign_1, sign_2, sign_3, sign_4 = 0, 0, 0, 0
        if self.data1:
            if (Numaverage(self.data1_trend["HS_1X"]) >= 0.8) and (Numaverage(self.data1_trend["HDS_1X"]) >= 0.8) and get_VIB(self.data1, self.fs, self.rpm, "rms"):
                sign_1 = 1
            else:
                sign_1 = 0

        if self.data2:
            if (Numaverage(self.data2_trend["HS_1X"]) >= 0.8) and (Numaverage(self.data2_trend["HDS_1X"]) >= 0.8) and get_VIB(self.data2, self.fs, self.rpm, "rms"):
                sign_2 = 1
            else:
                sign_2 = 0

        if self.data3:
            if (Numaverage(self.data3_trend["HS_1X"]) >= 0.8) and (Numaverage(self.data3_trend["HDS_1X"]) >= 0.8) and get_VIB(self.data3, self.fs, self.rpm, "rms"):
                sign_3 = 1
            else:
                sign_3 = 0

        if self.data4:
            if (Numaverage(self.data4_trend["HS_1X"]) >= 0.8) and (Numaverage(self.data4_trend["HDS_1X"]) >= 0.8) and get_VIB(self.data4, self.fs, self.rpm, "rms"):
                sign_4 = 1
            else:
                sign_4 = 0
        sign = sign_1 + sign_2 + sign_3 + sign_4
        if sign:
            return dict(故障模式=str(conclusion_return.iloc[13]["故障模式"]),
                        机理现象=str(conclusion_return.iloc[13]["机理现象"]),
                        机理原因=str(conclusion_return.iloc[13]["机理原因"]))
        else:
            return "转子支承部件没有松动"


    def zhuanzibujianliewen(self):  # 14 转子部件裂纹
        sign_1, sign_2, sign_3, sign_4 = 0, 0, 0, 0
        if self.data1:
            if (get_VIB(self.data1, self.fs, self.rpm, "xampl")[1] / get_VIB(self.data1, self.fs, self.rpm, "xampl")[0] >= 1.0) and (Numaverage(self.data1_trend["HDS_1X"]) >= 0.8) and get_VIB(self.data1, self.fs, self.rpm, "rms") >= 4.5:
                sign_1 = 1
            else:
                sign_1 = 0

        if self.data2:
            if (get_VIB(self.data2, self.fs, self.rpm, "xampl")[1] / get_VIB(self.data2, self.fs, self.rpm, "xampl")[0] >= 1.0) and (Numaverage(self.data2_trend["HDS_1X"]) >= 0.8) and get_VIB(self.data2, self.fs, self.rpm, "rms") >= 4.5:
                sign_2 = 1
            else:
                sign_2 = 0

        if self.data3:
            if (get_VIB(self.data3, self.fs, self.rpm, "xampl")[1] / get_VIB(self.data3, self.fs, self.rpm, "xampl")[0] >= 1.0) and (Numaverage(self.data3_trend["HDS_1X"]) >= 0.8) and get_VIB(self.data3, self.fs, self.rpm, "rms") >= 4.5:
                sign_3 = 1
            else:
                sign_3 = 0

        if self.data4:
            if (get_VIB(self.data4, self.fs, self.rpm, "xampl")[1] / get_VIB(self.data4, self.fs, self.rpm, "xampl")[0] >= 1.0) and (Numaverage(self.data4_trend["HDS_1X"]) >= 0.8) and get_VIB(self.data4, self.fs, self.rpm, "rms") >= 4.5:
                sign_4 = 1
            else:
                sign_4 = 0
        sign = sign_1 + sign_2 + sign_3 + sign_4
        if sign:
            return dict(故障模式=str(conclusion_return.iloc[14]["故障模式"]),
                        机理现象=str(conclusion_return.iloc[14]["机理现象"]),
                        机理原因=str(conclusion_return.iloc[14]["机理原因"]))
        else:
            return "转子部件没有裂纹"

    def dianjikeshangbuzhouwashuimowodong(self):  # 15 电机壳上部轴瓦水膜涡动
        sign_1, sign_2 = 0, 0
        if self.data1:
            if (amplitude(self.data1, self.fs, self.sw_freq) / get_VIB(self.data1, self.fs, self.rpm, "xampl")[0] >= 1.0) and (Numaverage(self.data1_trend["SW_X"]) >= 0.8):
                sign_1 = 1
            else:
                sign_1 = 0

        if self.data2:
            if (amplitude(self.data2, self.fs, self.sw_freq) / get_VIB(self.data2, self.fs, self.rpm, "xampl")[0] >= 1.0) and (Numaverage(self.data2_trend["SW_X"]) >= 0.8):
                sign_2 = 1
            else:
                sign_2 = 0

        sign = sign_1 + sign_2
        if sign:
            return dict(故障模式=str(conclusion_return.iloc[15]["故障模式"]),
                        机理现象=str(conclusion_return.iloc[15]["机理现象"]),
                        机理原因=str(conclusion_return.iloc[15]["机理原因"]))
        else:
            return "电机壳上部轴瓦没有水膜涡动"

    def dianjikexiabuzhouwashuimowodong(self):  # 16 电机壳下部轴瓦水膜涡动
        sign_3, sign_4 = 0, 0
        if self.data3:
            if (amplitude(self.data3, self.fs, self.sw_freq) / get_VIB(self.data3, self.fs, self.rpm, "xampl")[0] >= 1.0) and (Numaverage(self.data3_trend["SW_X"]) >= 0.8):
                sign_3 = 1
            else:
                sign_3 = 0

        if self.data4:
            if (amplitude(self.data4, self.fs, self.sw_freq) / get_VIB(self.data4, self.fs, self.rpm, "xampl")[0] >= 1.0) and (Numaverage(self.data4_trend["SW_X"]) >= 0.8):
                sign_4 = 1
            else:
                sign_4 = 0

        sign = sign_3 + sign_4
        if sign:
            return dict(故障模式=str(conclusion_return.iloc[16]["故障模式"]),
                        机理现象=str(conclusion_return.iloc[16]["机理现象"]),
                        机理原因=str(conclusion_return.iloc[16]["机理原因"]))

        else:
            return "电机壳下部轴瓦没有水膜涡动"

    def dianjikeshangbuzhouwamosun(self):  # 17 电机壳上部轴瓦磨损(轴承水温)
        sign_1, sign_2 = 0, 0
        if self.data1:
            if (Numaverage(self.data1_trend["HS_1X"]) >= 0.8) or (Numaverage(self.data1_trend["HDS_1X"]) >= 0.8) and get_VIB(self.data1, self.fs, self.rpm, "rms") >= 4.5) and ((Numaverage(self.data1_trend["BTemp"][0]) >= 0.8) or (Numaverage(self.data1_trend["BTemp"][1]) >= 0.8) or (Numaverage(self.data1_trend["BTemp"][2]) >= 0.8) or (Numaverage(self.data1_trend["BTemp"][3]) >= 0.8):
                sign_1 = 1
            else:
                sign_1 = 0

        if self.data2:
            if  ((Numaverage(self.data2_trend["HS_1X"]) >= 0.8) or (
                        Numaverage(self.data2_trend["HDS_1X"]) >= 0.8) and get_VIB(self.data2, self.fs, self.rpm,
                                                                                   "rms") >= 4.5) and \
                ((Numaverage(self.data2_trend["BTemp"][0]) >= 0.8) or (
                        Numaverage(self.data2_trend["BTemp"][1]) >= 0.8) or (
                         Numaverage(self.data2_trend["BTemp"][2]) >= 0.8) or (
                         Numaverage(self.data2_trend["BTemp"][3]) >= 0.8)):
                sign_2 = 1
            else:
                sign_2 = 0

        sign = sign_1 + sign_2
        if sign:
            return dict(故障模式=str(conclusion_return.iloc[17]["故障模式"]),
                        机理现象=str(conclusion_return.iloc[17]["机理现象"]),
                        机理原因=str(conclusion_return.iloc[17]["机理原因"]))

        else:
            return "电机壳上部轴瓦没有磨损"

    def dianjikexiabuzhouwamosun(self):  # 18 电机壳下部轴瓦磨损(轴承水温)
        sign_3, sign_4 = 0, 0
        if self.data3:
            if ((Numaverage(self.data3_trend["HS_1X"]) >= 0.8) or (
                Numaverage(self.data3_trend["HDS_1X"]) >= 0.8) and get_VIB(self.data3, self.fs, self.rpm,
                                                                           "rms") >= 4.5) and \
                ((Numaverage(self.data3_trend["BTemp"][0]) >= 0.8) or (
                        Numaverage(self.data3_trend["BTemp"][1]) >= 0.8) or (
                         Numaverage(self.data3_trend["BTemp"][2]) >= 0.8) or (
                         Numaverage(self.data3_trend["BTemp"][3]) >= 0.8)):
                sign_3 = 1
            else:
                sign_3 = 0

        if self.data4:
            if  ((Numaverage(self.data4_trend["HS_1X"]) >= 0.8) or (
                        Numaverage(self.data4_trend["HDS_1X"]) >= 0.8) and get_VIB(self.data4, self.fs, self.rpm,
                                                                                   "rms") >= 4.5) and \
                ((Numaverage(self.data4_trend["BTemp"][0]) >= 0.8) or (
                        Numaverage(self.data4_trend["BTemp"][1]) >= 0.8) or (
                         Numaverage(self.data4_trend["BTemp"][2]) >= 0.8) or (
                         Numaverage(self.data4_trend["BTemp"][3]) >= 0.8)):
                sign_4 = 1
            else:
                sign_4 = 0

        sign = sign_3, sign_4
        if sign:
            return dict(故障模式=str(conclusion_return.iloc[18]["故障模式"]),
                        机理现象=str(conclusion_return.iloc[18]["机理现象"]),
                        机理原因=str(conclusion_return.iloc[18]["机理原因"]))
        else:
            return "电机壳下部轴瓦没有磨损"

def devide_diagnosis(): ##总体检测函数

    # 传入文件
    alarm_message = {}
    # 报警信息：alarm_message
    # {"电机": ["电机自由侧X", "电机负荷侧"]
    #  "风机": ["风机自由侧", "风机负荷侧"]
    #  }
    json1 = {}
    trend_data ={}


    if  alarm_message.key.isin('电机'):
        diag = Bilengji_Dianji(json1, alarm_message, trend_data)


        diag.dingziyichang()  # 1,电机定子异常故障
        diag.qixipianxin() # 2, 电机气隙动态偏心
        diag.zhuanzitongtiaoduanlie() # 3 电机转子铜条断裂
        diag.zhuanzitongtiaosongdonghuotuoluo() # 4 电机转子铜条松动或脱落
        diag.zhuanzibupingheng()  # 5 转子不平衡
        diag.zhouwaduizhongbuliang()  # 7 轴瓦对中不良
        diag.zhuanzhourewanqu() # 8 转轴（热）弯曲  ###这里有轴向位置
        diag.dongjingbujianmoca()  # 9 动静部件摩擦
        diag.zhuanzibujiansongdong()  # 10 转子部件松动
        diag.xuanzhuanshisu()  # 11 旋转失速
        diag.qishihuodongjingganshe()  # 汽蚀（或动静干涉）
        diag.zhuanzizhichengbujiansongdong()  # 13 转子支承部件松动
        diag.zhuanzibujianliewen()  # 14 转子部件裂纹
        diag.dianjikeshangbuzhouwashuimowodong()  # 15 电机壳上部轴瓦水膜涡动
        diag.dianjikexiabuzhouwashuimowodong()  # 16 电机壳下部轴瓦水膜涡动
        diag.dianjikeshangbuzhouwamosun()  # 17 电机壳上部轴瓦磨损(轴承水温)
        diag.dianjikexiabuzhouwamosun()  # 18 电机壳下部轴瓦磨损(轴承水温)

























































