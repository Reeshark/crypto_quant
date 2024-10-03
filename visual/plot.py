import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
def plot_price_with_adx(df,symbol,internal, ADX_thr=20,RSI_thr=[30,70]):
    # 创建一个画布和两个子图
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 12))

    # 上部子图：绘制收盘价曲线
    ax1.set_title('%s---%s Close Price'%(symbol,internal))
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Price')

    # 初始化颜色数组
    colors = ['' for _ in df.index]
    adx_colors = ['' for _ in df.index]
    rsi_colors = ['' for _ in df.index]
    # 根据 ADX 值与阈值的比较结果设置颜色
    for i in range(len(df)):
        if df['ADX'].iloc[i] < ADX_thr and df['RSI'].iloc[i]>RSI_thr[0] and df['RSI'].iloc[i]<RSI_thr[1]: # for price colors
            colors[i] = 'red'
        else:
            colors[i] = 'green'
        if df['ADX'].iloc[i] < ADX_thr: # for adx colors
            adx_colors[i] = 'red'
        else:
            adx_colors[i] = 'green'
        if df['RSI'].iloc[i]>RSI_thr[0] and df['RSI'].iloc[i]<RSI_thr[1]: # for rsi colors
            rsi_colors[i] = 'red'
        else:
            rsi_colors[i] = 'green'

    df['colors']=colors
    # 第二个子图：绘制ADX曲线
    ax2.set_title('ADX Threshold=%d'%ADX_thr)
    ax2.set_xlabel('Time')
    ax2.set_ylabel('ADX Value')
    ax3.set_title('RSI Threshold=[%d,%d]'%(RSI_thr[0],RSI_thr[1]))
    ax3.set_xlabel('Time')
    ax3.set_ylabel('RSI Value')
    # 绘制收盘价曲线，根据颜色数组绘制
    #ax1.plot(df.index, df['close_price'], color=colors[0])  # 绘制第一条线段
    for i in range(20, len(colors)):
        ax1.plot(df.index[i-1:i+1], df['close_price'].iloc[i-1:i+1], color=colors[i])
        ax2.plot(df.index[i-1:i+1], df['ADX'].iloc[i-1:i+1], color=adx_colors[i])
        ax3.plot(df.index[i - 1:i + 1], df['RSI'].iloc[i - 1:i + 1], color=rsi_colors[i])
        ax3.plot(df.index[i - 1:i + 1], df['RSI_EMA'].iloc[i - 1:i + 1], color=rsi_colors[i])


    #ax2.plot(df.index, df['ADX'], color='orange')
    ax2.axhline(y=ADX_thr, linestyle=':', color='r')
    ax3.axhline(y=RSI_thr[0], linestyle=':', color='r')
    ax3.axhline(y=RSI_thr[1], linestyle=':', color='r')
    # 设置网格线
    ax1.grid(True)
    ax2.grid(True)

    # 显示图表
    plt.tight_layout()
    plt.show()
    return

def plot_price_and_adx(df):
    close_prices = df['close_price'].tolist()
    adx_values = df['ADX'].tolist()
    rsi_values=df['RSI'].tolist()
    # 绘制收盘价曲线
    plt.subplot(3, 1, 1)  # 2行1列的第1个子图
    plt.plot(close_prices, label='Close Price')
    plt.title('Close Price Over Time')
    plt.xlabel('Time')
    plt.ylabel('Price')
    plt.legend()

    # 绘制ADX曲线
    plt.subplot(3, 1, 2)  # 2行1列的第2个子图
    plt.plot(adx_values, label='ADX', color='orange')
    plt.title('ADX Indicator')
    plt.xlabel('Time')
    plt.ylabel('ADX Value')
    plt.legend()

    # 绘制RSI曲线
    plt.subplot(3, 1, 3)  # 2行1列的第2个子图
    plt.plot(rsi_values, label='RSI', color='green')
    plt.title('RSI Indicator')
    plt.xlabel('Time')
    plt.ylabel('RSI Value')
    plt.legend()

    # 显示图表
    plt.tight_layout()  # 调整子图布局以避免重叠
    plt.show()
    return


def get_lorentzian_points(df):
    xs_long=[]
    ys_long=[]
    xs_short = []
    ys_short = []
    for index, row in enumerate(df.iterrows()):
        if row[1]['lor_signal']==1:
            xs_long.append(row[0])
            ys_long.append(row[1]['close_price'])
        elif row[1]['lor_signal']==-1:
            xs_short.append(row[0])
            ys_short.append(row[1]['close_price'])
    return xs_long,ys_long,xs_short,ys_short

