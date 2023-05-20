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
               
               "bff":["BPFI": BPFI, "BPFO": BPFO, "BSF": BSF, "FTF": FTF] # 轴承故障频率:Bearing failure frequency, 
                                                                         BPFI:轴承内圈故障频率; BPFO: 轴承外圈故障频率; BSF: 轴承滚动体故障频率; FTF: 轴承保持架故障
                "gmf":["value":[]]  # 齿轮啮合频率
        
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
# conclusion_return = pd.read_excel(r'F:\Aaxiaowei\算法组\雪工资料\主泵机理模型梳理20220715(1).xlsx')
conclusion_return = pd.read_excel(r'./池州海螺机理模型梳理.xlsx')  # 根据主泵和旋转设备整理而得

class Bilengji_Dianji:

    def __int__(self, json1, alarm_message, trend_data):
        self.point_data = json1["point_data"]
        self.point_info = json1['points_info']
        self.alarm_channel1 = alarm_message["电机"][0]  # 电机上壳横向振动X方向
        self.alarm_channel2 = alarm_message["电机"][1]  # 电机上壳横向振动Y方向
        self.alarm_channel3 = alarm_message["电机"][2]  # 电机下壳横向振动X方向
        self.alarm_channel4 = alarm_message["电机"][3]  # 电机下壳横向振动Y方向

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

        self.twosf0 = json1["twosf0"]  # 旋转磁场超越转子速度[f0/P- (1-s)f0/P] ×2P= 2sf0。
        self.fs = json1["fs"]  # 采样频率
        self.rpm = json1["rpm"]["转速"]  #
        self.X_1 = self.rpm / 60  # 一倍频

        self.bbf = json1["bbf"] # 轴承故障频率 ["BPFI": BPFI, "BPFO": BPFO, "BSF": BSF, "FTF": FTF]

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
            if (get_HCR(self.data1, self.fs, self.twosf0, 100, 5) >= 0.5 or get_HS(self.data1, self.fs, self.twosf0,
                                                                                   5) / get_HS(self.data1, self.fs,
                                                                                               self.X_1, 1) >= 1):
                sign_1 = 1
            else:
                sign_1 = 0

        if self.data2:
            if (get_HCR(self.data2, self.fs, self.twosf0, 100, 5) >= 0.5 or get_HS(self.data2, self.fs, self.twosf0,
                                                                                   5) / get_HS(self.data2, self.fs,
                                                                                               self.X_1, 1) >= 1):
                sign_2 = 1
            else:
                sign_2 = 0

        if self.data3:
            if (get_HCR(self.data3, self.fs, self.twosf0, 100, 5) >= 0.5 or get_HS(self.data3, self.fs, self.twosf0,
                                                                                   5) / get_HS(self.data3, self.fs,
                                                                                               self.X_1, 1) >= 1):
                sign_3 = 1
            else:
                sign_3 = 0

        if self.data4:
            if (get_HCR(self.data4, self.fs, self.twosf0, 100, 5) >= 0.5 or get_HS(self.data4, self.fs, self.twosf0,
                                                                                   5) / get_HS(self.data4, self.fs,
                                                                                               self.X_1, 1) >= 1):
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
            if (get_HCR(self.data1, self.fs, self.twosf0, 100, 5) >= 0.5 or Numaverage(
                    self.data1_trend["1倍频"]) >= 0.8):
                sign_1 = 1
            else:
                sign_1 = 0

        if self.data2:
            if (get_HCR(self.data2, self.fs, self.twosf0, 100, 5) >= 0.5 or Numaverage(
                    self.data2_trend["1倍频"]) >= 0.8):
                sign_2 = 1
            else:
                sign_2 = 0

        if self.data3:
            if (get_HCR(self.data2, self.fs, self.twosf0, 100, 5) >= 0.5 or Numaverage(
                    self.data2_trend["1倍频"]) >= 0.8):
                sign_3 = 1
            else:
                sign_3 = 0

        if self.data4:
            if (get_HCR(self.data2, self.fs, self.twosf0, 100, 5) >= 0.5 or Numaverage(
                    self.data2_trend["1倍频"]) >= 0.8):
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

    def zhuanzibupingheng(self):  # 5 转子不平衡
        sign_1, sign_2, sign_3, sign_4 = 0, 0, 0, 0
        if self.data1:
            if (get_VIB(self.data1, self.fs, self.rpm, "xampl")[0] / get_VIB(self.data1, self.fs, self.rpm,
                                                                             "acc_rms") >= 0.4 or Numaverage(
                    self.data1_trend["1倍频"]) >= 0.8):
                sign_1 = 1
            else:
                sign_1 = 0

        if self.data2:
            if (get_VIB(self.data2, self.fs, self.rpm, "xampl")[0] / get_VIB(self.data2, self.fs, self.rpm,
                                                                             "acc_rms") >= 0.4 or Numaverage(
                    self.data2_trend["1倍频"]) >= 0.8):
                sign_2 = 1
            else:
                sign_2 = 0

        if self.data3:
            if (get_VIB(self.data3, self.fs, self.rpm, "xampl")[0] / get_VIB(self.data3, self.fs, self.rpm,
                                                                             "acc_rms") >= 0.4 or Numaverage(
                    self.data3_trend["1倍频"]) >= 0.8):
                sign_3 = 1
            else:
                sign_3 = 0

        if self.data4:
            if (get_VIB(self.data4, self.fs, self.rpm, "xampl")[0] / get_VIB(self.data4, self.fs, self.rpm,
                                                                             "acc_rms") >= 0.4 or Numaverage(
                    self.data4_trend["1倍频"]) >= 0.8):
                sign_4 = 1
            else:
                sign_4 = 0
        sign = sign_1 + sign_2 + sign_3 + sign_4
        if sign:
            return dict(故障模式=str(conclusion_return.iloc[3]["故障模式"]),
                        机理现象=str(conclusion_return.iloc[3]["机理现象"]),
                        机理原因=str(conclusion_return.iloc[3]["机理原因"]))
        else:
            return "电机转子平衡"

    def zhouwaduizhongbuliang(self):  # 7 轴瓦对中不良
        sign_1, sign_2, sign_3, sign_4 = 0, 0, 0, 0
        if self.data1:
            if (get_VIB(self.data1, self.fs, self.rpm, "xampl")[1] / get_VIB(self.data1, self.fs, self.rpm, "xampl")[
                0] >= 1.0 or Numaverage(self.data1_trend["2倍频"]) >= 0.8):
                sign_1 = 1
            else:
                sign_1 = 0

        if self.data2:
            if (get_VIB(self.data2, self.fs, self.rpm, "xampl")[1] / get_VIB(self.data2, self.fs, self.rpm, "xampl")[
                0] >= 1.0 or Numaverage(self.data2_trend["2倍频"]) >= 0.8):
                sign_2 = 1
            else:
                sign_2 = 0

        if self.data3:
            if (get_VIB(self.data3, self.fs, self.rpm, "xampl")[1] / get_VIB(self.data3, self.fs, self.rpm, "xampl")[
                0] >= 1.0 or Numaverage(self.data3_trend["2倍频"]) >= 0.8):
                sign_3 = 1
            else:
                sign_3 = 0

        if self.data4:
            if (get_VIB(self.data4, self.fs, self.rpm, "xampl")[1] / get_VIB(self.data4, self.fs, self.rpm, "xampl")[
                0] >= 1.0 or Numaverage(self.data4_trend["2倍频"]) >= 0.8):
                sign_4 = 1
            else:
                sign_4 = 0
        sign = sign_1 + sign_2 + sign_3 + sign_4
        if sign:
            return dict(故障模式=str(conclusion_return.iloc[4]["故障模式"]),
                        机理现象=str(conclusion_return.iloc[4]["机理现象"]),
                        机理原因=str(conclusion_return.iloc[4]["机理原因"]))
        else:
            return "轴瓦对中正常"

    def zhuanzibujiansongdong(self):  # 10 转子部件松动
        sign_1, sign_2, sign_3, sign_4 = 0, 0, 0, 0
        if self.data1:
            if (get_VIB(self.data1, self.fs, self.rpm, "xampl")[1] / get_VIB(self.data1, self.fs, self.rpm, "xampl")[
                0]) and (Numaverage(self.data1_trend["HDS_1X"]) >= 0.8):
                sign_1 = 1
            else:
                sign_1 = 0

        if self.data2:
            if (get_VIB(self.data2, self.fs, self.rpm, "xampl")[1] / get_VIB(self.data2, self.fs, self.rpm, "xampl")[
                0]) and (Numaverage(self.data2_trend["HDS_1X"]) >= 0.8):
                sign_2 = 1
            else:
                sign_2 = 0

        if self.data3:
            if (get_VIB(self.data3, self.fs, self.rpm, "xampl")[1] / get_VIB(self.data3, self.fs, self.rpm, "xampl")[
                0]) and (Numaverage(self.data3_trend["HDS_1X"]) >= 0.8):
                sign_3 = 1
            else:
                sign_3 = 0

        if self.data4:
            if (get_VIB(self.data4, self.fs, self.rpm, "xampl")[1] / get_VIB(self.data4, self.fs, self.rpm, "xampl")[
                0]) and (Numaverage(self.data4_trend["HDS_1X"]) >= 0.8):
                sign_4 = 1
            else:
                sign_4 = 0
        sign = sign_1 + sign_2 + sign_3 + sign_4
        if sign:
            return dict(故障模式=str(conclusion_return.iloc[5]["故障模式"]),
                        机理现象=str(conclusion_return.iloc[5]["机理现象"]),
                        机理原因=str(conclusion_return.iloc[5]["机理原因"]))
        else:
            return "转子部件没有松动"

    def zhouchengguzhang(self):
        '''电机中轴承故障，包括：内圈、外圈、滚动体、保持架和不对中物种故障
            规则来源：旋转设备机理模型（三版2021105）.xlsx
            1，轴承内圈故障："HS(水平，BPFI，5）/overall(水平）>0.4 && speedall(水平）>4.5 || HS(竖直，BPFI，5）/overall(竖直）>0.4 && speedall(竖直）>4.5”
            2，轴承外圈故障："HS(水平，BPFO，5）/overall(水平）>0.4 && speedall(水平）>4.5 || HS(竖直，BPFO，5）/overall(竖直）>0.4 && speedall(竖直）>4.5 "
            3，轴承滚动体故障："HS(水平，BSF，5）/overall(水平）>0.4 && speedall(水平）>4.5 || HS(竖直，BSF，5）/overall(竖直）>0.4 && speedall(竖直）>4.5 "
            4，轴承保持架故障："HS(水平，FTF，5）/overall(水平）>0.4 && speedall(水平）>4.5 || HS(竖直，FTF，5）/overall(竖直）>0.4 && speedall(竖直）>4.5"
            5，"HS(水平，二倍频，1）/overall(水平1）>0.4  && speedall(水平1）>4.5|| HS(竖直，二倍频，1）/overall(竖直1）>0.4  && speedall(竖直1）>4.5 "

        '''

        if self.data1 or self.data2:
            if (get_HS(self.data1, self.fs, self.bbf["BPFI"], 5) / get_VIB(self.data1, self.fs, self.rpm, "xampl")[
                1] > 0.4 and get_VIB(self.data1, self.fs, self.rpm, "rms") > 4.5) or \
                (get_HS(self.data2, self.fs, self.bbf["BPFI"], 5) / get_VIB(self.data2, self.fs, self.rpm, "xampl")[
                1]> 0.4 and get_VIB(self.data2, self.fs, self.rpm, "rms") > 4.5):
                return dict(故障模式=str(conclusion_return.iloc[6]["故障模式"]),
                        机理现象=str(conclusion_return.iloc[6]["机理现象"]),
                        机理原因=str(conclusion_return.iloc[6]["机理原因"]))

        if self.data1 or self.data2:
            if (get_HS(self.data1, self.fs, self.bbf["BPFO"], 5) / get_VIB(self.data1, self.fs, self.rpm, "xampl")[
                1] > 0.4 and get_VIB(self.data1, self.fs, self.rpm, "rms") > 4.5) or \
                    (get_HS(self.data2, self.fs, self.bbf["BPFO"], 5) / get_VIB(self.data2, self.fs, self.rpm, "xampl")[
                1] > 0.4 and get_VIB(self.data2, self.fs, self.rpm, "rms") > 4.5):
                return dict(故障模式=str(conclusion_return.iloc[7]["故障模式"]),
                        机理现象=str(conclusion_return.iloc[7]["机理现象"]),
                        机理原因=str(conclusion_return.iloc[7]["机理原因"]))

        if self.data1 or self.data2:
            if (get_HS(self.data1, self.fs, self.bbf["BSF"], 5) / get_VIB(self.data1, self.fs, self.rpm, "xampl")[
                1] > 0.4 and get_VIB(self.data2, self.fs, self.rpm, "rms") > 4.5) or \
                    (get_HS(self.data1, self.fs, self.bbf["BSF"], 5) / get_VIB(self.data2, self.fs, self.rpm, "xampl")[
                1] > 0.4 and get_VIB(self.data2, self.fs, self.rpm, "rms") > 4.5):
                return dict(故障模式=str(conclusion_return.iloc[8]["故障模式"]),
                        机理现象=str(conclusion_return.iloc[8]["机理现象"]),
                        机理原因=str(conclusion_return.iloc[8]["机理原因"]))

        if self.data1 or self.data2:
            if (get_HS(self.data1, self.fs, self.bbf["FTF"], 5) / get_VIB(self.data1, self.fs, self.rpm, "xampl")[
                1] > 0.4 and get_VIB(self.data2, self.fs, self.rpm, "rms") > 4.5) or \
                    (get_HS(self.data2, self.fs, self.bbf["FTF"], 5) / get_VIB(self.data2, self.fs, self.rpm, "xampl")[
                1] > 0.4 and get_VIB(self.data2, self.fs, self.rpm, "rms") > 4.5):
                return dict(故障模式=str(conclusion_return.iloc[9]["故障模式"]),
                        机理现象=str(conclusion_return.iloc[9]["机理现象"]),
                        机理原因=str(conclusion_return.iloc[9]["机理原因"]))

        if self.data1 or self.data2:
            if (get_HS(self.data1, self.fs, self.X_1*2, 1) / get_VIB(self.data1, self.fs, self.rpm, "xampl")[
                1] > 0.4 and get_VIB(self.data1, self.fs, self.rpm, "rms") > 4.5) or \
                    (get_HS(self.data2, self.fs, self.X_1*2, 1) / get_VIB(self.data2, self.fs, self.rpm, "xampl")[
                1] > 0.4 and get_VIB(self.data2, self.fs, self.rpm,  "rms") > 4.5):
                return dict(故障模式=str(conclusion_return.iloc[10]["故障模式"]),
                        机理现象=str(conclusion_return.iloc[10]["机理现象"]),
                        机理原因=str(conclusion_return.iloc[10]["机理原因"]))


