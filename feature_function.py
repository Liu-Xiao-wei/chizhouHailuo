# -*- coding: utf-8 -*-
# @Time    : 2023/04/07
# @Author  : liuxiaowei

import time
import math
from scipy.fftpack import fft, fftshift, fftfreq, ifft, hilbert, ifftshift
import numpy as np
import pandas as pd
from scipy.signal import get_window, butter, filtfilt, lfilter, butter, sosfilt, hilbert, get_window
from scipy.interpolate import make_interp_spline

# from feature_extraction import add_windows, freq_select  # 对应函数已经从feature_extraction中提出


class Features:
    vel_rms = None  # 速度有效值
    acc_rms = None  # 加速度有效值
    acc_peak = None  # 加速度峰值
    impulse = None  # 冲击值
    x_half1 = None  # 0.5倍频
    x_half3 = None  # 1.5倍频
    x_half5 = None  # 2.5倍频
    x_half7 = None  # 3.5倍频
    x_half9 = None  # 4.5倍频
    x_half11 = None  # 5.5倍频
    x_1 = None  # 1倍频
    x_2 = None  # 2倍频
    x_3 = None  # 3倍频
    x_4 = None  # 4倍频
    x_5 = None  # 5倍频


def add_windows(signal, window='hann'):
    """

    """
    signal_array = get_array(signal)
    window_len = len(signal_array)
    window_array = get_window(window, window_len)
    return window_array * signal_array

def freq_select(fft_signal, sampling_frequency, freq_ratio):
    fft_signal_len = len(fft_signal)
    fftshift_signal = fftshift(fft_signal)
    freq = fftfreq(fft_signal_len, 1 / sampling_frequency)
    fftshift_freq = fftshift(freq)
    low_cutoff_frequency = sampling_frequency / freq_ratio[1]
    high_cutoff_frequency = sampling_frequency / freq_ratio[0]
    # 频率选择的下限为10HZ,上限为1000HZ。即如果采样频率/信号频率小于10HZ，则将频率下限设置为10HZ。
    low_cutoff_frequency = max(low_cutoff_frequency, 10)
    high_cutoff_frequency = min(high_cutoff_frequency, 4000)
    fftshift_freq_index = [low_cutoff_frequency >= abs(f) for f in fftshift_freq]
    fftshift_signal[fftshift_freq_index] = complex(0.0, 0.0)
    return fftshift_signal

def trend_change(data):
    order = 1
    index = [i for i in range(1, len(data) + 1)]
    coeffs = np.polyfit(index, list(data), order)
    slope = coeffs[-2]
    if float(slope) >= 0.3:
        return True
    else:
        return False


def amplitude(signal, sampleFrequency, frequency):
    """
    根据输入的频率，计算频率对应的幅值
    :param signal:输入的信号
    :param sampleFrequency：采样频率
    :param frequency: 输入的频率
    :return: 输出频率对应的幅值
    """
    x_axis, y_axis = fft_spectrum(signal, sampleFrequency)
    ratio = x_axis[1]-x_axis[0]
    if frequency-ratio >= 0:
        value = max(y_axis[int(frequency-ratio):int(frequency+1+ratio)])
    else:
        value = max(y_axis[0:int(frequency+ratio)])
    return value


# def get_HCR(signal, sampleFrequency, center_frequency, sideband_frequency, order, num=5):
#     """
#     计算选定振动测点特征能量比;边带频率和中心频率的比值
#
#     :param signal:振动测点输入信号
#     :param sampleFrequency: 采样频率
#     :param center_frequency:   float:测点-特征名称（中心频率）
#     :param sideband_frequency: float:测点-特征名称（边带频率）
#     :param order:  int:阶次
#     :param num:int:边带选择个数
#     :return:特征能量比（Harmonic center ratio）
#     """
#
#     value1 = 0  # 分子
#     value2 = 0  # 分母
#     for i in range(order):
#         for j in range(num):
#             value3 = math.sqrt(sum(amplitude(signal, sampleFrequency, center_frequency-j*sideband_frequency)**2 + \
#                           amplitude(signal, sampleFrequency,center_frequency+j*sideband_frequency)**2))
#             value1 += value3
#
#         value4 = math.sqrt(amplitude(signal, sampleFrequency,center_frequency)**2)
#         value2 += value4
#     return value1/value2

