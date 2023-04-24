# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
from feature_function import *
from read_dat import *

def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi('PyCharm')
    filepath = r"F:\Aaxiaowei\项目\应力波项目\厚德实验数据\赵克钦采集数据\变速轴承内外圈复合故障1600n\停机1.dat"
    Raw_Data = read_dat(filepath)
    channel_ID = list(Raw_Data.keys())
    sampling_frequency = Raw_Data["50294D208019011"]['sampling_frequency']
    signal_data = Raw_Data["50294D208019011"]['signal_data']
    feature = VibFeatures(signal_data, sampling_frequency, rpm=None, featureName='rms')

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
