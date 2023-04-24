import time
import time
from scipy.fftpack import fft, fftshift, fftfreq, ifft, hilbert, ifftshift
import numpy as np
import pandas as pd
from scipy.signal import get_window, butter, filtfilt, lfilter, butter, sosfilt, hilbert, get_window
from scipy.interpolate import make_interp_spline


class Extraction:
    def __init__(self, rawdata):
        self.wave_data = rawdata - np.mean(rawdata)
        print('data length:', len(self.wave_data))

    def feature_extraction(self):
        feature_return = Features()
        waves_return = Wave()
        raw_return = Raw()
        raw_return.raw_wave = list(self.wave_data)

        # 通频速度有效值（10-1000HZ）
        passband_acc_wave = filter_wave(self.wave_data, 128, [10,1000], "bandpass", len(self.wave_data))
        passband_wave = iomega(passband_acc_wave, dt=1 / len(passband_acc_wave), out_type=2, in_type=3,
                               freq_ratio=[10, 1000], return_type='signal')         # 增加频域积分上下截至频率，雪增红
        passband_rms = self.calculate_feature(passband_wave, 'rms')
        feature_return.passband_rms = passband_rms

        # 低频速度有效值（3-1000HZ）, 速度峰值(3-1000HZ)
        lowband_acc_wave = filter_wave(self.wave_data, 128, [3, 1000], "bandpass", len(self.wave_data))
        lowband_wave = iomega(lowband_acc_wave, dt=1 / len(lowband_acc_wave), out_type=2, in_type=3,
                               freq_ratio=[3, 1000],return_type='signal')           # 增加频域积分上下截至频率，雪增红
        lowband_rms = self.calculate_feature(lowband_wave, 'rms')
        lowband_peak = self.calculate_feature(lowband_wave, 'peak')
        feature_return.lowband_rms = lowband_rms
        feature_return.lowband_peak = lowband_peak
        waves_return.velocity_wave = list(lowband_wave)

        # 加速度有效值（3-10K HZ）, 加速度峰值（3-10K HZ）, 加速度峭度（3-10K HZ）, 加速度歪度（3-10K HZ）
        try:
            acc_wave = filter_wave(self.wave_data, 128, [3, 10000], "bandpass", len(self.wave_data))
        except Exception:
            acc_wave = filter_wave(self.wave_data, 128, [3, 10000], "bandpass", len(self.wave_data))   # 修改成[3,10000],雪增红
        acc_rms = self.calculate_feature(acc_wave, 'rms')
        acc_peak = self.calculate_feature(acc_wave, 'peak')
        acc_kurtosis = self.calculate_feature(acc_wave, 'kurtosis')
        acc_skew = self.calculate_feature(acc_wave, 'skew')
        feature_return.acc_rms = acc_rms
        feature_return.acc_peak = acc_peak
        feature_return.acc_kurtosis = acc_kurtosis
        feature_return.acc_skew = acc_skew
        waves_return.acc_wave = list(acc_wave)

        # 振动冲击值（10K-40K HZ）---> 5K-10K
        sideband_acc_wave = filter_wave(self.wave_data, 128, [5000, 10000], "bandpass", len(self.wave_data))
        impulse_wave_1 = hilbert_envelop(sideband_acc_wave)
        impulse_wave = filter_wave(impulse_wave_1, 128, 1000, "lowpass", len(impulse_wave_1))    # 需确认宁国最近更新的算法，应该是低通1000Hz，雪增红
        # SUM x(t)dt
        impluse = self.calculate_feature(impulse_wave_1, 'impulse', fs=len(impulse_wave_1))      # 记得好像是有效值计算方法，雪增红
        feature_return.impluse = impluse/9.8                                    # 10修改为9.8，雪增红
        waves_return.sideband_acc_wave = list(impulse_wave)

        # 时间
        time_now = int(time.time())
        feature_return.time = time_now
        waves_return.time = time_now
        raw_return.time = time_now

        return feature_return, waves_return, raw_return

    def calculate_feature(self, data, feature='rms', fs=None):
        data = get_array(data)
        if feature == 'rms':
            value = np.sqrt(np.mean(data ** 2))
        elif feature == 'peak':
            value = (np.max(data) - np.min(data)) / 2
        elif feature == 'kurtosis':
            value = self._extracted_kurtosis_skew(data, 4)
        elif feature == 'impulse':
            value = np.sqrt(np.mean(data ** 2))                    # 需要确认宁国水泥最新算法，好像是有效值计算方法
        elif feature == 'skew':
            value = self._extracted_kurtosis_skew(data, 3)
        return value

    def _extracted_kurtosis_skew(self, data, arg1):
        drop_mean_data = data - np.mean(data)
        rms = np.sqrt(np.mean(data ** 2))
        return np.mean(drop_mean_data**arg1) / rms**arg1