def get_HCR(signal, sampleFrequency, center_frequency, sideband_frequency, order):
    '''
    :param signal:振动测点输入信号
    :param sampleFrequency: 采样频率
    :param center_frequency:   float:测点-特征名称（中心频率）
    :param sideband_frequency: float:测点-特征名称（边带频率）
    :param order:  int:阶次
    :param num:int:边带选择个数
    :return:特征能量比（Harmonic center ratio）
    '''

    T2 = amplitude(signal, sampleFrequency, center_frequency)
    T3 = amplitude(signal, sampleFrequency, sideband_frequency)

    den = [(Z * T2) ** 2 for Z in range(1, order + 1)]
    den_sum = np.sqrt(np.sum(den))
    b = []
    for Z in range(1, order + 1):
        a = [(Z * T2 - n * T3) ** 2 + (Z * T2 + n * T3) ** 2 for n in range(1, 6)]
        b.append(np.sqrt(np.sum(a)))

    return np.sum(b) / den_sum

def get_HS(signal, sampleFrequency, x_frequency, order):
    """
    计算倍频能量和，频率及对应阶次，如x_frequency=50Hz,order=3;则计算50Hz,100Hz,150Hz对应的频率幅值
    :param signal:
    :param sampleFrequency: 采样频率
    :param X_frequency:需要计算的频率
    :param order: 频率对应的阶次
    :return:所有频率和
    """
    frequency_amplitude_list = []
    for i in range(order):
        value = amplitude(signal, sampleFrequency, (i+1)*x_frequency)
        frequency_amplitude_list.append(value)
    return np.sqrt(np.sum(frequency_amplitude_list))


def get_HCS(signal, sampleFrequency, center_frequency, sideband_frequency, order, num=5):
    """

    :param signal: 振动测点输入信号
    :param sampleFrequency: 采样频率
    :param center_frequency: float:测点-特征名称（中心频率）
    :param sideband_frequency: float:测点-特征名称（边带频率）
    :param order: int:阶次
    :param num: 边带选择个数
    :return: 能量和
    """

    value1 = 0  # +号左边
    value2 = 0  # +号右边
    for i in range(order):
        for j in range(num):
            value3 = math.sqrt(sum(amplitude(center_frequency-j*sideband_frequency)**2 + \
                          amplitude(center_frequency+j*sideband_frequency)**2))
            value1 += value3

        value4 = math.sqrt(amplitude(center_frequency)**2)
        value2 += value4
    return value1+value2


def get_HDS(signal, fraction_frequency, order):
    """
    计算分数倍频能量和，一般为0.5,1.5,2.5,3.5,...
    :param signal: 波形信号
    :param fraction_frequency: 分数倍频
    :param order:
    :return: 分数倍频和
    """
    value_list = []
    for i in range(order):
        value_list.append(amplitude(fraction_frequency + i))
    return 0.707*np.sqrt(np.sum([x**2 for x in value_list]))


def get_HRS(signal, sampleFrequency, frequency_low, frequency_high):
    """
    根据给出的频率范围，计算频带能量和
    :param signal:波形信号
    :param frequency_low:频带下限
    :param frequency_high:频带上限
    :return:频带能量和
    """

    x_axis, y_axis = fft_spectrum(signal, sampleFrequency)
    # x_axis = []  # FFT后横坐标，频率
    # y_axis = []  # FFT后纵坐标，幅值
    ratio = x_axis[1] - x_axis[0]
    t1 = frequency_low / ratio
    t2 = frequency_high / ratio
    return np.sqrt(np.sum([x**2 for x in y_axis[t1, t2]]))


def Numaverage(data_trend: list) -> float:
    """
    计算一段数据的平均值
    :param data: 数据列表
    return float
    """
    return float(np.mean(data_trend))


def detrend(signal, deg=2):
    """
    计算一段数据的趋势
    :param signal: 数据列表
    :param deg:
    :return:
    """
    signal_array = get_array(signal)
    x_signal = np.arange(len(signal_array))
    fun = np.polyfit(x_signal, signal_array, deg)
    polyfit_signal = np.polyval(fun, x_signal)
    return signal_array - polyfit_signal