def plot_RAL(df,symbol,internal, ADX_thr=20,RSI_thr=[30,70]):
    # 创建一个画布和两个子图
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 12))

    # 上部子图：绘制收盘价曲线
    ax1.set_title('%s---%s Close Price'%(symbol,internal))
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Price')

    # 初始化颜色数组
    colors = ['' for _ in df.index]
    adx_colors = ['' for _ in df.index]
    rsi_colors = ['' for _ in df.index]
    # 根据 ADX 值与阈值的比较结果设置颜色
    for i in range(len(df)):
        if df['ADX'].iloc[i] < ADX_thr and df['RSI'].iloc[i]>RSI_thr[0] and df['RSI'].iloc[i]<RSI_thr[1]: # for price colors
            colors[i] = 'orange'
        else:
            colors[i] = 'blue'
        if df['ADX'].iloc[i] < ADX_thr: # for adx colors
            adx_colors[i] = 'orange'
        else:
            adx_colors[i] = 'blue'
        if df['RSI'].iloc[i]>RSI_thr[0] and df['RSI'].iloc[i]<RSI_thr[1]: # for rsi colors
            rsi_colors[i] = 'orange'
        else:
            rsi_colors[i] = 'blue'

    df['colors']=colors
    # 第二个子图：绘制ADX曲线
    ax2.set_title('ADX Threshold=%d'%ADX_thr)
    ax2.set_xlabel('Time')
    ax2.set_ylabel('ADX Value')
    ax3.set_title('RSI Threshold=[%d,%d]'%(RSI_thr[0],RSI_thr[1]))
    ax3.set_xlabel('Time')
    ax3.set_ylabel('RSI Value')
    # 绘制收盘价曲线，根据颜色数组绘制
    #ax1.plot(df.index, df['close_price'], color=colors[0])  # 绘制第一条线段
    for i in range(20, len(colors)):
        ax1.plot(df.index[i:i+2], df['close_price'].iloc[i:i+2], color=colors[i])
        ax2.plot(df.index[i:i+2], df['ADX'].iloc[i:i+2], color=adx_colors[i])
        ax3.plot(df.index[i:i+2], df['RSI'].iloc[i:i+2], color=rsi_colors[i])
        ax3.plot(df.index[i:i + 2], df['RSI_EMA'].iloc[i:i + 2], color='red')

    #ax2.plot(df.index, df['ADX'], color='orange')
    ax2.axhline(y=ADX_thr, linestyle=':', color='r')
    ax3.axhline(y=RSI_thr[0], linestyle=':', color='r')
    ax3.axhline(y=RSI_thr[1], linestyle=':', color='r')
    # 设置网格线
    ax1.grid(True)
    ax2.grid(True)
    ax3.grid
    # 画Lorentzian买卖信号
    xs_long, ys_long, xs_short, ys_short=get_lorentzian_points(df)
    ax1.plot(xs_long,ys_long,'o',color='green')
    ax1.plot(xs_short, ys_short, 'o', color='red')
    # 显示图表
    plt.tight_layout()
    plt.show()
    return