class Features:
    passband_rms = None # 通频速度有效值
    lowband_rms = None # 低频速度有效值
    lowband_peak = None # 速度峰值
    acc_rms = None # 加速度有效值
    acc_peak = None # 加速度峰值
    acc_kurtosis = None # 加速度峭度指标
    acc_skew = None # 加速度歪度指标
    impluse = None # 振动冲击值
    time = None # 时间戳
    channelId = None # 通道ID

class Raw:
    raw_wave = None # 原始波形
    time = None
    channelId = None

class Wave:
    acc_wave = None # 加速度波形（3-10K HZ带通滤波后的加速度波形）
    velocity_wave = None # 速度波形（3-1000HZ带通滤波、频域积分后的速度波形）
    sideband_acc_wave = None # 加速度波形（10K HZ高通滤波后的加速度波形）
    time = None
    channelId = None


class ReturnFeature:
    raw_wave = None
    passband_rms = None
    lowband_rms = None
    lownband_peak = None
    acc_rms = None
    acc_peak = None
    acc_kurtosis = None
    acc_skew = None
    impluse = None
    acc_wave = None
    velocity_wave = None
    sideband_acc_wave = None
    time = None
    channelId = None


def hilbert_envelop(signal_series):
    """
    输入原始信号，输出包络时域信号
    """
    signal_array = get_array(signal_series)
    hx = hilbert(signal_array)  # 对信号进行希尔伯特变换。
    analytic_signal = signal_array - hx * 1j  # 进行hilbert变换后的解析信号
    return np.abs(analytic_signal)


class RawData:
    SensorEngineeringUnit = None
    channelId = None
    dataNodeGatewayNo = None
    dataNodeNo = None
    number = None
    waveData = None


def filter_wave(x: np.ndarray, order: int, wn: int or list, type: str, fs: float, output: str = 'sos'):
    """
    振动信号过滤,实现高通，低通，旁通等功能。
    :param x: np.ndarray
    :param order: int,阶次
    :param wn: int or list, if type is lowpass or highpass,the value is int,otherwise the value is list 截止频率
    ,top and bottom limit
    :param type:str,lowpass,highpass,bandpass,bandstop
    :param fs:float,frequence
    :param output:str,three types: ba,sos,zpk
    :return:np.array,过滤的信号
    """
    sos = butter(order, wn, type, False, fs=fs, output=output)
    return sosfilt(sos, x)


class ButterworthFiltering:
    """
    调用Scipy.signal.butter中的Butterworth滤波器,属于无限冲激响应（IIR）滤波器
    Calling Butterworth filter in Scipy. signal. butter belongs to
    Infinite Impulse Response (IIR) filter
    """

    def __init__(self, order=4, sampling_frequency=25600):
        self.order = order  # 滤波器的阶数
        self.sampling_frequency = sampling_frequency  # 采样频率

    def low_filtering(self, cutoff_frequency, series):
        """
        Low pass filter
        :param cutoff_frequency: 信号的截止频率
        :param series: 要过滤的目标信号
        :return: 低通滤波过滤之后的信号
        """
        wn = 2 * cutoff_frequency / self.sampling_frequency
        array = get_array(series)
        b, a = butter(self.order, wn, btype="lowpass", output="ba")
        return filtfilt(b, a, array)

    def high_filtering(self, cutoff_frequency, series):
        """
        High pass filter
        :param cutoff_frequency: 信号的截止频率
        :param series: 要过滤的目标信号
        :return: 高通滤波过滤之后的信号
        """
        wn = 2 * cutoff_frequency / self.sampling_frequency
        array = get_array(series)
        b, a = butter(self.order, wn, btype="highpass", output="ba")
        return filtfilt(b, a, array)

    def band_filtering(self, lowcut, highcut, series):
        """
        Bandpass filtering
        :param lowcut:信号截止频率下限
        :param highcut:信号截止频率上限
        :param series:要过滤的目标信号
        :return:带通滤波过滤之后的信号
        """
        if lowcut is not None and lowcut > 0 and lowcut < self.sampling_frequency / 2:
            low = lowcut
        else:
            low = self.sampling_frequency / 2 - 1.1
        if highcut is not None and highcut < self.sampling_frequency / 2:
            high = highcut
        else:
            high = self.sampling_frequency / 2 - 0.9
        low = 2 * low / self.sampling_frequency
        high = 2 * high / self.sampling_frequency
        array = get_array(series)
        b, a = butter(self.order, [low, high], btype="bandpass", output="ba")
        return filtfilt(b, a, array, irlen=self.sampling_frequency / 2)