# =========================================================================================================
# 包络谱分析
def envelope_spectrum(signal_series, fs):
    """
    实现时序包络分析普
    :param signal_series: 采样的时序数据
    :param fs: 采样的频率
    :return: 包络谱的频率 x_frequency 和幅值 y_amplitude (仅仅是大于零的频率)
    """
    len_signal = len(signal_series)  # 计算采样数据的长度
    hy = hilbert_envelop(signal_series)  # 计算信号的包络
    hy -= np.mean(hy)
    # x_frequency = np.array([(i + 1) * fs / data_len for i in range(int(data_len / 2))])  # 计算频率
    # y_amplitude = y_amplitude[len(x_frequency) + 1:]  # 偏移 因为FFT后为对称的双边谱，因此只取一半
    y_dual_amplitude = abs(fftshift(fft(hy))) * 2 / len_signal  # 计算幅值
    x_dual_freq = fftshift(fftfreq(len_signal, 1 / fs))  # 计算频率
    x_freq = x_dual_freq[x_dual_freq >= 0]
    y_amplitude = y_dual_amplitude[x_dual_freq >= 0]
    assert len(x_freq) == len(y_amplitude)
    # 让x_frequency和y_amplitude的维度一样
    # if len(y_amplitude) > len(x_frequency):
    #     length = len(y_amplitude) - len(x_frequency)
    #     y_amplitude = y_amplitude[length:]
    # elif len(y_amplitude) < len(x_frequency):
    #     length = len(x_frequency) - len(y_amplitude)
    #     x_frequency = x_frequency[length:]
    return x_freq, y_amplitude



def filter_wave(x: np.ndarray, order: int, wn: int or list, type: str, fs: float, output: str = 'sos'):
    """
    振动信号过滤,实现高通，低通，旁通等功能。
    :param x: np.ndarray
    :param order: int,阶次
    :param wn: int or list, if type is lowpass or highpass,the value is int,otherwise the value is list 截止频率
    ,top and bottom limit
    :param type:str,lowpass,highpass,bandpass, bandstop
    :param fs:float, frequence
    :param output:str,three types: ba,sos,zpk
    :return:np.array,过滤的信号
    """
    sos = butter(order, wn, type, False, fs=fs, output=output)
    return sosfilt(sos, x)


def iomega(signal, dt, out_type, in_type=3, windows=None, pro_s=1, freq_ratio=[10, 1000], return_type='signal'):
    """
    加速度信号进来，做积分变成速度信号
    signal=列表
    dt=1/fs(fs（采样频率）加速度信号长度)
    out_type=2(1-位移，2-速度，3-加速度，4-冲击)
    pro_s=1(默认1s)
    """
    if in_type not in [1, 2, 3, 4]:
        raise ValueError('Value for datain_type must be a 1, 2 or 3')
    if out_type not in [1, 2, 3, 4]:
        raise ValueError('Value for dataout_type must be 1, 2 or 3')
    if return_type not in ['signal', 'feature', 'both']:
        raise ValueError('return_type must be signal, feature or both')
    fs = 1 / dt  # Sampling frequency 采样频率
    signal_array = get_array(signal)
    # 取前1s的数据加窗处理
    process_len = round(fs * pro_s)
    signal_array = signal_array[:process_len].copy()
    # signal_array = signal_array[:].copy()
    signal_len = len(signal_array)
    if windows is not None:
        signal_array = add_windows(signal_array, windows)
    detrend_signal = detrend(signal_array, 0)
    fft_size = signal_len
    iomega_array = 1j * 2 * np.pi * fftshift(fftfreq(n=fft_size, d=dt))
    iomega_exp = out_type - in_type
    if fft_size > signal_len:
        detrend_signal = np.append(detrend_signal, np.zeros(fft_size - signal_len))
    # Transform datain into frequency domain via FFT and shift output (A)
    # so that zero-frequency amplitude is in the middle of the array(instead of the beginning)
    assert fft_size == len(detrend_signal)
    fft_signal = fft(detrend_signal)
    fftshift_signal = freq_select(fft_signal, fs, freq_ratio)
    for j in range(fft_size):
        if iomega_array[j] != 0:
            fftshift_signal[j] = fftshift_signal[j] * np.power(iomega_array[j], iomega_exp)
        else:
            fftshift_signal[j] = complex(0.0, 0.0)
    # Shift new frequency-amplitude array back to MATLAB format and
    # transform back into the time d omain via the inverse FFT
    ifft_signal = ifft(fftshift(fftshift_signal))
    signal_out = ifft_signal.real
    detrend_signal_out = detrend(signal_out, 2)
    if return_type == 'signal':
        return detrend_signal_out * 1000
    fftshift_signal = fftshift(fft(detrend_signal_out))
    energy_correction_dict = {'hann': 1.63, 'blackman': 1.97, 'kaiser': 1.86, 'hamming': 1.59, 'flattop': 2.26}
    dual_signal_freq = fftshift(fftfreq(fft_size, dt))
    dual_spectrum = abs(fftshift_signal) * 2 / fft_size
    unilateral_signal_spectrum = dual_spectrum[dual_signal_freq >= 0].copy()
    rms = ((sum(unilateral_signal_spectrum ** 2) - unilateral_signal_spectrum[0] ** 2 / 2
            - unilateral_signal_spectrum[-1] ** 2 / 2) / 2) ** 0.5
    pk_pk = max(detrend_signal_out) - min(detrend_signal_out)
    if windows is not None and windows in energy_correction_dict:
        rms = rms * energy_correction_dict[windows]
    feature_rms = rms * 1000  # 加速度换算为速度，×1000 雪增红
    feature_pk_pk = pk_pk * 1000  # 加速度换算为速度 ×1000  雪增红
    if return_type == 'both':
        return detrend_signal_out, (feature_rms, feature_pk_pk)
    elif return_type == 'feature':
        return feature_rms, feature_pk_pk