def plot_strategy_RAL(df,symbol,internal,mode='A', ADX_thr=20,RSI_thr=[30,70],dump_file=''):
    # 创建一个画布和两个子图
    fig, (ax2, ax1, ax3,ax4,ax5) = plt.subplots(5, 1, figsize=(36, 18))

    # 上部子图：绘制收盘价曲线
    ax1.set_title('%s---%s %s-%s Close Price'%(symbol,internal,str(df['open_time'].tolist()[0]),str(df['close_time'].tolist()[-1])))
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Price')
    # 上部子图：绘制收盘价曲线
    ax2.set_title('%s---%s Close Price'%(symbol,internal))
    ax2.set_xlabel('Time')
    ax2.set_ylabel('Price')
    # 初始化颜色数组
    colors = ['' for _ in df.index]
    trend_colors=['' for _ in df.index]
    adx_colors = ['' for _ in df.index]
    rsi_colors = ['' for _ in df.index]
    # 根据 ADX 值与阈值的比较结果设置颜色
    for i in range(len(df)):
        if mode=='A':
            if df['ADX'].iloc[i] < ADX_thr and df['RSI'].iloc[i]>RSI_thr[0] and df['RSI'].iloc[i]<RSI_thr[1]: # for price colors
                colors[i] = 'orange'
                trend_colors[i]='orange'
            else:
                if df['strategy_signal'].iloc[i] == 1:
                    colors[i] = 'green'
                elif df['strategy_signal'].iloc[i] == -1:
                    colors[i] = 'red'
                else:
                    colors[i] = 'blue'
                trend_colors[i] = 'blue'
        elif mode=='B':
            if df['strategy_signal'].iloc[i]==1:
                colors[i]='green'
            elif df['strategy_signal'].iloc[i]==-1:
                colors[i]='red'
            else:
                colors[i]='blue'
            if df['ADX'].iloc[i] < ADX_thr and df['RSI'].iloc[i] > RSI_thr[0] and df['RSI'].iloc[i] < RSI_thr[1]:
                trend_colors[i]='orange'
            else:
                trend_colors[i]='blue'
        if df['ADX'].iloc[i] < ADX_thr: # for adx colors
            adx_colors[i] = 'orange'
        else:
            adx_colors[i] = 'blue'
        if df['RSI'].iloc[i]>RSI_thr[0] and df['RSI'].iloc[i]<RSI_thr[1]: # for rsi colors
            rsi_colors[i] = 'orange'
        else:
            rsi_colors[i] = 'blue'

    df['colors']=colors
    # 第二个子图：绘制ADX曲线
    ax3.set_title('ADX Threshold=%d'%ADX_thr)
    ax3.set_xlabel('Time')
    ax3.set_ylabel('ADX Value')
    ax4.set_title('RSI Threshold=[%d,%d]'%(RSI_thr[0],RSI_thr[1]))
    ax4.set_xlabel('Time')
    ax4.set_ylabel('RSI Value')
    ax5.set_title('Final Balance=%d'%(df['balance'].values[-1]))
    ax5.set_xlabel('Time')
    ax5.set_ylabel('Balance')
    # 绘制收盘价曲线，根据颜色数组绘制
    #ax1.plot(df.index, df['close_price'], color=colors[0])  # 绘制第一条线段
    for i in range(20, len(colors)):
        # ax1.plot(df.index[i-1:i+1], df['close_price'].iloc[i-1:i+1], color=colors[i])
        # ax2.plot(df.index[i-1:i+1], df['ADX'].iloc[i-1:i+1], color=adx_colors[i])
        # ax3.plot(df.index[i-1:i+1], df['RSI'].iloc[i-1:i+1], color=rsi_colors[i])
        # ax4.plot(df.index[i-1:i + 1], df['balance'].iloc[i-1:i + 1], color='blue')
        ax1.plot(df.index[i:i+2], df['close_price'].iloc[i:i+2], color=colors[i])
        ax2.plot(df.index[i:i + 2], df['close_price'].iloc[i:i + 2], color=trend_colors[i])
        ax3.plot(df.index[i:i+2], df['ADX'].iloc[i:i+2], color=adx_colors[i])
        ax4.plot(df.index[i:i+2], df['RSI'].iloc[i:i+2], color=rsi_colors[i])
        ax4.plot(df.index[i - 1:i + 1], df['RSI_EMA2'].iloc[i - 1:i + 1], color='red')
        ax5.plot(df.index[i:i + 2], df['balance'].iloc[i:i + 2], color='blue')


    #ax2.plot(df.index, df['ADX'], color='orange')
    ax3.axhline(y=ADX_thr, linestyle=':', color='r')
    ax4.axhline(y=RSI_thr[0], linestyle=':', color='r')
    ax4.axhline(y=RSI_thr[1], linestyle=':', color='r')
    # 设置网格线
    ax1.grid(True)
    ax2.grid(True)
    ax3.grid(True)
    ax4.grid(True)
    ax5.grid(True)
    # 画Lorentzian买卖信号
    xs_long, ys_long, xs_short, ys_short=get_lorentzian_points(df)
    # ax1.plot(xs_long,ys_long,'o',color='green')
    # ax1.plot(xs_short, ys_short, 'o', color='red')
    # ax2.plot(xs_long,ys_long,'o',color='green')
    # ax2.plot(xs_short, ys_short, 'o', color='red')
    # 显示图表
    plt.tight_layout()
    if not dump_file=='' and 'pdf' in dump_file:
        plt.savefig(dump_file, format='pdf', dpi=400)
    else:
        plt.show()
    return

