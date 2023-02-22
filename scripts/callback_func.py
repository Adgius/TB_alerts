import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
import pandas as pd
import numpy as np
import configparser
import os
import datetime as dt
from datetime import timedelta

config = configparser.ConfigParser()  # создаём объекта парсера
config.read("scripts/config.ini") 

print(os.getcwd())

def check_alert(x, y, std_scale=2, lag=10, border='lower'): #Из конфига
    x = x.sort_values()
    y = y.values[np.argsort(x)]
    last_x = x.iloc[-1]
    last_y = y[-1]
    start = last_x.date() - timedelta(days=lag)
    Y = y[(x.dt.date >= start) & (x.dt.date < last_x.date())]
    
    mean = Y.mean()
    std = Y.std() * std_scale
    upper = mean + std
    lower = mean - std
    if border == 'lower':
        return last_y < lower
    else:
        return last_y > upper

def check_alerts_all(): #Из конфига

    lag_gp = int(config["GOOGLE_CONST"]["lag_rating"])
    std_gp = float(config["GOOGLE_CONST"]["std_rating"])
    lag_gp_comment = int(config["GOOGLE_CONST"]["lag_comment"])
    std_gp_comment = float(config["GOOGLE_CONST"]["std_comment"])

    lag_as = int(config["AppStore_CONST"]["lag_rating"])
    std_as = float(config["AppStore_CONST"]["std_rating"])
    lag_as_comment = int(config["AppStore_CONST"]["lag_comment"])
    std_as_comment = float(config["AppStore_CONST"]["std_comment"])

    res = pd.read_csv('./ds/res.csv')
    res['date'] = pd.to_datetime(res['date'])
    gp = res[res['source'] == 'GooglePlay']
    ap = res[res['source'] == 'AppStore']

    com_AS = pd.read_csv('./ds/AS_reviews.csv')
    com_AS['date'] = pd.to_datetime(com_AS['date'])
    com_GP = pd.read_csv('./ds/GP_reviews.csv')
    com_GP['at'] = pd.to_datetime(com_GP['at'])

    gp_com_count = com_GP[['score', 'at']].set_index('at').sort_index().rolling(window='2D').count().reset_index()
    ap_com_count = com_AS[['rating', 'date']].set_index('date').sort_index().rolling(window='2D').count().reset_index()
    
    return dict(gp=check_alert(gp['date'], gp['score'], lag=lag_gp, std_scale=std_gp),
                ap=check_alert(ap['date'], ap['score'], lag=lag_as, std_scale=std_as),
                com_AS=check_alert(ap_com_count['date'], ap_com_count['rating'], lag=lag_as_comment, std_scale=std_as_comment),
                com_GP=check_alert(gp_com_count['at'], gp_com_count['score'], lag=lag_gp_comment, std_scale=std_gp_comment))


