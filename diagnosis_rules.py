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
 'HS_1X': []  HS(水平1，1倍频，5)
 'HDS_1X': [] HDS(水平1，1倍频，5）
 
 ...
}
#################################################
报警信息：alarm_message
{"电机":["电机自由侧X", "电机负荷侧"]
 "风机":["风机自由侧", "风机负荷侧"]
}


"""""
from feature_function import *

# 计分函数
def calculate_weight_score_3_v2(a1, a2, a3, x):
    """
    a1:下限值
    a2:上限值
    a3:报警值
    return:
        weight,score
    """
    print('-----', a1, a2, a3, x)

    b = 1 / 4 * a1 + 3 / 4 * a2
    try:
        if x < b:
            w = 1
            score = 90
        elif b <= x < a2:
            w = math.exp(((x - b) / b) ** 2)
            k = (80 - 90) / (a2 - b)
            score = 90 - abs(k * (x - b))
        elif a2 <= x < a3:
            w = math.exp(((x - b) / b) ** 2 + ((x - a2) / a2) ** 2)
            k = (60 - 80) / (a3 - a2)
            score = 80 - abs(k * (x - a2))
        else:  # x>a3 报警值
            print('dd')
            w = math.exp(((x - b) / b) ** 2 + ((x - a2) / a2) ** 2 + ((x - a3) / a3) ** 2)
            k = (60 - 80) / (a3 - a2)
            score = 80 - abs(k * (x - a2))
            if score > 0:
                score = score
            else:
                score = 0
    except:
        x = a3
        w = math.exp(((x - b) / b) ** 2 + ((x - a2) / a2) ** 2 + ((x - a3) / a3) ** 2)
        k = (60 - 80) / (a3 - a2)
        score = 80 - abs(k * (x - a2))
        if score > 0:
            score = score
        else:
            score = 0
    return round(w, 2), round(score, 2)


# 篦冷风机
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

        self.fs = json1["fs"]  # 采样频率
        self.rpm = json1["rpm"]["转速"]  #
        self.X_1 = self.rpm / 60  # 一倍频


    def diagnosis_rule(self):
        """
        :return: diagnosis_result, maintenance_advice
                正常值上限       注意      告警      备注
        不平衡     0.6           0.7     0.8       一倍频与acc_rms的比值
        不对中     0.3           0.6      1        二倍频与一倍频比值
        轴承故障    0.8           2       3         冲击平均值大小
        """
        # 故障模式列表
        result_list = ['不平衡', '不对中', '轴承故障']
        # 故障原因
        reason_list = ['1、制造误差、装配误差、材料不均匀等；2、转子不均匀结垢、不均匀磨损、不均匀腐蚀等；2、转子零部件脱落、叶轮流道有异物等。',
                       '1、初始联轴器安装对中不良；2、安装对中不良、地基沉降或轴承支撑部件热膨胀不均匀；3、负重、自重作用、摩擦等使转轴弯曲。',
                       '1、磨损擦伤、点蚀、疲劳剥落；2、润滑油脂乳化、结块、含有杂质等引起的理化指标下降；3、轴承处于贫油状态等。']
        # 维修列表
        maintenance_list = ['调整动平衡，做现场单面或双面动平衡，严重时拆检检修。',
                            '1、检查电机与泵联轴器对中偏差情况；2、检查电机或泵两端的轴心安装同心度；3、检查地基有无沉降现象；4、通过信号特征甄别转轴是否（热）弯曲。',
                            '检查润滑油理化情况，选择更滑润滑油，严重时更换轴承']

        # 不平衡
        try:
            sign_1, sign_2, sign_3, sign_4 = 0, 0, 0, 0


            data1_vib_rate = get_VIB(self.data1, self.fs, self.rpm, "xampl")[0] / get_VIB(self.data1, self.fs, self.rpm, "acc_rms")
            data2_vib_rate = get_VIB(self.data2, self.fs, self.rpm, "xampl")[0] / get_VIB(self.data2, self.fs, self.rpm, "acc_rms")
            data3_vib_rate = get_VIB(self.data3, self.fs, self.rpm, "xampl")[0] / get_VIB(self.data3, self.fs, self.rpm, "acc_rms")
            data4_vib_rate = get_VIB(self.data4, self.fs, self.rpm, "xampl")[0] / get_VIB(self.data4, self.fs, self.rpm, "acc_rms")

            if self.data1:
                if data1_vib_rate >= 0.4 or Numaverage(self.data1_trend["1倍频"]) >= 0.8:
                    sign_1 = 1
                else:
                    sign_1 = 0

            if self.data2:
                if data2_vib_rate >= 0.4 or Numaverage(self.data2_trend["1倍频"]) >= 0.8:
                    sign_2 = 1
                else:
                    sign_2 = 0

            if self.data3:
                if data3_vib_rate >= 0.4 or Numaverage(self.data3_trend["1倍频"]) >= 0.8:
                    sign_3 = 1
                else:
                    sign_3 = 0

            if self.data4:
                if data4_vib_rate >= 0.4 or Numaverage(self.data4_trend["1倍频"]) >= 0.8:
                    sign_4 = 1
                else:
                    sign_4 = 0

            sign = sign_1 + sign_2 + sign_3 + sign_4

            if sign:
                max_vib_rate = max(data1_vib_rate, data2_vib_rate, data3_vib_rate, data4_vib_rate)
                imbalance_w, imbalance_score = calculate_weight_score_3_v2(0.6, 0.7, 0.8, max_vib_rate)  # 阈值如何确定
            else:
                imbalance_w, imbalance_score = 1, 88

        except:
            imbalance_w, imbalance_score = 1, 88

        # 不对中
        try:
            '''不对中故障
            "HS(水平1，二倍频幅值，1）/overall(水平1）>0.4  && speedall(水平1）>4.5||
            HS(竖直1，二倍频幅值，1）/overall(竖直1）>0.4  && speedall(竖直1）>4.5||
            HS(水平2，二倍频幅值，1）/overall(水平2）>0.4  && speedall(水平2）>4.5||
            HS(竖直2，二倍频幅值，1）/overall(竖直2）>0.4  && speedall(竖直2）>4.5"
            '''
            sign_1, sign_2, sign_3, sign_4 = 0, 0, 0, 0
            data1_misalignment_rate = get_HS(self.data1, self.fs, self.X_1 * 2, 1) / get_VIB(self.data1, self.fs, self.rpm, "xampl")[1]
            data2_misalignment_rate = get_HS(self.data2, self.fs, self.X_1 * 2, 1) / get_VIB(self.data2, self.fs, self.rpm, "xampl")[1]
            data3_misalignment_rate = get_HS(self.data3, self.fs, self.X_1 * 2, 1) / get_VIB(self.data3, self.fs, self.rpm, "xampl")[1]
            data4_misalignment_rate = get_HS(self.data4, self.fs, self.X_1 * 2, 1) / get_VIB(self.data4, self.fs, self.rpm, "xampl")[1]

            sign_1, sign_2, sign_3, sign_4 = 0, 0, 0, 0

            if self.data1:
                if data1_misalignment_rate > 0.4 and get_VIB(self.data1, self.fs, self.rpm, "rms") > 4.5:
                    sign_1 = 1
                else:
                    sign_1 = 0

            if self.data2:
                if data2_misalignment_rate > 0.4 and get_VIB(self.data2, self.fs, self.rpm, "rms") > 4.5:
                    sign_2 = 1
                else:
                    sign_2 = 0

            if self.data3:
                if data3_misalignment_rate > 0.4 and get_VIB(self.data3, self.fs, self.rpm, "rms") > 4.5:
                    sign_3 = 1
                else:
                    sign_3 = 0

            if self.data4:
                if data4_misalignment_rate > 0.4 and get_VIB(self.data4, self.fs, self.rpm, "rms") > 4.5:
                    sign_4 = 1
                else:
                    sign_4 = 0

            sign = sign_1 + sign_2 + sign_3 + sign_4

            if sign:
                max_vib_rate = max(data1_misalignment_rate, data2_misalignment_rate, data3_misalignment_rate,
                                   data4_misalignment_rate)
                misalignment_w, misalignment_score = calculate_weight_score_3_v2(0.6, 0.7, 0.8, max_vib_rate)  # 阈值如何确定
            else:
                misalignment_w, misalignment_score = 1, 88

        except:
            misalignment_w, misalignment_score = 1, 88

        # 轴承故障
        try:
            data1_impulse = get_VIB(self.data1, self.fs, self.rpm, "impulse")
            data2_impulse = get_VIB(self.data2, self.fs, self.rpm, "impulse")
            impulse_mean = np.mean([data1_impulse, data2_impulse])
            if impulse_mean > 2:
                bearing_w, bearing_score = calculate_weight_score_3_v2(0.8, 2, 3, impulse_mean)
            else:
                bearing_w, bearing_score = 1, 88

        except:
            bearing_w, bearing_score = 1, 88

        rate_list = [imbalance_score, misalignment_score, bearing_score]
        weight_list = [imbalance_w, misalignment_w, bearing_w]
        return_index = rate_list.index(min(rate_list))
        diagnosis_weight = weight_list[return_index]
        diagnosis_score = min(rate_list)

        if diagnosis_score >= 80:
            diagnosis_level = '健康'
        elif diagnosis_score >= 60:
            diagnosis_level = '注意'
        else:
            diagnosis_level = '警告'

        if diagnosis_score < 60:
            maintenance_advice = maintenance_list[return_index]
            reason_result = reason_list[return_index]
            diagnosis_result = result_list[return_index]

        else:
            maintenance_advice = ''
            reason_result = ''
            diagnosis_result = '健康'

        # return imbalance_w, imbalance_score, misalignment_w, misalignment_score, bearing_w, bearing_score, diagnosis_result, reason_result, maintenance_advice, diagnosis_level, diagnosis_score, diagnosis_weight
        result = [{"diagnosis_level": diagnosis_level, "diagnosis_result": diagnosis_result,
                   "diagnosis_weight": diagnosis_weight, "diagnosis_score": diagnosis_score,
                   "reason_result": reason_result, "maintenance_advice": maintenance_advice}]
        return result

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

        # self.bbf = json1["bbf"] # 轴承故障频率 ["BPFI": BPFI, "BPFO": BPFO, "BSF": BSF, "FTF": FTF]

    def diagnosis_rule(self):  #
        """
        :param axmpl: 1xAmpl--10xAmpl
        :return: diagnosis_result, maintenance_advice
                正常值上限       注意      告警      备注
        不平衡     0.6           0.7     0.8       一倍频与acc_rms的比值
        不对中     0.3           0.6      1        二倍频与一倍频比值
        轴承故障    0.8           2       3         冲击平均值大小
        """
        # 故障模式列表
        result_list = ['不平衡', '不对中', '轴承故障']
        # 故障原因
        reason_list = [
            '1、制造误差、装配误差、材料不均匀等；2、转子不均匀结垢、不均匀磨损、不均匀腐蚀等；2、转子零部件脱落、叶轮流道有异物等。',
            '1、初始联轴器安装对中不良；2、安装对中不良、地基沉降或轴承支撑部件热膨胀不均匀；3、负重、自重作用、摩擦等使转轴弯曲。',
            '1、磨损擦伤、点蚀、疲劳剥落；2、润滑油脂乳化、结块、含有杂质等引起的理化指标下降；3、轴承处于贫油状态等。']
        # 维修列表
        maintenance_list = ['调整动平衡，做现场单面或双面动平衡，严重时拆检检修。',
                            '1、检查电机与泵联轴器对中偏差情况；2、检查电机或泵两端的轴心安装同心度；3、检查地基有无沉降现象；4、通过信号特征甄别转轴是否（热）弯曲。',
                            '检查润滑油理化情况，选择更滑润滑油，严重时更换轴承']

        # 不平衡
        '''不平衡故障
         "HS(水平1，一倍频幅值，1）/overall(水平1）>0.4  && speedall(水平1）>4.5||
         HS(竖直1，一倍频幅值，1）/overall(竖直1）>0.4  && speedall(竖直1）>4.5||
         HS(水平2，一倍频幅值，1）/overall(水平2）>0.4  && speedall(水平2）>4.5||
         HS(竖直2，一倍频幅值，1）/overall(竖直2）>0.4  && speedall(竖直2）>4.5"
         '''
        try:
            sign_1, sign_2, sign_3, sign_4 = 0, 0, 0, 0
            data1_hs_rate = get_HS(self.data1, self.fs, self.X_1, 1) / get_VIB(self.data1, self.fs, self.rpm, "xampl")[1]
            data2_hs_rate = get_HS(self.data2, self.fs, self.X_1, 1) / get_VIB(self.data2, self.fs, self.rpm, "xampl")[
                1]
            data3_hs_rate = get_HS(self.data3, self.fs, self.X_1, 1) / get_VIB(self.data3, self.fs, self.rpm, "xampl")[
                1]
            data4_hs_rate = get_HS(self.data4, self.fs, self.X_1, 1) / get_VIB(self.data4, self.fs, self.rpm, "xampl")[
                1]

            if self.data1:
                if data1_hs_rate > 0.4 and get_VIB(self.data1, self.fs, self.rpm, "rms") > 4.5:
                    sign_1 = 1
                else:
                    sign_1 = 0

            if self.data2:
                if data2_hs_rate > 0.4 and get_VIB(self.data2, self.fs, self.rpm, "rms") > 4.5:
                    sign_2 = 1
                else:
                    sign_2 = 0

            if self.data3:
                if data3_hs_rate > 0.4 and get_VIB(self.data3, self.fs, self.rpm, "rms") > 4.5:
                    sign_3 = 1
                else:
                    sign_3 = 0

            if self.data4:
                if data4_hs_rate > 0.4 and get_VIB(self.data4, self.fs, self.rpm, "rms") > 4.5:
                    sign_4 = 1
                else:
                    sign_4 = 0

            sign = sign_1 + sign_2 + sign_3 + sign_4

            if sign:
                max_vib_rate = max(data1_hs_rate, data2_hs_rate, data3_hs_rate, data4_hs_rate)
                imbalance_w, imbalance_score = calculate_weight_score_3_v2(0.6, 0.7, 0.8, max_vib_rate)  # 阈值如何确定
            else:
                imbalance_w, imbalance_score = 1, 88

        except:
            imbalance_w, imbalance_score = 1, 88

        # 不对中
        try:
            '''不对中故障
            "HS(水平1，二倍频幅值，1）/overall(水平1）>0.4  && speedall(水平1）>4.5||
            HS(竖直1，二倍频幅值，1）/overall(竖直1）>0.4  && speedall(竖直1）>4.5||
            HS(水平2，二倍频幅值，1）/overall(水平2）>0.4  && speedall(水平2）>4.5||
            HS(竖直2，二倍频幅值，1）/overall(竖直2）>0.4  && speedall(竖直2）>4.5"
            '''
            data1_misalignment_rate = get_HS(self.data1, self.fs, self.X_1 * 2, 1) / \
                                      get_VIB(self.data1, self.fs, self.rpm, "xampl")[1]
            data2_misalignment_rate = get_HS(self.data2, self.fs, self.X_1 * 2, 1) / \
                                      get_VIB(self.data2, self.fs, self.rpm, "xampl")[1]
            data3_misalignment_rate = get_HS(self.data3, self.fs, self.X_1 * 2, 1) / \
                                      get_VIB(self.data3, self.fs, self.rpm, "xampl")[1]
            data4_misalignment_rate = get_HS(self.data4, self.fs, self.X_1 * 2, 1) / \
                                      get_VIB(self.data4, self.fs, self.rpm, "xampl")[1]

            sign_1, sign_2, sign_3, sign_4 = 0, 0, 0, 0

            if self.data1:
                if data1_misalignment_rate > 0.4 and get_VIB(self.data1, self.fs, self.rpm, "rms") > 4.5:
                    sign_1 = 1
                else:
                    sign_1 = 0

            if self.data2:
                if data2_misalignment_rate > 0.4 and get_VIB(self.data2, self.fs, self.rpm, "rms") > 4.5:
                    sign_2 = 1
                else:
                    sign_2 = 0

            if self.data3:
                if data3_misalignment_rate > 0.4 and get_VIB(self.data3, self.fs, self.rpm, "rms") > 4.5:
                    sign_3 = 1
                else:
                    sign_3 = 0

            if self.data4:
                if data4_misalignment_rate > 0.4 and get_VIB(self.data4, self.fs, self.rpm, "rms") > 4.5:
                    sign_4 = 1
                else:
                    sign_4 = 0

            sign = sign_1 + sign_2 + sign_3 + sign_4

            if sign:
                max_vib_rate = max(data1_misalignment_rate, data2_misalignment_rate, data3_misalignment_rate,
                                   data4_misalignment_rate)
                misalignment_w, misalignment_score = calculate_weight_score_3_v2(0.6, 0.7, 0.8, max_vib_rate)  # 阈值如何确定
            else:
                misalignment_w, misalignment_score = 1, 88

        except:
            misalignment_w, misalignment_score = 1, 88

        # 轴承故障
        try:
            data1_impulse = get_VIB(self.data1, self.fs, self.rpm, "impulse")
            data2_impulse = get_VIB(self.data2, self.fs, self.rpm, "impulse")
            impulse_mean = np.mean([data1_impulse, data2_impulse])
            if impulse_mean > 2:
                bearing_w, bearing_score = calculate_weight_score_3_v2(0.8, 2, 3, impulse_mean)
            else:
                bearing_w, bearing_score = 1, 88

        except:
            bearing_w, bearing_score = 1, 88

        rate_list = [imbalance_score, misalignment_score, bearing_score]
        weight_list = [imbalance_w, misalignment_w, bearing_w]
        return_index = rate_list.index(min(rate_list))
        diagnosis_weight = weight_list[return_index]
        diagnosis_score = min(rate_list)

        if diagnosis_score >= 80:
            diagnosis_level = '健康'
        elif diagnosis_score >= 60:
            diagnosis_level = '注意'
        else:
            diagnosis_level = '警告'

        if diagnosis_score < 60:
            maintenance_advice = maintenance_list[return_index]
            reason_result = reason_list[return_index]
            diagnosis_result = result_list[return_index]

        else:
            maintenance_advice = ''
            reason_result = ''
            diagnosis_result = '健康'

        # return imbalance_w, imbalance_score, misalignment_w, misalignment_score, bearing_w, bearing_score, diagnosis_result, reason_result, maintenance_advice, diagnosis_level, diagnosis_score, diagnosis_weight
        result = [{"diagnosis_level": diagnosis_level, "diagnosis_result": diagnosis_result,
                   "diagnosis_weight": diagnosis_weight, "diagnosis_score": diagnosis_score,
                   "reason_result": reason_result, "maintenance_advice": maintenance_advice}]
        return result


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


    def diagnosis_rule(self):
        """
        :param axmpl: 1xAmpl--10xAmpl
        :return: diagnosis_result, maintenance_advice
                    正常值上限       注意      告警      备注
        齿轮不平衡     0.6           0.7     0.8       get_HS(self.data1, self.fs, self.X_1, 5) / get_VIB(self.data1, self.fs, self.rpm, "xampl")[1]
        齿轮不同轴     0.3           0.6      1        HCR(水平，1X，GMF，5)
        齿面磨损                                       get_HCR(self.data1, self.fs, self.X_1, self.GMF, 1)
        轴承故障       0.8           2       3         冲击平均值大小
        """
        # 故障模式列表
        result_list = ['齿轮不平衡', '齿轮不同轴','齿面磨损', '轴承故障']
        # 故障原因
        reason_list = [
            '装配误差造成齿轮与转轴不同轴。',
            '装配误差造成齿轮与转轴不同轴。',
            '偏工况运行、加工误差、安装偏差、润滑品质差等。',
            '1、磨损擦伤、点蚀、疲劳剥落；2、润滑油脂乳化、结块、含有杂质等引起的理化指标下降；3、轴承处于贫油状态等。']

        # 维修列表
        maintenance_list = ['严重时，建议重新装配处理。',
                            '严重时，建议重新装配处理。',
                            '严重时，建议回厂检修处理。',
                            '检查润滑油理化情况，选择更滑润滑油，严重时更换轴承']

        # 齿轮不平衡
        '''齿轮不平衡
                "HCR(水平，1X，GMF，5）>0.4  && speedall(水平1）>4.5 && HS(水平，1X，5）/overall(水平）>0.4 ||
                 HCR(水平，1X，GMF，5）>0.4  && speedall(竖直1）>4.5 &&  HS(竖直，1X，5）/overall(竖直）>0.4 "
                '''
        try:
            sign_1, sign_2 = 0, 0
            data1_imbalance_rate = get_HS(self.data1, self.fs, self.X_1, 5) / get_VIB(self.data1, self.fs, self.rpm, "xampl")[1]
            data2_imbalance_rate = get_HS(self.data2, self.fs, self.X_1, 5) / get_VIB(self.data2, self.fs, self.rpm, "xampl")[1]


            if self.data1:
                if data1_imbalance_rate > 0.4 and get_VIB(self.data1, self.fs, self.rpm, "rms") > 4.5 and get_HCR(self.data1, self.fs,
                                                                                                 self.X_1, self.GMF,
                                                                                                 5) >= 0.4:
                    sign_1 = 1
                else:
                    sign_1 = 0

            if self.data2:
                if data2_imbalance_rate > 0.4 and get_VIB(self.data2, self.fs, self.rpm, "rms") > 4.5 and get_HCR(self.data2, self.fs,
                                                                                                 self.X_1, self.GMF,
                                                                                                 5) >= 0.4:
                    sign_2 = 1
                else:
                    sign_2 = 0

            max_imbalance_rate = max(data1_imbalance_rate, data2_imbalance_rate)
            sign = sign_1 + sign_2
            if sign:
                imbalance_w, imbalance_score = calculate_weight_score_3_v2(0.8, 2, 3, max_imbalance_rate)  # 阈值需要确定
            else:
                imbalance_w,imbalance_score = 1, 88

        except:
            imbalance_w, imbalance_score = 1, 88

        # 齿轮不同轴
        '''齿轮不同轴
                "HCR(水平，1X，GMF，5) >0.4  && speedall(水平1）>4.5 && HS(水平，1X，5）/overall(水平）>0.4 ||
                HCR(竖直，1X，GMF，5) >0.4  && speedall(竖直1）>4.5 &&  HS(竖直，1X，5）/overall(竖直）>0.4 "
                '''
        try:
            sign_1, sign_2 = 0, 0
            data1_axes_rate = get_HCR(self.data1, self.fs, self.X_1, self.GMF, 5)
            data2_axes_rate = get_HCR(self.data2, self.fs, self.X_1, self.GMF, 5)

            if self.data1:
                if data1_axes_rate > 0.4 and get_VIB(self.data1, self.fs, self.rpm,"rms") > 4.5 and get_HS(self.data1, self.fs,self.X_1,5) / get_VIB(self.data1, self.fs, self.rpm, "xampl")[1] > 0.4:
                    sign_1 = 1
                else:
                    sign_1 = 0

            if self.data2:
                if data2_axes_rate >= 0.4 and get_VIB(self.data2, self.fs, self.rpm,
                                                                                          "rms") > 4.5 and get_HS(
                        self.data2, self.fs, self.X_1, 5) / get_VIB(self.data2, self.fs, self.rpm, "xampl")[1] > 0.4:
                    sign_2 = 1
                else:
                    sign_2 = 0

            max_axes_rate = max(data1_axes_rate, data2_axes_rate)
            sign = sign_1 + sign_2
            if sign:
                difaxes_w, difaxes_score = calculate_weight_score_3_v2(0.8, 2, 3, max_axes_rate)  # 阈值需要确定
            else:
                difaxes_w, difaxes_score = 1, 88

        except:
            difaxes_w, difaxes_score = 1, 88


        # 齿面磨损
        '''齿面磨损
        "HS(水平，1X，5）/overall(水平）>0.4 && speedall(水平）>4.5 && HCR(水平，1X，GMF，1）>0.4 ||
        HS(竖直，1X，5）/overall(竖直）>0.4 && speedall(竖直）>4.5 &&  HCR(竖直，1X，GMF，1）>0.4 "
        '''
        try:
            sign_1, sign_2 = 0, 0
            data1_wear_rate = get_HCR(self.data1, self.fs, self.X_1, self.GMF, 1)
            data2_wear_rate = get_HCR(self.data2, self.fs, self.X_1, self.GMF, 1)
            if self.data1:
                if data1_wear_rate > 0.4 and get_VIB(self.data1, self.fs, self.rpm,
                                                                                         "rms") > 4.5 and get_HS(
                    self.data1,
                    self.fs,
                    self.X_1, 5) / \
                        get_VIB(self.data1, self.fs, self.rpm, "xampl")[1] > 0.4:
                    sign_1 = 1
                else:
                    sign_1 = 0

            if self.data2:
                if data2_wear_rate >= 0.4 and get_VIB(self.data2, self.fs, self.rpm,
                                                                                          "rms") > 4.5 and get_HS(
                    self.data2,
                    self.fs,
                    self.X_1, 5) / \
                        get_VIB(self.data2, self.fs, self.rpm, "xampl")[1] > 0.4:
                    sign_2 = 1
                else:
                    sign_2 = 0

            max_wear_rate = max(data1_wear_rate, data2_wear_rate)
            sign = sign_1 + sign_2
            if sign:
                wear_w, wear_score = calculate_weight_score_3_v2(0.8, 2, 3, max_wear_rate)  # 阈值需要确定
            else:
                wear_w, wear_score = 1, 88

        except:
            wear_w, wear_score = 1, 88

        # 轴承故障
        try:
            data1_impulse = get_VIB(self.data1, self.fs, self.rpm, "impulse")
            data2_impulse = get_VIB(self.data2, self.fs, self.rpm, "impulse")
            impulse_mean = np.mean([data1_impulse, data2_impulse])
            if impulse_mean > 2:
                bearing_w, bearing_score = calculate_weight_score_3_v2(0.8, 2, 3, impulse_mean)
            else:
                bearing_w, bearing_score = 1, 88

        except:
            bearing_w, bearing_score = 1, 88

        rate_list = [imbalance_score, difaxes_score, wear_score, bearing_score]
        weight_list = [imbalance_w, difaxes_w, wear_w, bearing_w]
        return_index = rate_list.index(min(rate_list))
        diagnosis_weight = weight_list[return_index]
        diagnosis_score = min(rate_list)

        if diagnosis_score >= 80:
            diagnosis_level = '健康'
        elif diagnosis_score >= 60:
            diagnosis_level = '注意'
        else:
            diagnosis_level = '警告'

        if diagnosis_score < 60:
            maintenance_advice = maintenance_list[return_index]
            reason_result = reason_list[return_index]
            diagnosis_result = result_list[return_index]

        else:
            maintenance_advice = ''
            reason_result = ''
            diagnosis_result = '健康'

        # return imbalance_w, imbalance_score, wear_w, wear_score, bearing_w, bearing_score, diagnosis_result, reason_result, maintenance_advice, diagnosis_level, diagnosis_score, diagnosis_weight
        result = [{"diagnosis_level": diagnosis_level, "diagnosis_result": diagnosis_result,
                   "diagnosis_weight": diagnosis_weight, "diagnosis_score": diagnosis_score,
                   "reason_result": reason_result, "maintenance_advice": maintenance_advice}]
        return result




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

    def diagnosis_rule(self):
        """
        :param axmpl: 1xAmpl--10xAmpl
        :return: diagnosis_result, maintenance_advice
                正常值上限       注意      告警      备注
        不平衡     0.6           0.7     0.8       get_HS(self.data1, self.fs, self.X_1, 1) / get_VIB(self.data1, self.fs, self.rpm, "xampl")[1]
        不对中     0.3           0.6      1        get_HS(self.data1, self.fs, self.X_1 * 2, 1) / get_VIB(self.data1, self.fs, self.rpm, "xampl")[1]
        油膜涡动    0.8           2       3         get_HS(self.data1, self.fs, self.X_1*0.45, 5) / get_VIB(self.data1, self.fs, self.rpm, "xampl")[1]
        轴瓦不对中                                  get_VIB(self.data1, self.fs, self.rpm, "xampl")[1] / get_VIB(self.data1, self.fs, self.rpm, "xampl")[0]
        """
        # 故障模式列表
        result_list = ['不平衡', '不对中', '油膜涡动', '轴瓦不对中']

        # 故障原因
        reason_list = [
            '1、制造误差、装配误差、材料不均匀等；2、转子不均匀结垢、不均匀磨损、不均匀腐蚀等；2、转子零部件脱落、叶轮流道有异物等。',
            '1、初始联轴器安装对中不良；2、安装对中不良、地基沉降或轴承支撑部件热膨胀不均匀；3、负重、自重作用、摩擦等使转轴弯曲。',
            '滑动轴瓦严重磨损或油膜间隙过大，转子偏离其转动中心，致使油膜合力与载荷不能平衡。',
            '1、电机和泵端轴瓦中心同心度不良。2、地基沉降或轴瓦支撑部件热膨胀不均匀；3、转子动静摩擦或受其他载荷使转轴弯曲。']

        # 维修列表
        maintenance_list = ['调整动平衡，做现场单面或双面动平衡，严重时拆检检修。',
                            '1、检查电机与泵联轴器对中偏差情况；2、检查电机或泵两端的轴心安装同心度；3、检查地基有无沉降现象；4、通过信号特征甄别转轴是否（热）弯曲。',
                            '减小轴承间隙、降低供油压力、适当调整润滑油温、降低润滑油粘度。',
                            '1、检查电机或泵两端的轴心安装同心度；3、检查地基有无沉降现象；4、通过信号特征甄别转轴是否（热）弯曲。']


        # 不平衡
        '''不平衡故障
         "HS(水平1，一倍频幅值，1）/overall(水平1）>0.4  && speedall(水平1）>4.5||
         HS(竖直1，一倍频幅值，1）/overall(竖直1）>0.4  && speedall(竖直1）>4.5||
         HS(水平2，一倍频幅值，1）/overall(水平2）>0.4  && speedall(水平2）>4.5||
         HS(竖直2，一倍频幅值，1）/overall(竖直2）>0.4  && speedall(竖直2）>4.5"
         '''
        try:
            sign_1, sign_2, sign_3, sign_4 = 0, 0, 0, 0
            data1_hs_rate = get_HS(self.data1, self.fs, self.X_1, 1) / get_VIB(self.data1, self.fs, self.rpm, "xampl")[
                1]
            data2_hs_rate = get_HS(self.data2, self.fs, self.X_1, 1) / get_VIB(self.data2, self.fs, self.rpm, "xampl")[
                1]
            data3_hs_rate = get_HS(self.data3, self.fs, self.X_1, 1) / get_VIB(self.data3, self.fs, self.rpm, "xampl")[
                1]
            data4_hs_rate = get_HS(self.data4, self.fs, self.X_1, 1) / get_VIB(self.data4, self.fs, self.rpm, "xampl")[
                1]

            if self.data1:
                if data1_hs_rate > 0.4 and get_VIB(self.data1, self.fs, self.rpm, "rms") > 4.5:
                    sign_1 = 1
                else:
                    sign_1 = 0

            if self.data2:
                if data2_hs_rate > 0.4 and get_VIB(self.data2, self.fs, self.rpm, "rms") > 4.5:
                    sign_2 = 1
                else:
                    sign_2 = 0

            if self.data3:
                if data3_hs_rate > 0.4 and get_VIB(self.data3, self.fs, self.rpm, "rms") > 4.5:
                    sign_3 = 1
                else:
                    sign_3 = 0

            if self.data4:
                if data4_hs_rate > 0.4 and get_VIB(self.data4, self.fs, self.rpm, "rms") > 4.5:
                    sign_4 = 1
                else:
                    sign_4 = 0

            sign = sign_1 + sign_2 + sign_3 + sign_4

            if sign:
                max_vib_rate = max(data1_hs_rate, data2_hs_rate, data3_hs_rate, data4_hs_rate)
                imbalance_w, imbalance_score = calculate_weight_score_3_v2(0.6, 0.7, 0.8, max_vib_rate)  # 阈值如何确定
            else:
                imbalance_w, imbalance_score = 1, 88

        except:
            imbalance_w, imbalance_score = 1, 88

        # 不对中
        try:
            '''不对中故障
            "HS(水平1，二倍频幅值，1）/overall(水平1）>0.4  && speedall(水平1）>4.5||
            HS(竖直1，二倍频幅值，1）/overall(竖直1）>0.4  && speedall(竖直1）>4.5||
            HS(水平2，二倍频幅值，1）/overall(水平2）>0.4  && speedall(水平2）>4.5||
            HS(竖直2，二倍频幅值，1）/overall(竖直2）>0.4  && speedall(竖直2）>4.5"
            '''
            data1_misalignment_rate = get_HS(self.data1, self.fs, self.X_1 * 2, 1) / \
                                      get_VIB(self.data1, self.fs, self.rpm, "xampl")[1]
            data2_misalignment_rate = get_HS(self.data2, self.fs, self.X_1 * 2, 1) / \
                                      get_VIB(self.data2, self.fs, self.rpm, "xampl")[1]
            data3_misalignment_rate = get_HS(self.data3, self.fs, self.X_1 * 2, 1) / \
                                      get_VIB(self.data3, self.fs, self.rpm, "xampl")[1]
            data4_misalignment_rate = get_HS(self.data4, self.fs, self.X_1 * 2, 1) / \
                                      get_VIB(self.data4, self.fs, self.rpm, "xampl")[1]

            sign_1, sign_2, sign_3, sign_4 = 0, 0, 0, 0

            if self.data1:
                if data1_misalignment_rate > 0.4 and get_VIB(self.data1, self.fs, self.rpm, "rms") > 4.5:
                    sign_1 = 1
                else:
                    sign_1 = 0

            if self.data2:
                if data2_misalignment_rate > 0.4 and get_VIB(self.data2, self.fs, self.rpm, "rms") > 4.5:
                    sign_2 = 1
                else:
                    sign_2 = 0

            if self.data3:
                if data3_misalignment_rate > 0.4 and get_VIB(self.data3, self.fs, self.rpm, "rms") > 4.5:
                    sign_3 = 1
                else:
                    sign_3 = 0

            if self.data4:
                if data4_misalignment_rate > 0.4 and get_VIB(self.data4, self.fs, self.rpm, "rms") > 4.5:
                    sign_4 = 1
                else:
                    sign_4 = 0

            sign = sign_1 + sign_2 + sign_3 + sign_4

            if sign:
                max_vib_rate = max(data1_misalignment_rate, data2_misalignment_rate, data3_misalignment_rate,
                                   data4_misalignment_rate)
                misalignment_w, misalignment_score = calculate_weight_score_3_v2(0.6, 0.7, 0.8,
                                                                                 max_vib_rate)  # 阈值如何确定
            else:
                misalignment_w, misalignment_score = 1, 88

        except:
            misalignment_w, misalignment_score = 1, 88

        # 油膜涡动
        '''油膜涡动
                "HS(水平，0.41X-0.48X，5）/overall(水平）>0.4 && speedall(水平）>4.5 ||
                HS(竖直，0.41X-0.48X，5）/overall(竖直）>0.4 && speedall(竖直）>4.5"

                '''
        try:
            sign_1, sign_2 = 0, 0

            data1_hs_rate = get_HS(self.data1, self.fs, self.X_1*0.45, 5) / get_VIB(self.data1, self.fs, self.rpm, "xampl")[1]
            data2_hs_rate = get_HS(self.data2, self.fs, self.X_1 * 0.45, 5) / \
                            get_VIB(self.data2, self.fs, self.rpm, "xampl")[1]

            if self.data1:
                if (data1_hs_rate > 0.4) and get_VIB(self.data1, self.fs, self.rpm, "rms") > 4.5 :  # 分频的计算方式可以再优化
                    sign_1 = 1
                else:
                    sign_1 = 0

            if self.data2:
                if (data2_hs_rate > 0.4) and get_VIB(self.data2, self.fs, self.rpm, "rms") > 4.5 :  # 分频的计算方式可以再优化
                    sign_2 = 1
                else:
                    sign_2 = 0

            sign =  sign_1 + sign_2

            if sign:
                max_hs_rate = max(data1_hs_rate, data2_hs_rate)
                whirl_w, whirl_score = calculate_weight_score_3_v2(0.6, 0.7, 0.8, max_hs_rate)  # 阈值如何确定
            else:
                whirl_w, whirl_score = 1, 88

        except:
            whirl_w, whirl_score = 1, 88

        # 轴瓦对中不良
        '''轴瓦对中不良
        "【VIB(水平1-2倍频）/ VIB(水平1-1倍频）＞1.0 or Numaverage（水平1-2倍频、累计100点）>0.8 】and VIB(水平1-速度总值）>4.5 or
        【VIB(竖直1-2倍频）/ VIB(竖直1-1倍频）＞1.0 or Numaverage（竖直1-2倍频、累计100点）>0.8 】and VIB(竖直1-速度总值）>4.5 or
        【VIB(水平2-2倍频）/ VIB(水平2-1倍频）＞1.0 or Numaverage（水平2-2倍频、累计100点）>0.8 】and VIB(水平2-速度总值）>4.5 or
        【VIB(竖直2-2倍频）/ VIB(竖直2-1倍频）＞1.0 or Numaverage（竖直2-2倍频、累计100点）>0.8 】and VIB(竖直2-速度总值）>4.5"

        '''
        try:
            sign_1, sign_2, sign_3, sign_4 = 0, 0, 0, 0
            data1_vib_rate = get_VIB(self.data1, self.fs, self.rpm, "xampl")[1] / get_VIB(self.data1, self.fs, self.rpm, "xampl")[0]
            data2_vib_rate = get_VIB(self.data2, self.fs, self.rpm, "xampl")[1] / \
                            get_VIB(self.data2, self.fs, self.rpm, "xampl")[0]
            data3_vib_rate = get_VIB(self.data3, self.fs, self.rpm, "xampl")[1] / \
                             get_VIB(self.data3, self.fs, self.rpm, "xampl")[0]
            data4_vib_rate = get_VIB(self.data4, self.fs, self.rpm, "xampl")[1] / \
                             get_VIB(self.data4, self.fs, self.rpm, "xampl")[0]

            if self.data1:
                if (data1_vib_rate >= 1.0 or Numaverage(self.data1_trend["2倍频"]) >= 0.8) and get_VIB(self.data1, self.fs, self.rpm, "rms"):
                    sign_1 = 1
                else:
                    sign_1 = 0

            if self.data2:
                if (data2_vib_rate >= 1.0 or Numaverage(self.data2_trend["2倍频"]) >= 0.8) and get_VIB(self.data2, self.fs, self.rpm, "rms"):
                    sign_2 = 1
                else:
                    sign_2 = 0

            if self.data3:
                if (data3_vib_rate >= 1.0 or Numaverage(self.data3_trend["2倍频"]) >= 0.8) and get_VIB(self.data3, self.fs, self.rpm, "rms"):
                    sign_3 = 1
                else:
                    sign_3 = 0

            if self.data4:
                if (data4_vib_rate >= 1.0 or Numaverage(self.data4_trend["2倍频"]) >= 0.8) and get_VIB(self.data4, self.fs, self.rpm, "rms"):
                    sign_4 = 1
                else:
                    sign_4 = 0
            sign = sign_1 + sign_2 + sign_3 + sign_4
            if sign:
                max_vib_rate = max(data1_vib_rate, data2_vib_rate, data3_vib_rate, data4_vib_rate)
                bush_w, bush_score = calculate_weight_score_3_v2(0.6, 0.7, 0.8, max_vib_rate)  # 阈值如何确定
            else:
                bush_w, bush_score = 1, 88

        except:
            bush_w, bush_score = 1, 88

        rate_list = [imbalance_score, misalignment_score, whirl_score, bush_score]
        weight_list = [imbalance_w, misalignment_w, whirl_w, bush_w]
        return_index = rate_list.index(min(rate_list))
        diagnosis_weight = weight_list[return_index]
        diagnosis_score = min(rate_list)

        if diagnosis_score >= 80:
            diagnosis_level = '健康'
        elif diagnosis_score >= 60:
            diagnosis_level = '注意'
        else:
            diagnosis_level = '警告'

        if diagnosis_score < 60:
            maintenance_advice = maintenance_list[return_index]
            reason_result = reason_list[return_index]
            diagnosis_result = result_list[return_index]

        else:
            maintenance_advice = ''
            reason_result = ''
            diagnosis_result = '健康'

        # return imbalance_w, imbalance_score, wear_w, wear_score, bearing_w, bearing_score, diagnosis_result, reason_result, maintenance_advice, diagnosis_level, diagnosis_score, diagnosis_weight
        result = [{"diagnosis_level": diagnosis_level, "diagnosis_result": diagnosis_result,
                   "diagnosis_weight": diagnosis_weight, "diagnosis_score": diagnosis_score,
                   "reason_result": reason_result, "maintenance_advice": maintenance_advice}]
        return result


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
        result = diag.diagnosis_rule()


    if alarm_message.key.isin(['篦冷风机']):
        diag = Bilengji_Fengji(json1, alarm_message, trend_data)
        result = diag.diagnosis_rule()

    if alarm_message.key.isin(['齿轮箱']):
        diag = Gearbox(json1, alarm_message, trend_data)
        result = diag.diagnosis_rule()

    if alarm_message.key.isin(['风机']):
        diag = Fengji(json1, alarm_message, trend_data)
        result = diag.diagnosis_rule()