def plot_lorentzian_stat(stat_info,dump_file=''):
    # Fixing random state for reproducibility

    x = np.random.rand(len(stat_info))
    y = np.random.rand(len(stat_info))
    colors=[]
    for index in range(len(stat_info)):
        if stat_info['is_correct'].iloc[index]==True:
            if stat_info['lor_signal'].iloc[index]==1:
                colors.append('green')
            else:
                colors.append('red')
        else:
            if stat_info['lor_signal'].iloc[index] == 1:
                colors.append('blue')
            else:
                colors.append('orange')
    fig, axs = plt.subplots(2, 3,figsize=(18, 12))

    # Matplotlib marker symbol
    axs[0, 0].scatter(stat_info['wave_1d_h'], y, s=20, c=colors)
    axs[0, 0].set_title("wave_1d_h")

    axs[0, 1].scatter(stat_info['wave_o'], y, s=20, c=colors)
    axs[0, 1].set_title("wave_o")

    axs[0, 2].scatter(stat_info['wave_h'], y, s=20, c=colors)
    axs[0, 2].set_title("wave_h")

    axs[1, 0].scatter(stat_info['rsi'], y, s=20, c=colors)
    axs[1, 0].set_title("rsi")

    axs[1, 1].scatter(stat_info['lor_score'], y, s=20, c=colors)
    axs[1, 1].set_title("lor_score")

    # regular 5-pointed asterisk marker
    axs[1, 2].scatter(stat_info['wave_1d_h'], stat_info['rsi'], s=20, c=colors)
    axs[1, 2].set_title("wave_1d_h-rsi")

    plt.tight_layout()
    if not dump_file=='' and 'pdf' in dump_file:
        plt.savefig(dump_file, format='pdf', dpi=400)
    else:
        plt.show()
    return