class Bilengji_Fengji:

    def __int__(self, json1, alarm_message, trend_data):
        self.point_data = json1["point_data"]
        self.point_info = json1['points_info']
        self.alarm_channel1 = alarm_message["电机"][0]  # 风机驱动端水平
        self.alarm_channel2 = alarm_message["电机"][1]  # 风机驱动端竖直
        self.alarm_channel3 = alarm_message["电机"][2]  # 风机非驱端水平
        self.alarm_channel4 = alarm_message["电机"][3]  # 风机非驱端竖直

        self.data1 = self.point_data[self.alarm_channel1]['vel_data']['value']  #
        self.frequency_1 = self.point_info[self.alarm_channel1]['sn_info']['hz']
        self.data2 = self.point_data[self.alarm_channel2]['vel_data']['value']
        self.frequency_2 = self.point_info[self.alarm_channel2]['sn_info']['hz']
        self.data3 = self.point_data[self.alarm_channel3]['vel_data']['value']  #
        self.frequency_3 = self.point_info[self.alarm_channel3]['sn_info']['hz']
        self.data4 = self.point_data[self.alarm_channel4]['vel_data']['value']
        self.frequency_4 = self.point_info[self.alarm_channel4]['sn_info']['hz']

        self.data1_trend = trend_data[alarm_message["风机"][0]]
        self.data2_trend = trend_data[alarm_message["风机"][1]]
        self.data3_trend = trend_data[alarm_message["风机"][2]]
        self.data4_trend = trend_data[alarm_message["风机"][3]]

        self.twosf0 = json1["twosf0"]  # 旋转磁场超越转子速度[f0/P- (1-s)f0/P] ×2P= 2sf0。
        self.fs = json1["fs"]  # 采样频率
        self.rpm = json1["rpm"]["转速"]  #
        self.X_1 = self.rpm / 60  # 一倍频

        self.bbf = json1["bbf"] # 轴承故障频率 ["BPFI": BPFI, "BPFO": BPFO, "BSF": BSF, "FTF": FTF]

    def bupingheng(self):
        '''不平衡故障
        "HS(水平1，一倍频幅值，1）/overall(水平1）>0.4  && speedall(水平1）>4.5||
        HS(竖直1，一倍频幅值，1）/overall(竖直1）>0.4  && speedall(竖直1）>4.5||
        HS(水平2，一倍频幅值，1）/overall(水平2）>0.4  && speedall(水平2）>4.5||
        HS(竖直2，一倍频幅值，1）/overall(竖直2）>0.4  && speedall(竖直2）>4.5"
        '''

        sign_1, sign_2, sign_3, sign_4 = 0, 0, 0, 0

        if self.data1:
            if (get_HS(self.data1, self.fs, self.X_1, 1) / get_VIB(self.data1, self.fs, self.rpm, "xampl")[1] > 0.4 and get_VIB(self.data1, self.fs, self.rpm, "rms") > 4.5):
                sign_1 = 1
            else:
                sign_1 = 0

        if self.data2:
            if (get_HS(self.data2, self.fs, self.X_1, 1) / get_VIB(self.data2, self.fs, self.rpm, "xampl")[1] > 0.4 and get_VIB(self.data2, self.fs, self.rpm, "rms") > 4.5):
                sign_2 = 1
            else:
                sign_2 = 0

        if self.data3:
            if (get_HS(self.data3, self.fs, self.X_1, 1) / get_VIB(self.data3, self.fs, self.rpm, "xampl")[1] > 0.4 and get_VIB(self.data3, self.fs, self.rpm, "rms") > 4.5):
                sign_3 = 1
            else:
                sign_3 = 0

        if self.data4:
            if (get_HS(self.data4, self.fs, self.X_1, 1) / get_VIB(self.data4, self.fs, self.rpm, "xampl")[1] > 0.4 and get_VIB(self.data4, self.fs, self.rpm, "rms") > 4.5):
                sign_4 = 1
            else:
                sign_4 = 0

        sign = sign_1 + sign_2 + sign_3 + sign_4
        if sign:
            return dict(故障模式=str(conclusion_return.iloc[11]["故障模式"]),
                        机理现象=str(conclusion_return.iloc[11]["机理现象"]),
                        机理原因=str(conclusion_return.iloc[11]["机理原因"]))
        else:
            return "风机转子平衡"

    def zhuanzibuduizhong(self):
        '''不对中故障
        "HS(水平1，二倍频幅值，1）/overall(水平1）>0.4  && speedall(水平1）>4.5||
        HS(竖直1，二倍频幅值，1）/overall(竖直1）>0.4  && speedall(竖直1）>4.5||
        HS(水平2，二倍频幅值，1）/overall(水平2）>0.4  && speedall(水平2）>4.5||
        HS(竖直2，二倍频幅值，1）/overall(竖直2）>0.4  && speedall(竖直2）>4.5"

        '''
        sign_1, sign_2, sign_3, sign_4 = 0, 0, 0, 0

        if self.data1:
            if (get_HS(self.data1, self.fs, self.X_1*2, 1) / get_VIB(self.data1, self.fs, self.rpm, "xampl")[
                1] > 0.4 and get_VIB(self.data1, self.fs, self.rpm, "rms") > 4.5):
                sign_1 = 1
            else:
                sign_1 = 0

        if self.data2:
            if (get_HS(self.data2, self.fs, self.X_1*2, 1) / get_VIB(self.data2, self.fs, self.rpm, "xampl")[
                1] > 0.4 and get_VIB(self.data2, self.fs, self.rpm, "rms") > 4.5):
                sign_2 = 1
            else:
                sign_2 = 0

        if self.data3:
            if (get_HS(self.data3, self.fs, self.X_1*2, 1) / get_VIB(self.data3, self.fs, self.rpm, "xampl")[
                1] > 0.4 and get_VIB(self.data3, self.fs, self.rpm, "rms") > 4.5):
                sign_3 = 1
            else:
                sign_3 = 0

        if self.data4:
            if (get_HS(self.data4, self.fs, self.X_1*2, 1) / get_VIB(self.data4, self.fs, self.rpm, "xampl")[
                1] > 0.4 and get_VIB(self.data4, self.fs, self.rpm, "rms") > 4.5):
                sign_4 = 1
            else:
                sign_4 = 0

        sign = sign_1 + sign_2 + sign_3 + sign_4
        if sign:
            return dict(故障模式=str(conclusion_return.iloc[12]["故障模式"]),  # 机理模型读入新的的表格
                        机理现象=str(conclusion_return.iloc[12]["机理现象"]),
                        机理原因=str(conclusion_return.iloc[12]["机理原因"]))
        else:
            return "风机转子对中"

    def zhouchengguzhang(self):
        '''电机中轴承故障，包括：内圈、外圈、滚动体、保持架和不对中物种故障
            规则来源：旋转设备机理模型（三版2021105）.xlsx
            1，轴承内圈故障："HS(水平，BPFI，5）/overall(水平）>0.4 && speedall(水平）>4.5 || HS(竖直，BPFI，5）/overall(竖直）>0.4 && speedall(竖直）>4.5”
            2，轴承外圈故障："HS(水平，BPFO，5）/overall(水平）>0.4 && speedall(水平）>4.5 || HS(竖直，BPFO，5）/overall(竖直）>0.4 && speedall(竖直）>4.5 "
            3，轴承滚动体故障："HS(水平，BSF，5）/overall(水平）>0.4 && speedall(水平）>4.5 || HS(竖直，BSF，5）/overall(竖直）>0.4 && speedall(竖直）>4.5 "
            4，轴承保持架故障："HS(水平，FTF，5）/overall(水平）>0.4 && speedall(水平）>4.5 || HS(竖直，FTF，5）/overall(竖直）>0.4 && speedall(竖直）>4.5"
            5，"HS(水平，二倍频，1）/overall(水平1）>0.4  && speedall(水平1）>4.5|| HS(竖直，二倍频，1）/overall(竖直1）>0.4  && speedall(竖直1）>4.5 "

        '''

        if self.data1 or self.data2:
            if (get_HS(self.data1, self.fs, self.bbf["BPFI"], 5) / get_VIB(self.data1, self.fs, self.rpm, "xampl")[
                1] > 0.4 and get_VIB(self.data1, self.fs, self.rpm, "impulse") > 3) or \
                (get_HS(self.data2, self.fs, self.bbf["BPFI"], 5) / get_VIB(self.data2, self.fs, self.rpm, "xampl")[
                1]> 0.4 and get_VIB(self.data2, self.fs, self.rpm, "impulse") > 3):
                return dict(故障模式=str(conclusion_return.iloc[6]["故障模式"]),
                        机理现象=str(conclusion_return.iloc[6]["机理现象"]),
                        机理原因=str(conclusion_return.iloc[6]["机理原因"]))

        if self.data1 or self.data2:
            if (get_HS(self.data1, self.fs, self.bbf["BPFO"], 5) / get_VIB(self.data1, self.fs, self.rpm, "xampl")[
                1] > 0.4 and get_VIB(self.data1, self.fs, self.rpm, "impulse") > 3) or \
                    (get_HS(self.data2, self.fs, self.bbf["BPFO"], 5) / get_VIB(self.data2, self.fs, self.rpm, "xampl")[
                1] > 0.4 and get_VIB(self.data2, self.fs, self.rpm, "impulse") > 3):
                return dict(故障模式=str(conclusion_return.iloc[7]["故障模式"]),
                        机理现象=str(conclusion_return.iloc[7]["机理现象"]),
                        机理原因=str(conclusion_return.iloc[7]["机理原因"]))

        if self.data1 or self.data2:
            if (get_HS(self.data1, self.fs, self.bbf["BSF"], 5) / get_VIB(self.data1, self.fs, self.rpm, "xampl")[
                1] > 0.4 and get_VIB(self.data2, self.fs, self.rpm, "impulse") > 3) or \
                    (get_HS(self.data1, self.fs, self.bbf["BSF"], 5) / get_VIB(self.data2, self.fs, self.rpm, "xampl")[
                1] > 0.4 and get_VIB(self.data2, self.fs, self.rpm,"impulse") > 3):
                return dict(故障模式=str(conclusion_return.iloc[8]["故障模式"]),
                        机理现象=str(conclusion_return.iloc[8]["机理现象"]),
                        机理原因=str(conclusion_return.iloc[8]["机理原因"]))

        if self.data1 or self.data2:
            if (get_HS(self.data1, self.fs, self.bbf["FTF"], 5) / get_VIB(self.data1, self.fs, self.rpm, "xampl")[
                1] > 0.4 and get_VIB(self.data2, self.fs, self.rpm, "impulse") > 3) or \
                    (get_HS(self.data2, self.fs, self.bbf["FTF"], 5) / get_VIB(self.data2, self.fs, self.rpm, "xampl")[
                1] > 0.4 and get_VIB(self.data2, self.fs, self.rpm, "impulse") > 3):
                return dict(故障模式=str(conclusion_return.iloc[9]["故障模式"]),
                        机理现象=str(conclusion_return.iloc[9]["机理现象"]),
                        机理原因=str(conclusion_return.iloc[9]["机理原因"]))

        if self.data1 or self.data2:
            if (get_HS(self.data1, self.fs, self.X_1*2, 1) / get_VIB(self.data1, self.fs, self.rpm, "xampl")[
                1] > 0.4 and get_VIB(self.data1, self.fs, self.rpm, "rms") > 4.5) or \
                    (get_HS(self.data2, self.fs, self.X_1*2, 1) / get_VIB(self.data2, self.fs, self.rpm, "xampl")[
                1] > 0.4 and get_VIB(self.data2, self.fs, self.rpm,  "rms") > 4.5):
                return dict(故障模式=str(conclusion_return.iloc[10]["故障模式"]),
                        机理现象=str(conclusion_return.iloc[10]["机理现象"]),
                        机理原因=str(conclusion_return.iloc[10]["机理原因"]))