def calculate_feature(data, fs=0, feature='rms'):
    data = get_array(data)

    if feature == 'rms':
        value = np.sqrt(np.mean(data ** 2))
    elif feature == 'peak':
        value = (np.max(data) - np.min(data)) / 2
    elif feature == '峰值':
        value = (max(data) - min(data)) / 2
    # elif feature == 'kurtosis':
    #     value = self._extracted_kurtosis_skew(data, 4)
    elif feature == 'impulse':
        value = np.sqrt(np.mean(data ** 2)) / 9.8 # 需要确认宁国水泥最新算法，好像是有效值计算方法

    return value


def get_array(array):
    """
    transform data to numpy.array
    """
    if isinstance(array, np.ndarray):
        if len(array.shape) == 1:
            return array
        elif len(array.shape) == 2 and (array.shape[0] == 1 or array.shape[1] == 1):
            return array.reshape(-1)
        else:
            raise TypeError("The dimension of the numpy.array must be 1 or 2")
    elif isinstance(array, (list, pd.Series)):
        array = np.array(array)
        return get_array(array)
    else:
        raise TypeError("Input must be a numpy.array, list or pandas.Series")


def hilbert_envelop(signal_series):
    """
    输入原始信号，输出包络时域信号
    """
    signal_array = get_array(signal_series)
    hx = hilbert(signal_array)  # 对信号进行希尔伯特变换。
    analytic_signal = signal_array - hx * 1j  # 进行hilbert变换后的解析信号
    return np.abs(analytic_signal)