def plot_three_trade(df,symbol,internals,mode='F', ADX_thr=20,RSI_thr=[30,70],dump_file=''):
    time_start=df[2]['open_time'].values[0]
    time_end=df[2]['close_time'].values[-1]
    df[0]=df[0].loc[df[0]['open_time']>=time_start]
    df[0] = df[0].loc[df[0]['close_time'] <= time_end]
    df[1]=df[1].loc[df[1]['open_time']>=time_start]
    df[1] = df[1].loc[df[1]['close_time'] <= time_end]
    # 创建一个画布和两个子图
    fig, (ax1,ax2, ax3,ax4,ax5,ax6,ax7) = plt.subplots(7, 1, figsize=(48, 48)) #width,height

    # 上部子图：绘制收盘价曲线
    ax1.set_title('%s---%s %s-%s Close Price'%(symbol,internals[0],str(df[0]['open_time'].tolist()[0]),str(df[0]['close_time'].tolist()[-1])))
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Price')
    # 上部子图：绘制收盘价曲线
    ax2.set_title('%s-%s MACD'%(symbol,internals[0]))
    ax2.set_xlabel('Time')
    ax2.set_ylabel('Price')
    # 初始化颜色数组
    df1_colors=['' for _ in df[0].index]
    macd_colors=['' for _ in df[0].index]
    for i in range(len(df[0])):
        macd1=df[0].iloc[i]['MACD_Histogram']
        lor1 = df[0].iloc[i]['signal']
        macd1_ct = df[0].iloc[i]['MACD_CT']
        pred1=df[0].iloc[i]['prediction']
        if mode=='F': #大周期MACD或n根K线趋势或lor，中周期Lor或MACD，小周期MACD金死叉或Lor:
            if (pred1>2):  # 三个周期，两种指标均是看多
                df1_colors[i] = 'green'
            elif (pred1<-2):  # 三个周期，两种指标均是看多
                df1_colors[i] = 'red'
            else:
                df1_colors[i]='blue'
            if macd1>0:
                macd_colors[i]='green'
            else:
                macd_colors[i]='red'

    for i in range(0, len(df1_colors)):
        ax1.plot(df[0].index[i:i+2], df[0]['close_price'].iloc[i:i+2], color=df1_colors[i])
        ax2.bar(df[0].index[i:i+2], df[0]['MACD_Histogram'].iloc[i:i + 2], color=macd_colors[i])


    # 上部子图：绘制收盘价曲线
    ax3.set_title('%s---%s %s-%s Close Price'%(symbol,internals[1],str(df[1]['open_time'].tolist()[0]),str(df[1]['close_time'].tolist()[-1])))
    ax3.set_xlabel('Time')
    ax3.set_ylabel('Price')
    # 上部子图：绘制收盘价曲线
    ax4.set_title('%s-%s MACD'%(symbol,internals[1]))
    ax4.set_xlabel('Time')
    ax4.set_ylabel('Price')
    # 初始化颜色数组
    df2_colors=['' for _ in df[1].index]
    macd_colors=['' for _ in df[1].index]
    for i in range(len(df[1])):
        macd2=df[1].iloc[i]['MACD_Histogram']
        lor2 = df[1].iloc[i]['signal']
        macd2_ct = df[1].iloc[i]['MACD_CT']
        if mode=='F': #大周期MACD或n根K线趋势或lor，中周期Lor或MACD，小周期MACD金死叉或Lor:
            if (macd2 > 0 ):  # 三个周期，两种指标均是看多
                df2_colors[i] = 'green'
            elif (macd2 < 0 ):  # 三个周期，两种指标均是看多
                df2_colors[i] = 'red'
            else:
                df2_colors[i]='blue'
            if macd2>0:
                macd_colors[i]='green'
            else:
                macd_colors[i]='red'

    for i in range(0, len(df2_colors)):
        ax3.plot(df[1].index[i:i+2], df[1]['close_price'].iloc[i:i+2], color=df2_colors[i])
        ax4.bar(df[1].index[i:i+2], df[1]['MACD_Histogram'].iloc[i:i + 2], color=macd_colors[i])

    # 上部子图：绘制收盘价曲线
    ax5.set_title('%s---%s %s-%s Close Price'%(symbol,internals[2],str(df[2]['open_time'].tolist()[0]),str(df[2]['close_time'].tolist()[-1])))
    ax5.set_xlabel('Time')
    ax5.set_ylabel('Price')
    # 上部子图：绘制收盘价曲线
    ax6.set_title('%s-%s MACD'%(symbol,internals[2]))
    ax6.set_xlabel('Time')
    ax6.set_ylabel('Price')
    # 初始化颜色数组
    df3_colors=['' for _ in df[2].index]
    macd_colors=['' for _ in df[2].index]
    for i in range(len(df[2])):
        macd3=df[2].iloc[i]['MACD_Histogram']
        lor3 = df[2].iloc[i]['signal']
        macd3_ct = df[2].iloc[i]['MACD_CT']
        if mode=='F': #大周期MACD或n根K线趋势或lor，中周期Lor或MACD，小周期MACD金死叉或Lor:
            if (lor3== 1):  # 三个周期，两种指标均是看多
                df3_colors[i] = 'green'
            elif (lor3 == -1):  # 三个周期，两种指标均是看多
                df3_colors[i] = 'red'
            else:
                df3_colors[i]='blue'
            if macd3>0:
                macd_colors[i]='green'
            else:
                macd_colors[i]='red'

    for i in range(0, len(df3_colors)):
        ax5.plot(df[2].index[i:i+2], df[2]['close_price'].iloc[i:i+2], color=df3_colors[i])
        ax6.bar(df[2].index[i:i+2], df[2]['MACD_Histogram'].iloc[i:i + 2], color=macd_colors[i])
        ax7.plot(df[2].index[i:i + 2], df[2]['balance'].iloc[i:i + 2], color='blue')



    # 设置网格线
    ax1.grid(True)
    ax2.grid(True)
    ax3.grid(True)
    ax4.grid(True)
    ax5.grid(True)
    ax6.grid(True)
    ax7.grid(True)
    #画Lorentzian买卖信号
    xs_long, ys_long, xs_short, ys_short=get_lorentzian_points(df[0])
    ax1.plot(xs_long,ys_long,'o',color='green')
    ax1.plot(xs_short, ys_short, 'o', color='red')
    xs_long, ys_long, xs_short, ys_short=get_lorentzian_points(df[1])
    ax3.plot(xs_long,ys_long,'o',color='green')
    ax3.plot(xs_short, ys_short, 'o', color='red')
    xs_long, ys_long, xs_short, ys_short=get_lorentzian_points(df[2])
    ax5.plot(xs_long,ys_long,'o',color='green')
    ax5.plot(xs_short, ys_short, 'o', color='red')
    # ax2.plot(xs_long,ys_long,'o',color='green')
    # ax2.plot(xs_short, ys_short, 'o', color='red')
    # 显示图表
    plt.tight_layout()
    if not dump_file=='' and 'pdf' in dump_file:
        plt.savefig(dump_file, format='pdf', dpi=400)
    else:
        plt.show()
    return