class Gearbox:

    def __int__(self, json1, alarm_message, trend_data):
        self.point_data = json1["point_data"]
        self.point_info = json1['points_info']
        self.alarm_channel1 = alarm_message["齿轮箱"][0]  # 齿轮驱动端水平
        self.alarm_channel2 = alarm_message["齿轮箱"][1]  # 齿轮驱动端竖直


        self.data1 = self.point_data[self.alarm_channel1]['vel_data']['value']  #
        self.frequency_1 = self.point_info[self.alarm_channel1]['sn_info']['hz']
        self.data2 = self.point_data[self.alarm_channel2]['vel_data']['value']
        self.frequency_2 = self.point_info[self.alarm_channel2]['sn_info']['hz']


        self.data1_trend = trend_data[alarm_message["齿轮箱"][0]]
        self.data2_trend = trend_data[alarm_message["齿轮箱"][1]]


        self.fs = json1["fs"]  # 采样频率
        self.rpm = json1["rpm"]["转速"]  #
        self.X_1 = self.rpm / 60  # 一倍频
        self.GMF = json1["GMF"] # 齿轮啮合频率

        self.bbf = json1["bbf"] # 轴承故障频率 ["BPFI": BPFI, "BPFO": BPFO, "BSF": BSF, "FTF": FTF]

    def cilunbupingheng(self):
        '''齿轮不平衡
        "HCR(水平，1X，GMF，5）>0.4  && speedall(水平1）>4.5 && HS(水平，1X，5）/overall(水平）>0.4 ||
         HCR(水平，1X，GMF，5）>0.4  && speedall(竖直1）>4.5 &&  HS(竖直，1X，5）/overall(竖直）>0.4 "
        '''
        sign_1, sign_2 = 0, 0
        if self.data1:
            if get_HS(self.data1, self.fs, self.X_1, 5) / get_VIB(self.data1, self.fs, self.rpm, "xampl")[1] > 0.4 and get_VIB(self.data1, self.fs, self.rpm, "rms") > 4.5 and get_HCR(self.data1, self.fs, self.X_1, self.GMF, 5) >= 0.4 :
                sign_1 = 1
            else:
                sign_1 = 0

        if self.data2:
            if get_HS(self.data2, self.fs, self.X_1, 5) / get_VIB(self.data2, self.fs, self.rpm, "xampl")[1] > 0.4 and get_VIB(self.data2, self.fs, self.rpm, "rms") > 4.5 and get_HCR(self.data2, self.fs, self.X_1, self.GMF, 5) >= 0.4 :
                sign_2 = 1
            else:
                sign_2 = 0

        sign = sign_1 + sign_2

        if sign:
            return dict(故障模式=str(conclusion_return.iloc[13]["故障模式"]),
                        机理现象=str(conclusion_return.iloc[13]["机理现象"]),
                        机理原因=str(conclusion_return.iloc[13]["机理原因"]))
        else:
            return "齿轮平衡"

    def cilunbutongzhou(self):
        '''齿轮不同轴
        "HCR(水平，1X，GMF，5）>0.4  && speedall(水平1）>4.5 && HS(水平，1X，5）/overall(水平）>0.4 ||
        HCR(竖直，1X，GMF，5）>0.4  && speedall(竖直1）>4.5 &&  HS(竖直，1X，5）/overall(竖直）>0.4 "
        '''
        sign_1, sign_2 = 0, 0
        if self.data1:
            if get_HCR(self.data1, self.fs,self.X_1, self.GMF, 5) > 0.4 and get_VIB(self.data1, self.fs, self.rpm, "rms") > 4.5 and get_HS(self.data1, self.fs, self.X_1, 5) / get_VIB(self.data1, self.fs, self.rpm, "xampl")[1] > 0.4 :
                sign_1 = 1
            else:
                sign_1 = 0

        if self.data2:
            if get_HCR(self.data2, self.fs,self.X_1, self.GMF,5) >= 0.4 and get_VIB(self.data2, self.fs, self.rpm, "rms") > 4.5 and get_HS(self.data2, self.fs, self.X_1, 5) / get_VIB(self.data2, self.fs, self.rpm, "xampl")[1] > 0.4 :
                sign_2 = 1
            else:
                sign_2 = 0

        sign = sign_1 + sign_2

        if sign:
            return dict(故障模式=str(conclusion_return.iloc[14]["故障模式"]),
                        机理现象=str(conclusion_return.iloc[14]["机理现象"]),
                        机理原因=str(conclusion_return.iloc[14]["机理原因"]))
        else:
            return "齿轮同轴"

    def chimianmoshun(self):
        '''齿面磨损
        "HS(水平，1X，5）/overall(水平）>0.4 && speedall(水平）>4.5 && HCR(水平，1X，GMF，1）>0.4 ||
        HS(竖直，1X，5）/overall(竖直）>0.4 && speedall(竖直）>4.5 &&  HCR(竖直，1X，GMF，1）>0.4 "
        '''

        sign_1, sign_2 = 0, 0
        if self.data1:
            if get_HCR(self.data1, self.fs, self.X_1, self.GMF, 1) > 0.4 and get_VIB(self.data1, self.fs, self.rpm,
                                                                                     "rms") > 4.5 and get_HS(self.data1,
                                                                                                             self.fs,
                                                                                                             self.X_1, 5) / \
                    get_VIB(self.data1, self.fs, self.rpm, "xampl")[1] > 0.4:
                sign_1 = 1
            else:
                sign_1 = 0

        if self.data2:
            if get_HCR(self.data2, self.fs, self.X_1, self.GMF, 1) >= 0.4 and get_VIB(self.data2, self.fs, self.rpm,
                                                                                      "rms") > 4.5 and get_HS(self.data2,
                                                                                                              self.fs,
                                                                                                              self.X_1, 5) / \
                    get_VIB(self.data2, self.fs, self.rpm, "xampl")[1] > 0.4:
                sign_2 = 1
            else:
                sign_2 = 0

        sign = sign_1 + sign_2

        if sign:
            return dict(故障模式=str(conclusion_return.iloc[15]["故障模式"]),
                        机理现象=str(conclusion_return.iloc[15]["机理现象"]),
                        机理原因=str(conclusion_return.iloc[15]["机理原因"]))
        else:
            return "齿轮没有齿面磨损"

    def zhouchengguzhang(self):
        '''轴承故障，包括：内圈、外圈、滚动体、保持架和不对中物种故障
            规则来源：旋转设备机理模型（三版2021105）.xlsx
            1，轴承内圈故障："HS(水平，BPFI，5）/overall(水平）>0.4 && speedall(水平）>4.5 || HS(竖直，BPFI，5）/overall(竖直）>0.4 && speedall(竖直）>4.5”
            2，轴承外圈故障："HS(水平，BPFO，5）/overall(水平）>0.4 && speedall(水平）>4.5 || HS(竖直，BPFO，5）/overall(竖直）>0.4 && speedall(竖直）>4.5 "
            3，轴承滚动体故障："HS(水平，BSF，5）/overall(水平）>0.4 && speedall(水平）>4.5 || HS(竖直，BSF，5）/overall(竖直）>0.4 && speedall(竖直）>4.5 "
            4，轴承保持架故障："HS(水平，FTF，5）/overall(水平）>0.4 && speedall(水平）>4.5 || HS(竖直，FTF，5）/overall(竖直）>0.4 && speedall(竖直）>4.5"
            5，"HS(水平，二倍频，1）/overall(水平1）>0.4  && speedall(水平1）>4.5|| HS(竖直，二倍频，1）/overall(竖直1）>0.4  && speedall(竖直1）>4.5 "

        '''

        if self.data1 or self.data2:
            if (get_HS(self.data1, self.fs, self.bbf["BPFI"], 5) / get_VIB(self.data1, self.fs, self.rpm, "xampl")[
                1] > 0.4 and get_VIB(self.data1, self.fs, self.rpm, "impulse") > 3) or \
                (get_HS(self.data2, self.fs, self.bbf["BPFI"], 5) / get_VIB(self.data2, self.fs, self.rpm, "xampl")[
                1]> 0.4 and get_VIB(self.data2, self.fs, self.rpm, "impulse") > 3):
                return dict(故障模式=str(conclusion_return.iloc[7]["故障模式"]),
                        机理现象=str(conclusion_return.iloc[7]["机理现象"]),
                        机理原因=str(conclusion_return.iloc[7]["机理原因"]))

        if self.data1 or self.data2:
            if (get_HS(self.data1, self.fs, self.bbf["BPFO"], 5) / get_VIB(self.data1, self.fs, self.rpm, "xampl")[
                1] > 0.4 and get_VIB(self.data1, self.fs, self.rpm, "impulse") > 3) or \
                    (get_HS(self.data2, self.fs, self.bbf["BPFO"], 5) / get_VIB(self.data2, self.fs, self.rpm, "xampl")[
                1] > 0.4 and get_VIB(self.data2, self.fs, self.rpm, "impulse") > 3):
                return dict(故障模式=str(conclusion_return.iloc[8]["故障模式"]),
                        机理现象=str(conclusion_return.iloc[8]["机理现象"]),
                        机理原因=str(conclusion_return.iloc[8]["机理原因"]))

        if self.data1 or self.data2:
            if (get_HS(self.data1, self.fs, self.bbf["BSF"], 5) / get_VIB(self.data1, self.fs, self.rpm, "xampl")[
                1] > 0.4 and get_VIB(self.data2, self.fs, self.rpm, "impulse") > 3) or \
                    (get_HS(self.data1, self.fs, self.bbf["BSF"], 5) / get_VIB(self.data2, self.fs, self.rpm, "xampl")[
                1] > 0.4 and get_VIB(self.data2, self.fs, self.rpm,"impulse") > 3):
                return dict(故障模式=str(conclusion_return.iloc[9]["故障模式"]),
                        机理现象=str(conclusion_return.iloc[9]["机理现象"]),
                        机理原因=str(conclusion_return.iloc[9]["机理原因"]))


        if self.data1 or self.data2:
            if (get_HS(self.data1, self.fs, self.bbf["FTF"], 5) / get_VIB(self.data1, self.fs, self.rpm, "xampl")[
                1] > 0.4 and get_VIB(self.data1, self.fs, self.rpm,"impulse") > 3) or \
                    (get_HS(self.data2, self.fs, self.bbf["FTF"], 5) / get_VIB(self.data2, self.fs, self.rpm, "xampl")[
                1] > 0.4 and get_VIB(self.data2, self.fs, self.rpm, "impulse") > 3):
                return dict(故障模式=str(conclusion_return.iloc[10]["故障模式"]),
                        机理现象=str(conclusion_return.iloc[10]["机理现象"]),
                        机理原因=str(conclusion_return.iloc[10]["机理原因"]))

        if self.data1 or self.data2:
            if (get_HS(self.data1, self.fs, self.X_1*2, 1) / get_VIB(self.data1, self.fs, self.rpm, "xampl")[
                1] > 0.4 and get_VIB(self.data1, self.fs, self.rpm, "rms") > 4.5) or \
                    (get_HS(self.data2, self.fs, self.X_1*2, 1) / get_VIB(self.data2, self.fs, self.rpm, "xampl")[
                1] > 0.4 and get_VIB(self.data2, self.fs, self.rpm,  "rms") > 4.5):
                return dict(故障模式=str(conclusion_return.iloc[11]["故障模式"]),
                        机理现象=str(conclusion_return.iloc[11]["机理现象"]),
                        机理原因=str(conclusion_return.iloc[11]["机理原因"]))