def detrend(signal, deg=2):
    """

    """
    signal_array = get_array(signal)
    x_signal = np.arange(len(signal_array))
    fun = np.polyfit(x_signal, signal_array, deg)
    polyfit_signal = np.polyval(fun, x_signal)
    return signal_array - polyfit_signal


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


def fft_spectrum1(x: np.ndarray, fs: float):
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
    y = abs(np.fft.fft(x))[:int(n / 2)] *2/ n                 # 归一化处理，双边频谱反转上去需×2，已经验证通过，具体找雪增红探讨
    return f, y




def acc2dis(data: np.ndarray, fs: float):
    """
    采用时域积分的方式，将振动加速度信号转化为速度信号和位移信号
    Parameters
    ----------
    data: np.ndarray, 振动加速度信号
    fs: float, 采样频率

    Return
    ------
    s_ifft: np.ndarray, 积分速度信号
    d_ifft：np.ndarray, 积分位移信号
    """
    n = len(data)
    a_mul_dt = data / fs

    s = []
    total = a_mul_dt[0]
    for i in range(n - 1):
        total = total + a_mul_dt[i + 1]
        s.append(total)
    s_fft = np.fft.fft(s)
    s_fft[:2] = 0  # 去除直流分量
    s_fft[-3:] = 0  # 去除直流分量
    s_ifft = np.real(np.fft.ifft(s_fft))

    s_mut_dt = s_ifft / fs
    d = []
    total = s_mut_dt[0]
    for i in range(n - 2):
        total = total + s_mut_dt[i + 1]
        d.append(total)
    d_fft = np.fft.fft(d)
    d_fft[:2] = 0
    d_fft[-3:] = 0
    d_ifft = np.real(np.fft.ifft(d_fft))
    return s_ifft * 1000, d_ifft * 1000000  # 单位转换


def iomega(signal, dt, out_type, in_type=3, windows=None, pro_s=1, freq_ratio=[10,1000], return_type='signal'):
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
    feature_rms = rms*1000                 # 加速度换算为速度，×1000 雪增红
    feature_pk_pk = pk_pk*1000             # 加速度换算为速度 ×1000  雪增红
    if return_type == 'both':
        return detrend_signal_out, (feature_rms, feature_pk_pk)
    elif return_type == 'feature':
        return feature_rms, feature_pk_pk


def calculate_peak_mean_kurtosis(data):
    data = get_array(data)
    data_abs = np.abs(data)
    peak = (np.max(data) - np.min(data)) / 2
    mean = np.mean(data_abs)
    N = len(data)
    variance = np.sum(np.multiply(data, data)) / (N - 1)
    kurtosis = np.mean(data ** 4) / (variance ** 2)
    return {'peak': peak,
            'mean': mean,
            'kurtosis': kurtosis}