def plot_one_trade(df,symbol,internals,mode='F', ADX_thr=20,RSI_thr=[30,70],dump_file=''):
    time_start=df[2]['open_time'].values[0]
    time_end=df[2]['close_time'].values[-1]
    df[0]=df[0].loc[df[0]['open_time']>=time_start]
    df[0] = df[0].loc[df[0]['close_time'] <= time_end]
    df[1]=df[1].loc[df[1]['open_time']>=time_start]
    df[1] = df[1].loc[df[1]['close_time'] <= time_end]
    # 创建一个画布和两个子图
    fig, (ax1,ax2, ax3,ax4,ax5,ax6,ax7) = plt.subplots(7, 1, figsize=(48, 48)) #width,height

    # 上部子图：绘制收盘价曲线
    ax1.set_title('%s---%s %s-%s Close Price'%(symbol,internals[0],str(df[0]['open_time'].tolist()[0]),str(df[0]['close_time'].tolist()[-1])))
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Price')
    # 上部子图：绘制收盘价曲线
    ax2.set_title('%s-%s MACD'%(symbol,internals[0]))
    ax2.set_xlabel('Time')
    ax2.set_ylabel('Value')

    # 上部子图：绘制收盘价曲线
    ax3.set_title('%s-%s MACD_diff'%(symbol,internals[0]))
    ax3.set_xlabel('Time')
    ax3.set_ylabel('Value')

    # 上部子图：绘制收盘价曲线
    ax4.set_title('%s-%s ADX'%(symbol,internals[0]))
    ax4.set_xlabel('Time')
    ax4.set_ylabel('Value')

    ax5.set_title('%s-%s ADX_diff'%(symbol,internals[0]))
    ax5.set_xlabel('Time')
    ax5.set_ylabel('Value')
    # 初始化颜色数组
    df1_colors=['' for _ in df[0].index]
    macd_colors=['' for _ in df[0].index]
    macd_diff_colors = ['' for _ in df[0].index]
    adx_colors = ['' for _ in df[0].index]
    adx_diff_colors = ['' for _ in df[0].index]
    macd1_diff_list = []
    adx1_diff_list = []
    for i in range(len(df[0])):
        macd1=df[0].iloc[i]['MACD_Histogram']
        lor1 = df[0].iloc[i]['signal']
        macd1_ct = df[0].iloc[i]['MACD_CT']
        pred1=df[0].iloc[i]['prediction']
        adx=df[0].iloc[i]['ADX']
        if i==0:
            macd1_diff=0
            adx1_diff=0
        else:
            macd1_diff=df[0].iloc[i]['MACD_Histogram']-df[0].iloc[i-1]['MACD_Histogram']
            adx1_diff=df[0].iloc[i]['ADX']-df[0].iloc[i-1]['ADX']
        macd1_diff_list.append(macd1_diff)
        adx1_diff_list.append(adx1_diff)
        if mode=='F': #大周期MACD或n根K线趋势或lor，中周期Lor或MACD，小周期MACD金死叉或Lor:
            if (pred1>0):  # 三个周期，两种指标均是看多
                df1_colors[i] = 'green'
            elif (pred1<0 ):  # 三个周期，两种指标均是看多
                df1_colors[i] = 'red'
            else:
                df1_colors[i]='blue'
            if macd1>0:
                macd_colors[i]='green'
            else:
                macd_colors[i]='red'
            if macd1_diff>0:
                macd_diff_colors[i]='green'
            else:
                macd_diff_colors[i] = 'red'
            if adx>ADX_thr:
                adx_colors[i]='orange'
            else:
                adx_colors[i]='blue'
            if adx1_diff > 0:
                adx_diff_colors[i] = 'green'
            else:
                adx_diff_colors[i] = 'red'

    for i in range(0, len(df1_colors)):
        ax1.plot(df[0].index[i:i+2], df[0]['close_price'].iloc[i:i+2], color=df1_colors[i])
        ax2.bar(df[0].index[i:i+2], df[0]['MACD_Histogram'].iloc[i:i + 2], color=macd_colors[i])
        ax3.bar(df[0].index[i:i + 2], macd1_diff_list[i:i+2], color=macd_diff_colors[i])
        ax4.plot(df[0].index[i:i + 2], df[0]['ADX'].iloc[i:i+2], color=adx_colors[i])
        ax5.bar(df[0].index[i:i + 2], adx1_diff_list[i:i + 2], color=adx_diff_colors[i])


    # 设置网格线
    ax1.grid(True)
    ax2.grid(True)
    ax3.grid(True)
    ax4.grid(True)
    ax5.grid(True)
    ax6.grid(True)
    ax7.grid(True)
    #画Lorentzian买卖信号
    xs_long, ys_long, xs_short, ys_short=get_lorentzian_points(df[0])
    ax1.plot(xs_long,ys_long,'o',color='green')
    ax1.plot(xs_short, ys_short, 'o', color='red')
    # 显示图表
    plt.tight_layout()
    if not dump_file=='' and 'pdf' in dump_file:
        plt.savefig(dump_file, format='pdf', dpi=400)
    else:
        plt.show()
    return


