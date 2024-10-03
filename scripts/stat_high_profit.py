import os.path

import pandas as pd
import json
import glob
output_root='C:\\trade\\results\wave_trading\\24.9.18\\'
columns = ['type', 'clen', 'alen', 'slen', 'buy_thresh', 'sell_thresh',
           'return_thresh', 'Final_Balance', ' Min_Balance', ' Annual_profit']
df_total = pd.DataFrame(columns=columns)
df_t10 = pd.DataFrame(columns=columns)
output_list=glob.glob(output_root+'*.txt')
for output_txt in output_list:
    symbol=os.path.basename(output_txt)[:-4]
    print(symbol)
    cnt=0
    with open(output_txt, 'r', encoding='utf-8') as file:
        for line in file:
            if cnt%2==0:
                data_str1 = line.strip().replace("'", '"')
                # 使用json.loads()解析字符串
                data_dict = json.loads(data_str1)
            else:
                # 预处理字符串，使其成为有效的JSON格式
                # 将键和值用双引号包围，并替换百分号
                data_str = line.strip().replace(":", "\": \"").replace(",", "\", \"").replace("%", " ")
                data_str = data_str.replace("Final Balance", "Final_Balance").replace("Min Balance",
                                                                                        "Min_Balance")
                data_str = "{\"" + data_str + "\"}"

                # 使用json.loads()解析字符串
                data_dict2 = json.loads(data_str)
                data_dict.update(data_dict2)
                if cnt==1:
                    df = pd.DataFrame([data_dict])
                    df[[' Annual_profit','Final_Balance',' Min_Balance']]=df[[' Annual_profit','Final_Balance',' Min_Balance']].astype(float)
                else:
                    new_df = pd.DataFrame([data_dict])
                    new_df[[' Annual_profit','Final_Balance',' Min_Balance']] = new_df[[' Annual_profit','Final_Balance',' Min_Balance']].astype(float)
                    df = pd.concat([df, new_df], axis=0)
            cnt+=1
    df['type']=symbol
    df_total=pd.concat([df_total, df], axis=0)
    df_total=pd.concat([df_total, df], axis=0)
    cond=(df[' Min_Balance']>6000) & (df[' Annual_profit']>5)
    df=df[cond]
    df_sorted = df.sort_values(by=' Annual_profit', ascending=False)
    df_t10 = pd.concat([df_t10, df_sorted.head(10)], axis=0)
    df_sorted = df.sort_values(by=' Min_Balance', ascending=False)
    df_t10 = pd.concat([df_t10, df_sorted.head(10)], axis=0)
grouped_df = df_t10.groupby(['clen', 'alen', 'slen', 'buy_thresh', 'sell_thresh',
           'return_thresh']).size().reset_index(name='Counts')
group_sorted = grouped_df.sort_values(by='Counts', ascending=False)

columns = ['clen', 'alen', 'slen', 'buy_thresh', 'sell_thresh',
           'return_thresh', 'Profit_Median','Profit_Mean', ' Min_Balance', ' ratio']
df_stat = pd.DataFrame(columns=columns)
for index, row_info in enumerate(group_sorted.iterrows()):
    row = row_info[1]
    #values=[80,45,25,6,9,0]
    values=[row['clen'], row['alen'], row['slen'],row['buy_thresh'], row['sell_thresh'],row['return_thresh']]
    print(values)
    condition = ((df_total['clen'] == values[0]) & (df_total['alen'] == values[1]) & (df_total['slen'] == values[2]) &
                 (df_total['buy_thresh'] == values[3])) & (df_total['sell_thresh'] == values[4])  & (df_total['return_thresh'] == values[5])
    filtered_df = df_total[condition]
    profit_median=filtered_df[' Annual_profit'].median()
    profit_mean=filtered_df[' Annual_profit'].mean()
    min_balance_median=filtered_df[' Min_Balance'].median()
    positive_ratio=sum(filtered_df[' Annual_profit']>0)/len(filtered_df)
    print('Profit Median: %.3f, Min_Balance:%.3f, ratio:%.3f'%(profit_median,min_balance_median,positive_ratio))
    values = [
        row['clen'],
        row['alen'],
        row['slen'],
        row['buy_thresh'],
        row['sell_thresh'],
        row['return_thresh'],
        profit_median,
        profit_mean,
        min_balance_median,
        positive_ratio
    ]
    # 创建DataFrame
    stat = pd.DataFrame([values], columns=columns)
    df_stat = pd.concat([df_stat, stat], axis=0)
print('testing')