def fft_spectrum(x: np.ndarray, fs: float):
    """
    傅里叶变换频谱
    :param x:np.ndarray 时序振动信号
    :param fs:float 采样频率
    :return:
    f:np.ndarray, 频率
    y:np.ndarray, 幅值
    """
    n = len(x)
    f = fs * np.arange(n // 2) / n
    y = abs(np.fft.fft(x))[:int(n / 2)] * 2 / n
    return f, y


def get_VIB(signal, sampleFrequency, rpm, featureName="rms"):
    """
    计算振动波形信号的特征值
    :param signal: 振动信号原始波形-加速度
    :param sampleFrequency: 信号采样频率
    :param rpm: 该通道位置处对应的转速
    :return: 特征值
    """

    signal -= np.mean(signal)

    if featureName == "acc_rms":
        # 加速度有效值
        acc_rms = calculate_feature(signal, sampleFrequency, 'rms')
        return acc_rms

    if featureName == "rms":
        # 速度有效值
        passband_acc_wave = filter_wave(signal, 128, [10, 1000], "bandpass", sampleFrequency)
        passband_wave = iomega(passband_acc_wave, dt=1 / len(passband_acc_wave), out_type=2, in_type=3,
                               freq_ratio=[10, 1000], return_type='signal')
        passband_rms = calculate_feature(passband_wave, rpm, 'rms')
        return passband_rms

    if featureName == 'impulse':
        # 冲击值
        sideband_acc_wave = filter_wave(signal, 128, [5000, 10000], "bandpass", sampleFrequency)
        impulse_wave_1 = hilbert_envelop(sideband_acc_wave)
        impulse_wave = filter_wave(signal, 128, [3, 500], "bandpass", sampleFrequency)
        impulse = calculate_feature(impulse_wave, rpm, 'impulse')

        return impulse

    if featureName == "xampl":
        # 倍频值
        return_list = []
        x_axis, y_axis = fft_spectrum(signal, sampleFrequency)
        if rpm is None:
            try:
                # 防止y_axis长度不足1000时
                max_ampl_index = y_axis[0:999].index(y_axis[0:999])  # 取0-1000Hz中的最大值
                rpm = x_axis[max_ampl_index][0] * 60  # 根据幅值中最大值索引找到频率中对应位置
            except IndexError:
                max_ampl_index = y_axis.index(y_axis)  # 取0-1000Hz中的最大值
                rpm = x_axis[max_ampl_index][0] * 60
        ratio = x_axis[1] - x_axis[0]  # 频率分辨率
        x_1 = rpm / 60
        for i in [1, 2]:
            p1 = int((i * x_1 - 1) / ratio)  # 倍频左侧1Hz
            p2 = math.ceil((i * x_1 + 1) / ratio)  # 倍频右侧1Hz
            return_list.append(np.max(y_axis[p1:p2]))  # 从y_axis[p1:p2]中取最大值

        return return_list   # return_list[0] 1倍频; return_list[1]  2倍频



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

# 时域图
def time_plot(data, unit):
    bwith = 2
    # 字体大小
    fontsize = 20
    # 刻度线大小
    x_y_ticks_size = 18
    # 图片大小l
    figsize = (10, 6)
    # 画图
    plt.figure("", figsize=figsize)
    plt.xticks(fontsize=x_y_ticks_size)
    plt.yticks(fontsize=x_y_ticks_size)
    plt.title('时域图 ' + unit, fontsize=fontsize)
    plt.xlabel('时间(s)', fontsize=fontsize)
    plt.ylabel('振幅 (um)', fontsize=fontsize)
    plt.grid(ls='--', axis="y")
    # 获取边框并设置边框粗细
    ax = plt.gca()
    ax.spines['bottom'].set_linewidth(bwith)
    ax.spines['left'].set_linewidth(bwith)
    ax.spines['top'].set_linewidth(bwith)
    ax.spines['right'].set_linewidth(bwith)
    plt.plot(list(range(1, len(data) + 1)), data)
    figfile = BytesIO()
    plt.savefig(figfile, format='png', dpi=400)
    figfile.seek(0)  # rewind to beginning of file
    figdata_png = base64.b64encode(figfile.getvalue())
    img_str = str(figdata_png, "utf-8")
    plt.close()
    return figfile

# 频域图
def frequency_plot(data, unit, fs):
    x_axis, y_axis = fft_spectrum(data, fs)
    bwith = 2
    # 字体大小
    fontsize = 20
    # 刻度线大小
    x_y_ticks_size = 18
    # 图片大小l
    figsize = (10, 6)
    # 画图
    plt.figure("", figsize=figsize)
    plt.xticks(fontsize=x_y_ticks_size)
    plt.yticks(fontsize=x_y_ticks_size)
    plt.title('频域图 ' + unit, fontsize=fontsize)
    plt.xlabel('频率(Hz)', fontsize=fontsize)
    plt.ylabel('振幅 (um)', fontsize=fontsize)
    plt.grid(ls='--', axis="y")
    # 获取边框并设置边框粗细
    ax = plt.gca()
    ax.spines['bottom'].set_linewidth(bwith)
    ax.spines['left'].set_linewidth(bwith)
    ax.spines['top'].set_linewidth(bwith)
    ax.spines['right'].set_linewidth(bwith)
    plt.plot(x_axis, y_axis)
    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)  # rewind to beginning of file
    figdata_png = base64.b64encode(figfile.getvalue())
    img_str = str(figdata_png, "utf-8")
    plt.close()
    return figfile

# 包络图
def envelop_plot(data, unit, fs):
    x_axis, y_axis = envelope_spectrum(data, fs)
    fontsize = 10
    # plt.subplot(3, 1, 2)
    plt.plot(x_axis, y_axis, linewidth=0.5)
    plt.xticks(())  # fontsize=x_y_ticks_size
    plt.yticks()
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False
    plt.title('包络图 ' + unit, fontsize=fontsize)
    plt.grid(ls='--', axis="y")
    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)  # rewind to beginning of file
    figdata_png = base64.b64encode(figfile.getvalue())
    img_str = str(figdata_png, "utf-8")
    plt.close()
    return img_str

#===========================================#