def plot_pair_trading(df1,df2,df_pair,symbols,internal,dump_file=''):
    def signal_color(signal):
        color='black'
        if signal==0:
            color='blue'
        elif signal==1:
            color='green'
        elif signal==-1:
            color='red'
        return color

    fig, (ax1, ax2,ax3,ax4,ax5) = plt.subplots(5, 1, figsize=(20, 20))  # width,height
    spread=df_pair['spread']
    sma=df_pair['sma']
    bollinger_upper=df_pair['bollinger_upper']
    bollinger_lower=df_pair['bollinger_lower']

    df1_colors=['' for _ in df1.index]
    df2_colors=['' for _ in df2.index]
    for i in range(len(df1)):
        signal_1 = df1.iloc[i]['strategy_signal']
        signal_2 = df2.iloc[i]['strategy_signal']
        df1_colors[i]=signal_color(signal_1)
        df2_colors[i] = signal_color(signal_2)



    ax1.set_title('Close Price of %s_%s %s--%s'%(symbols[0],internal,str(df1['open_time'].tolist()[0]),str(df1['close_time'].tolist()[-1])))
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Price')
    ax2.set_title('Close Price of %s_%s %s--%s'%(symbols[1],internal,str(df2['open_time'].tolist()[0]),str(df2['close_time'].tolist()[-1])))
    ax2.set_xlabel('Time')
    ax2.set_ylabel('Price')
    for i in range(0, len(df1_colors)): #蓝色打底
        if df1_colors[i]=='blue':
            ax1.plot(df1.index[i:i + 2], df1['close_price'].iloc[i:i + 2], color=df1_colors[i])
            ax2.plot(df2.index[i:i + 2], df2['close_price'].iloc[i:i + 2], color=df2_colors[i])
    for i in range(0, len(df1_colors)): #红绿置顶
        if df1_colors[i]!='blue':
            ax1.plot(df1.index[i:i + 2], df1['close_price'].iloc[i:i + 2], color=df1_colors[i])
            ax2.plot(df2.index[i:i + 2], df2['close_price'].iloc[i:i + 2], color=df2_colors[i])

    ax3.set_title('Pair %s--%s %s Trading Strategy %s--%s'%(symbols[0],symbols[1],internal,str(df1['open_time'].tolist()[0]),str(df1['close_time'].tolist()[-1])))
    ax3.set_xlabel('Time')
    ax3.set_ylabel('Spread')
    ax3.plot(pd.Series(spread).index, spread, label='Spread')  # 假设 spread 是 Pandas Series
    ax3.plot(sma.index, sma, label='SMA', linestyle='--')  # 同上，sma 也需要是 Pandas Series
    ax3.plot(bollinger_upper.index, bollinger_upper, label='Bollinger Upper', linestyle='-.')
    ax3.plot(bollinger_lower.index, bollinger_lower, label='Bollinger Lower', linestyle='-.')

    balance_1=df1['balance']
    balance_2=df2['balance']
    balance=pd.Series(balance_1.values+balance_2.values)
    min_balance=min(balance)

    ax4.set_title('Partial Balance')
    ax4.set_xlabel('Time')
    ax4.set_ylabel('Balance')
    ax4.plot(range(len(balance)), balance_1, color='red')
    ax4.plot(range(len(balance)), balance_2, color='blue')

    # 计算年化收益
    time_diff=pd.to_timedelta(df1['close_time'].values[-1] - df1['open_time'].values[0], unit='s')
    profit=(balance.iloc[-1]-balance.iloc[0])/balance.iloc[0]
    annual_profit=profit/time_diff.total_seconds()*(86400*365)*100
    ax5.set_title('Final Balance:%.3f, Min Balance:%.3f, Annual_profit:%.3f%%'%(balance.iloc[-1],min_balance,annual_profit))
    ax5.set_xlabel('Time')
    ax5.set_ylabel('Balance')

    ax5.plot(range(len(balance)), balance, color='black')

    ax1.grid(True)
    ax2.grid(True)
    ax3.grid(True)
    ax4.grid(True)
    ax5.grid(True)
    plt.tight_layout()
    if not dump_file=='' and 'pdf' in dump_file:
        plt.savefig(dump_file, format='pdf', dpi=400)
    else:
        plt.show()
    return