class Iomega:
    def __init__(self, signal, fs, out_type, in_type=3, windows=None, pro_s=1, freq_cutoff=[None, None],
                 return_type='signal'):
        """
            IOMEGA is a MATLAB script for converting displacement, velocity, or
            acceleration time-series to either displacement, velocity, or
            acceleration times-series. The script takes an array of waveform data
            (datain), transforms into the frequency-domain in order to more easily
            convert into desired output form, and then converts back into the time
            domain resulting in output (dataout) that is converted into the desired form.
            :param signal: ndarray,list,or pd.Series
                input waveform data of type datain_type
            :param fs: int
                    Sampling frequency
            :param out_type: int 1 、2 or 3
                    1 – Displacement
                    2 – Velocity
                    3 – Acceleration
                    4 – Shock
            :param in_type: int 1 、2 or 3. Default 3 acceleration signal
                    1 – Displacement
                    2 – Velocity
                    3 – Acceleration
                    4 – Shock
            :param windows: string, float, or tuple
                The type of window to create. See scipy.signal.get_window for more details.
            :param pro_s: int
                处理的信号长度，默认是1s
            :param freq_cutoff: list or tuple ,eg[4, 2000]
                积分截止频率
            :param return_type: str
                'signal' 'feature' or 'both'
                if return_type is 'signal', return the waveform of the signal specified by out_type;
                if return_type is 'feature', returns the signal eigenvalue specified by out_type;
                if return_type is 'both', returns a tuple with two elements,
                the first element being the waveform of the signal, which type is ndarray
                and the second element being the eigenvalue of the signal
            :return:

            """
        self.signal = signal
        self.fs = fs
        self.out_type = out_type
        self.in_type = in_type
        self.windows = windows
        self.pro_s = pro_s
        self.freq_cutoff = freq_cutoff
        self.return_type = return_type

    def iomega(self):
        if self.in_type not in [1, 2, 3]:
            raise ValueError('Value for datain_type must be a 1, 2 or 3')
        if self.out_type not in [1, 2, 3]:
            raise ValueError('Value for dataout_type must be 1, 2 or 3')
        if self.return_type not in ['signal', 'feature', 'both']:
            raise ValueError('return_type must be signal, feature or both')
        # 输入的信号类型转换
        signal_array = get_array(self.signal)
        signal_len = len(signal_array)
        if self.windows is not None:
            signal_array = add_windows(signal_array, self.windows)
        detrend_signal = self.detrend(signal_array, 0)  # 去直流
        fft_size = signal_len
        dt = 1 / self.fs  # dt为采样周期，表示采集样本点之间的时间间隔
        bilateral_freq = fftshift(fftfreq(n=fft_size, d=dt))
        iomega_array = 1j * 2 * np.pi * bilateral_freq
        iomega_exp = self.out_type - self.in_type
        # Pad datain array with zeros (if needed)
        if fft_size > signal_len:
            detrend_signal = np.append(detrend_signal, np.zeros(fft_size - signal_len))
        # Transform datain into frequency domain via FFT and shift output (A)
        # so that zero-frequency amplitude is in the middle of the array(instead of the beginning)
        assert fft_size == len(detrend_signal)
        fft_signal = fftshift(fft(detrend_signal))
        fftshift_signal = self.freq_select(fft_signal, self.fs, self.freq_cutoff)
        for j in range(fft_size):
            if iomega_array[j] != 0:
                fftshift_signal[j] = fftshift_signal[j] * np.power(iomega_array[j], iomega_exp)
            else:
                fftshift_signal[j] = complex(0.0, 0.0)
        ifft_signal = ifft(ifftshift(fftshift_signal))
        signal_out = ifft_signal.real
        detrend_signal_out = self.detrend(signal_out, 2)
        if self.return_type == 'signal':
            return detrend_signal_out * 1000
        features = calculate_peak_mean_kurtosis(detrend_signal_out)
        features['peak'] = features['peak'] * 1000
        features['mean'] = features['mean'] * 1000
        return features

    def detrend(self, signal, deg=2):
        """
          利用numpy.polyfit接口 最小二乘多项式拟合，去除信号中的趋势项
          :param signal: ndarray,list,or pd.Series
                  Prepare to remove the trend signal
          :param deg: int
                  Degree of the fitting polynomial.
                  If you want to remove the DC component of the removed signal, set deg to 0
          :return: array_like
                  Detrended signal
          """
        signal_array = get_array(signal)
        x_signal = np.arange(len(signal_array))
        fun = np.polyfit(x_signal, signal_array, deg)
        polyfit_signal = np.polyval(fun, x_signal)
        return signal_array - polyfit_signal

    def freq_select(self, analysis_signal, sampling_frequency, freq_cutoff):
        """
        输入经过要分析的信号，将频率比范围内的信号频率加以保留，范围之外的信号频率用0补齐
        :param analysis_signal: ndarray
                经过FFT后的信号
        :param sampling_frequency: int
                信号的采样频率
        :param freq_cutoff: list or tuple   eg：[10, 4000]
                积分截止频率
        :return: ndarray
                输出经过fftshift之后的与输入等长的序列，将频率比范围内的信号频率加以保留，范围之外的信号频率用0补齐
        """
        low_cutoff_frequency = freq_cutoff[0] if freq_cutoff[0] is not None else 0
        high_cutoff_frequency = np.inf if freq_cutoff[1] is None else freq_cutoff[1]
        fft_signal_len = len(analysis_signal)
        fftshift_signal = analysis_signal
        fftshift_freq = fftshift(fftfreq(fft_signal_len, 1 / sampling_frequency))
        fftshift_freq_index = [
            not low_cutoff_frequency < abs(f) < high_cutoff_frequency
            for f in fftshift_freq
        ]
        fftshift_signal[fftshift_freq_index] = complex(0.0, 0.0)
        return fftshift_signal


def add_windows(signal, window='hann'):
    """

    """
    signal_array = get_array(signal)
    window_len = len(signal_array)
    window_array = get_window(window, window_len)
    return window_array * signal_array


def get_array(array):
    """transform data to numpy.array
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