def plot_dif(x, y, title, lag=10, sd=2, comments=False):
    # Подготовка данных. Лаг 30 дней
    last_date = x.sort_values().dt.date.values[-1]
    
    tail = x.dt.date >= (last_date - timedelta(days=30))
    y = y[tail]
    x = x[tail]
    
    end = (last_date - timedelta(days=3))
    last_value = y.values[-1]
    mean_days_ago = y[(x.dt.date >= end) & (x.dt.date != last_date)].mean()
    
    dif = round(last_value - mean_days_ago, 6)
    color = 'green' if dif >= 0 else 'red'
    pos = ((0.05, 0.06), (0.05, 0.16)) if dif >= 0 else ((0.05, 0.16), (0.05, 0.06)) 
    
    fig, ax = plt.subplots()
    ax.plot(x, y, label='true')
    
    
    y_upper = []
    y_lower = []
    y_pred = []
    X_test = []
    y_alert, X_alert = [], []
    
    for date, value in zip(x, y):
        end = date.date()
        start = date.date() - timedelta(days=lag)
        X_train = y[(x.dt.date >= start) & (x.dt.date < end)]
        mean = X_train.mean()
        std = X_train.std() * sd
        X_test.append(date)
        y_pred.append(mean)
        y_upper.append(mean + std), y_lower.append(mean - std if mean - std > 0 else 0)
        if not comments:
            if value < y_lower[-1]:
                X_alert.append(date)
                y_alert.append(y_lower[-1])

        else:
            if value > y_upper[-1]:
                X_alert.append(date)
                y_alert.append(y_upper[-1])
            
    ax.plot(x, y_pred, c='green', label='predict')        
    ax.scatter(X_alert, y_alert, c='red', label='alert')
    ax.fill_between(x, y_lower, y_upper, alpha=.5, linewidth=0, color='#9fd65f', label='conf.int')      
    # Major ticks every month, minor ticks every day,
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_minor_locator(mdates.DayLocator())
    ax.grid(True)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%b'))
    for label in ax.get_xticklabels(which='major'):
        label.set(rotation=30, horizontalalignment='right')
        
    if comments:
        title += f" :{'↑' if color=='green' else '↓'}{round(dif)}"
    else:
        ax.text(0.1, 0.1, f'{dif:f}', transform=ax.transAxes, bbox=dict(mutation_scale=1, fill=True, color='white', ec='black'), 
                fontsize=15, color=color)
        arrow = mpatches.FancyArrowPatch(pos[0], pos[1],
                                         mutation_scale=5, transform=ax.transAxes, color=color)
        ax.add_patch(arrow)
        
    ax.set_title(title)
    ax.legend()
    plt.savefig(f'{"avg" if not comments else "count"}.png')

def table_manager(name):
    if name == 'gp':
        lag_gp = int(config["GOOGLE_CONST"]["lag_rating"])
        std_gp = float(config["GOOGLE_CONST"]["std_rating"])
        lag_gp_comment = int(config["GOOGLE_CONST"]["lag_comment"])
        std_gp_comment = float(config["GOOGLE_CONST"]["std_comment"])

        res = pd.read_csv('./ds/res.csv') 
        res['date'] = pd.to_datetime(res['date'])
        gp = res[res['source'] == 'GooglePlay']
        x, y = gp['date'], gp['score']
        title = 'GooglePlay'

        com_GP = pd.read_csv('./ds/GP_reviews.csv')
        com_GP['at'] = pd.to_datetime(com_GP['at'])
        gp_com_count = com_GP[['score', 'at']].set_index('at').sort_index().rolling(window='2D').count().reset_index()

        plot_dif(x, y, title, lag=lag_gp, sd=std_gp , comments=False)
        plot_dif(gp_com_count['at'], gp_com_count['score'], title, lag=lag_gp_comment, sd=std_gp_comment , comments=True)

    elif name == 'ap':
        lag_as = int(config["AppStore_CONST"]["lag_rating"])
        std_as = float(config["AppStore_CONST"]["std_rating"])
        lag_as_comment = int(config["AppStore_CONST"]["lag_comment"])
        std_as_comment = float(config["AppStore_CONST"]["std_comment"])

        res = pd.read_csv('./ds/res.csv')
        res['date'] = pd.to_datetime(res['date'])
        ap = res[res['source'] == 'AppStore']
        x, y = ap['date'], ap['score']
        title = 'AppStore'

        com_AS = pd.read_csv('./ds/AS_reviews.csv')
        com_AS['date'] = pd.to_datetime(com_AS['date'])
        ap_com_count = com_AS[['rating', 'date']].set_index('date').sort_index().rolling(window='2D').count().reset_index()
        plot_dif(x, y, title, lag=lag_as, sd=std_as , comments=False)
        plot_dif(ap_com_count['date'], ap_com_count['rating'], title, lag=lag_as_comment, sd=std_as_comment , comments=True)

def alerts_info(d: dict):
    pass