def plot_wave(df,symbol,interval,dump_file=''):
    fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, figsize=(108, 18))

    # 上部子图：绘制收盘价曲线
    ax1.set_title('%s---%s %s-%s Close Price'%(symbol,interval,str(df['open_time'].tolist()[0]),str(df['close_time'].tolist()[-1])))
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Price')
    ax2.set_title('Wave Factor')
    ax2.set_xlabel('Time')
    ax2.set_ylabel('Wave Value')
    ax3.set_title('MACD')
    ax3.set_xlabel('Time')
    ax3.set_ylabel('MACD Value')

    # 初始化颜色数组
    colors = ['' for _ in df.index]
    wave_colors=['' for _ in df.index]
    wave_1d_colors = ['' for _ in df.index]
    macd_colors = ['' for _ in df.index]
    # 根据o和s的大小关系设置颜色
    for i in range(len(df)):
        if df['wave_o'].iloc[i] > df['wave_s'].iloc[i]: # o>s ?
            wave_colors[i]='green'
        else:
            wave_colors[i]='red'
        if df['wave_1d_h'].iloc[i]> 0: # o>s ?
            wave_1d_colors[i]='green'
        else:
            wave_1d_colors[i]='red'
        if df['MACD_Histogram'].iloc[i]>0:
            macd_colors[i]='green'
        else:
            macd_colors[i]='red'
        if df['strategy_signal'].iloc[i]==1:
            colors[i] = 'green'
        elif df['strategy_signal'].iloc[i]==-1:
            colors[i] = 'red'
        else:
            colors[i]='blue'
    df['colors']=colors

    # 绘制收盘价曲线，根据颜色数组绘制
    for i in range(20, len(colors)):
        ax1.plot(df.index[i:i+2], df['close_price'].iloc[i:i+2], color=colors[i])
        ax2.plot(df.index[i:i + 2], df['wave_o'].iloc[i:i + 2], color=wave_colors[i])
        ax2.plot(df.index[i:i + 2], df['wave_s'].iloc[i:i + 2], color=wave_colors[i])
        ax3.plot(df.index[i:i + 2], df['wave_1d_h'].iloc[i:i + 2], color=wave_1d_colors[i])
        #ax3.bar(df.index[i:i + 2], df['MACD_Histogram'].iloc[i:i + 2], color=macd_colors[i])

    ax2.axhline(y=100, linestyle=':', color='red')
    ax2.axhline(y=0, linestyle=':', color='blue')
    ax2.axhline(y=-100, linestyle=':', color='green')
    balance=df['balance']
    min_balance = min(balance)
    # 计算年化收益
    time_diff=pd.to_timedelta(df['close_time'].values[-1] - df['open_time'].values[0], unit='s')
    profit=(balance.iloc[-1]-balance.iloc[0])/balance.iloc[0]
    annual_profit=profit/time_diff.total_seconds()*(86400*365)*100
    ax4.set_title('Final Balance:%.3f, Min Balance:%.3f, Annual_profit:%.3f%%'%(balance.iloc[-1],min_balance,annual_profit))
    ax4.set_xlabel('Time')
    ax4.set_ylabel('Balance')
    ax4.plot(range(len(balance)), balance, color='black')
    # 设置网格线
    ax1.grid(True)
    ax2.grid(True)
    ax3.grid(True)
    ax4.grid(True)

    xs_long, ys_long, xs_short, ys_short=get_lorentzian_points(df)
    ax1.plot(xs_long,ys_long,'o',color='green')
    ax1.plot(xs_short, ys_short, 'o', color='red')
    # 显示图表
    plt.tight_layout()
    if not dump_file=='' and 'pdf' in dump_file:
        plt.savefig(dump_file, format='pdf', dpi=400)
    else:
        plt.show()
    return