class Fengji:
    def __int__(self, json1, alarm_message, trend_data):
        self.point_data = json1["point_data"]
        self.point_info = json1['points_info']
        self.alarm_channel1 = alarm_message["风机"][0]  # 风机驱动端水平 或轴承端水平
        self.alarm_channel2 = alarm_message["风机"][1]  # 风机驱动端竖直 或轴承端竖直
        self.alarm_channel3 = alarm_message["风机"][2]  # 风机非驱端水平
        self.alarm_channel4 = alarm_message["风机"][3]  # 风机非驱端竖直



        self.data1 = self.point_data[self.alarm_channel1]['vel_data']['value']  #
        self.frequency_1 = self.point_info[self.alarm_channel1]['sn_info']['hz']
        self.data2 = self.point_data[self.alarm_channel2]['vel_data']['value']
        self.frequency_2 = self.point_info[self.alarm_channel2]['sn_info']['hz']
        self.data3 = self.point_data[self.alarm_channel3]['vel_data']['value']  #
        self.frequency_3 = self.point_info[self.alarm_channel3]['sn_info']['hz']
        self.data4 = self.point_data[self.alarm_channel4]['vel_data']['value']
        self.frequency_4 = self.point_info[self.alarm_channel4]['sn_info']['hz']




        self.data1_trend = trend_data[alarm_message["风机"][0]]
        self.data2_trend = trend_data[alarm_message["风机"][1]]
        self.data3_trend = trend_data[alarm_message["风机"][2]]
        self.data4_trend = trend_data[alarm_message["风机"][3]]

        self.fs = json1["fs"]  # 采样频率
        self.rpm = json1["rpm"]["转速"]  #
        self.X_1 = self.rpm / 60  # 一倍频
        self.GMF = json1["GMF"] # 齿轮啮合频率

        self.bbf = json1["bbf"] # 轴承故障频率 ["BPFI": BPFI, "BPFO": BPFO, "BSF": BSF, "FTF": FTF]

    def bupingheng(self):
        '''不平衡故障
        "HS(水平1，一倍频幅值，1）/overall(水平1）>0.4  && speedall(水平1）>4.5||
        HS(竖直1，一倍频幅值，1）/overall(竖直1）>0.4  && speedall(竖直1）>4.5||
        HS(水平2，一倍频幅值，1）/overall(水平2）>0.4  && speedall(水平2）>4.5||
        HS(竖直2，一倍频幅值，1）/overall(竖直2）>0.4  && speedall(竖直2）>4.5"
        '''

        sign_1, sign_2, sign_3, sign_4 = 0, 0, 0, 0

        if self.data1:
            if (get_HS(self.data1, self.fs, self.X_1, 1) / get_VIB(self.data1, self.fs, self.rpm, "xampl")[
                1] > 0.4 and get_VIB(self.data1, self.fs, self.rpm, "rms") > 4.5):
                sign_1 = 1
            else:
                sign_1 = 0

        if self.data2:
            if (get_HS(self.data2, self.fs, self.X_1, 1) / get_VIB(self.data2, self.fs, self.rpm, "xampl")[
                1] > 0.4 and get_VIB(self.data2, self.fs, self.rpm, "rms") > 4.5):
                sign_2 = 1
            else:
                sign_2 = 0

        if self.data3:
            if (get_HS(self.data3, self.fs, self.X_1, 1) / get_VIB(self.data3, self.fs, self.rpm, "xampl")[
                1] > 0.4 and get_VIB(self.data3, self.fs, self.rpm, "rms") > 4.5):
                sign_3 = 1
            else:
                sign_3 = 0

        if self.data4:
            if (get_HS(self.data4, self.fs, self.X_1, 1) / get_VIB(self.data4, self.fs, self.rpm, "xampl")[
                1] > 0.4 and get_VIB(self.data4, self.fs, self.rpm, "rms") > 4.5):
                sign_4 = 1
            else:
                sign_4 = 0

        sign = sign_1 + sign_2 + sign_3 + sign_4
        if sign:
            return dict(故障模式=str(conclusion_return.iloc[12]["故障模式"]),
                        机理现象=str(conclusion_return.iloc[12]["机理现象"]),
                        机理原因=str(conclusion_return.iloc[12]["机理原因"]))
        else:
            return "转子平衡"

    def zhuanzibuduizhong(self):
        '''不对中故障
        "HS(水平1，二倍频幅值，1）/overall(水平1）>0.4  && speedall(水平1）>4.5||
        HS(竖直1，二倍频幅值，1）/overall(竖直1）>0.4  && speedall(竖直1）>4.5||
        HS(水平2，二倍频幅值，1）/overall(水平2）>0.4  && speedall(水平2）>4.5||
        HS(竖直2，二倍频幅值，1）/overall(竖直2）>0.4  && speedall(竖直2）>4.5"

        '''
        sign_1, sign_2, sign_3, sign_4 = 0, 0, 0, 0

        if self.data1:
            if (get_HS(self.data1, self.fs, self.X_1*2, 1) / get_VIB(self.data1, self.fs, self.rpm, "xampl")[
                1] > 0.4 and get_VIB(self.data1, self.fs, self.rpm, "rms") > 4.5):
                sign_1 = 1
            else:
                sign_1 = 0

        if self.data2:
            if (get_HS(self.data2, self.fs, self.X_1*2, 1) / get_VIB(self.data2, self.fs, self.rpm, "xampl")[
                1] > 0.4 and get_VIB(self.data2, self.fs, self.rpm, "rms") > 4.5):
                sign_2 = 1
            else:
                sign_2 = 0

        if self.data3:
            if (get_HS(self.data3, self.fs, self.X_1*2, 1) / get_VIB(self.data3, self.fs, self.rpm, "xampl")[
                1] > 0.4 and get_VIB(self.data3, self.fs, self.rpm, "rms") > 4.5):
                sign_3 = 1
            else:
                sign_3 = 0

        if self.data4:
            if (get_HS(self.data4, self.fs, self.X_1*2, 1) / get_VIB(self.data4, self.fs, self.rpm, "xampl")[
                1] > 0.4 and get_VIB(self.data4, self.fs, self.rpm, "rms") > 4.5):
                sign_4 = 1
            else:
                sign_4 = 0

        sign = sign_1 + sign_2 + sign_3 + sign_4
        if sign:
            return dict(故障模式=str(conclusion_return.iloc[12]["故障模式"]),
                        机理现象=str(conclusion_return.iloc[12]["机理现象"]),
                        机理原因=str(conclusion_return.iloc[12]["机理原因"]))
        else:
            return "转子对中"

    def youmowodong(self):
        '''油膜涡动
        "HS(水平，0.41X-0.48X，5）/overall(水平）>0.4 && speedall(水平）>4.5 ||
        HS(竖直，0.41X-0.48X，5）/overall(竖直）>0.4 && speedall(竖直）>4.5"

        '''
        sign_1, sign_2 = 0, 0
        if self.data1:
            if (get_HS(self.data1, self.fs, self.X_1*0.45, 5) / get_VIB(self.data1, self.fs, self.rpm, "xampl")[1] > 0.4) and get_VIB(self.data1, self.fs, self.rpm, "rms") > 4.5 :  # 分频的计算方式可以再优化
                sign_1 = 1
            else:
                sign_1 = 0

        if self.data2:
            if (get_HS(self.data2, self.fs, self.X_1*0.45, 5) / get_VIB(self.data2, self.fs, self.rpm, "xampl")[1] > 0.4) and get_VIB(self.data2, self.fs, self.rpm, "rms") > 4.5 :  # 分频的计算方式可以再优化
                sign_2 = 1
            else:
                sign_2 = 0

        sign =  sign_1 + sign_2

        if sign:
            return dict(故障模式=str(conclusion_return.iloc[17]["故障模式"]),
                        机理现象=str(conclusion_return.iloc[17]["机理现象"]),
                        机理原因=str(conclusion_return.iloc[17]["机理原因"]))
        else:
            return "没有油膜涡动"

    def zhouwaduizhongbuliang(self):  # 7 轴瓦对中不良
        sign_1, sign_2, sign_3, sign_4 = 0, 0, 0, 0
        if self.data1:
            if (get_VIB(self.data1, self.fs, self.rpm, "xampl")[1] / get_VIB(self.data1, self.fs, self.rpm, "xampl")[0] >= 1.0 ):
                sign_1 = 1
            else:
                sign_1 = 0

        if self.data2:
            if (get_VIB(self.data2, self.fs, self.rpm, "xampl")[1] / get_VIB(self.data2, self.fs, self.rpm, "xampl")[0] >= 1.0 ):
                sign_2 = 1
            else:
                sign_2 = 0

        if self.data3:
            if (get_VIB(self.data3, self.fs, self.rpm, "xampl")[1] / get_VIB(self.data3, self.fs, self.rpm, "xampl")[0] >= 1.0 ):
                sign_3 = 1
            else:
                sign_3 = 0

        if self.data4:
            if (get_VIB(self.data4, self.fs, self.rpm, "xampl")[1] / get_VIB(self.data4, self.fs, self.rpm, "xampl")[0] >= 1.0 ):
                sign_4 = 1
            else:
                sign_4 = 0
        sign = sign_1 + sign_2 + sign_3 + sign_4
        if sign:
            return dict(故障模式=str(conclusion_return.iloc[4]["故障模式"]),
                        机理现象=str(conclusion_return.iloc[4]["机理现象"]),
                        机理原因=str(conclusion_return.iloc[4]["机理原因"]))
        else:
            return "轴瓦对中正常"



def devide_diagnosis():  ##总体检测函数

    # 传入文件
    alarm_message = {}
    # 报警信息：alarm_message
    # {"电机": ["电机自由侧X", "电机负荷侧"]
    #  "风机": ["风机自由侧", "风机负荷侧"]
    #  }
    json1 = {}
    trend_data = {}

    if alarm_message.key.isin(['电机']):
        diag = Bilengji_Dianji(json1, alarm_message, trend_data)

        diag.dingziyichang()  # 1,电机定子异常故障
        diag.qixipianxin()  # 2, 电机气隙动态偏心
        diag.zhuanzitongtiaoduanlie()  # 3 电机转子铜条断裂
        diag.zhuanzibupingheng()  # 5 转子不平衡
        diag.zhouwaduizhongbuliang()  # 7 轴瓦对中不良
        diag.zhuanzibujiansongdong()  # 10 转子部件松动
        diag.zhouchengguzhang() # 轴承故障

    if alarm_message.key.isin(['篦冷风机']):
        diag = Bilengji_Fengji(json1, alarm_message, trend_data)
        diag.bupingheng()  # 5 不平衡
        diag.bupingheng()  # 不对中
        diag.zhouchengguzhang() #轴承故障

    if alarm_message.key.isin(['风机']):
        diag = Fengji(json1, alarm_message, trend_data)
        diag.bupingheng()  # 5 不平衡
        diag.bupingheng()  # 不对中
        diag.youmowodong() # 油膜涡动
        diag.zhouwaduizhongbuliang() # 轴瓦对中不良

    if alarm_message.key.isin(['齿轮箱']):
        diag = Gearbox(json1, alarm_message, trend_data)
        diag.cilunbupingheng()  # 齿轮不平衡
        diag.cilunbutongzhou() # 齿轮不平衡
        diag.chimianmoshun()  # 齿面磨损
        diag.zhouchengguzhang()  # 轴承故障
















