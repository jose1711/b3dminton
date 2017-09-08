#!/usr/bin/env python
"""
generates html and png file from b3dminton
statistics
"""
import pandas as pd
import numpy as np
import json
import os
import math
import matplotlib.pyplot as plt

from itertools import permutations
from glob import glob
from jinja2 import Environment, FileSystemLoader, select_autoescape
from matplotlib.pyplot import cm
from matplotlib import style

# matplot style for graphs
style.use('fivethirtyeight')

# df2 is the "master" dataframe containing
# all scores - we populate this with contents
# of bedminton-game-data.json
df2 = pd.DataFrame()

env = Environment(
    loader=FileSystemLoader('templates'),
    autoescape=select_autoescape(['html', 'xml'])
)

template_main = env.get_template('bedasstats.html')
template_player2player = env.get_template('player2player.html')


def do_graph(title,
             colors=cm.Dark2.colors,
             players=8,
             filename=None,
             dataframe=None,
             legend_loc='center left',
             height=9.6,
             width=12.8
             ):
    """
    makes a graph from a dataframe. output is written into
    a filename (.png)
    """
    colorlist = list(colors)
    ax = dataframe.fillna(0).plot(title=title,
                                  linewidth=3,
                                  )
    frequent_players = total_matches_count.index[:players]
    lines, labels = ax.get_legend_handles_labels()
    new_lines = []
    new_labels = []
    for line, label in zip(lines, labels):
        if label in frequent_players:
            line.set_color(colorlist.pop())
            new_labels.append(label)
            new_lines.append(line)
        else:
            line.set_color('black')
            line.set_linewidth(0.15)
            line.set_linestyle((1, (1, 1)))
            gray = line

    new_lines.append(gray)
    new_labels.append('others')
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.9, box.height])
    ax.legend(new_lines, new_labels, loc=legend_loc, bbox_to_anchor=(1, 0.5))
    fig = ax.get_figure()
    fig.set_figheight(height)
    fig.set_figwidth(width)
    fig.savefig(filename)


def r(body, series_label='#'):
    """
    converts dataframe/series object into html code. function is called
    by jinja2 template

    """
    out = ''
    if isinstance(body, pd.DataFrame):
        try:
            out = body.to_html(float_format='%.2f')
        except TypeError:
            out = body.to_html()
    elif isinstance(body, pd.Series):
        out = body.to_frame(series_label).to_html(float_format='%.1f')
    else:
        out = body
    return out


# populate df2 with contents of bedminton-game.data.json
with open('bedminton-game-data.json') as f:
    while True:
        line = f.readline().strip()
        if not line:
            break
        date, player_names, games = json.loads(line)
        index = pd.MultiIndex.from_tuples([(pd.to_datetime(date), x)
                                           for x in player_names])
        df = pd.DataFrame(games, index=index, columns=player_names)
        df2 = pd.concat([df2, df])

df2.sort_index()

total_matches_count = df2[df2.fillna(0) != 0].groupby(level=0).count()
total_matches_count = total_matches_count.sum().sort_values(ascending=False)
total_win_count = df2[df2 > 0].groupby(level=0).count().sum().sort_values(ascending=False)
total_winning_percentage = (total_win_count * 100 / total_matches_count).sort_values(ascending=False)

total_losses_count = df2[df2 < 0].count().sort_values(ascending=False)


wl = pd.DataFrame([df2[df2 > 0].count(), df2[df2 < 0].count()], index=['win',
                                                                       'loss']).T


game_points_weeks = df2.apply(abs).groupby(level=0).sum()
do_graph(title='Game points by weeks',
         colors=cm.Dark2.colors,
         players=8,
         filename='gp_by_months_8.png',
         dataframe=game_points_weeks,
         width=24)


game_points_total = df2.apply(abs).sum().sort_values(ascending=False)
# at least 2 visits in month
two_or_more_a_month = (df2[df2.fillna(0) != 0].groupby(level=0).count() > 0).groupby(lambda n: n.strftime('%y%m')).sum() > 1

# winning percentage - winners by months but only if attended at least 2x a month
matches_count_by_months = df2[df2.fillna(0) != 0].groupby(lambda n: n.strftime('%y%m'), level=0).count()
win_count_by_months = df2[df2 > 0].groupby(lambda n: n.strftime('%y%m'), level=0).count()
winmatch_ratio_by_months = (win_count_by_months * 100 / matches_count_by_months)
winmatch_ratio_by_months_stable = winmatch_ratio_by_months.T[two_or_more_a_month.T][winmatch_ratio_by_months.T[two_or_more_a_month.T] == winmatch_ratio_by_months.T[two_or_more_a_month.T].max()].T.dropna(axis='columns', how='all')
winmatch_ratio_by_months_stable = winmatch_ratio_by_months_stable.fillna(' ')


matches_count_by_weeks = df2[df2.fillna(0) != 0].groupby(level=0).count()
win_count_by_weeks = df2[df2 > 0].groupby(level=0).count()
winmatch_ratio_by_weeks = (win_count_by_weeks * 100 / matches_count_by_weeks)

# most (dis)balanced weeks (by standard deviation of players' percentage)
balance_by_weeks = winmatch_ratio_by_weeks.transpose().std().sort_values().iloc[[0, -1]]

do_graph(title='Winning percentage by month - first 8',
         colors=cm.Dark2.colors,
         players=8,
         filename='wp_by_months_8.png',
         dataframe=winmatch_ratio_by_months
         )

do_graph(title='Winning percentage by month - first 12',
         colors=cm.Paired.colors,
         players=12,
         filename='wp_by_months_12.png',
         dataframe=winmatch_ratio_by_months
         )


df2 = df2.replace(0, np.nan)

encounters = df2.groupby(level=1).count()

close_wins = df2[df2 < -12].T.count().groupby(level=1).sum().sort_values(ascending=False).head()
close_losses = df2[df2 < -12].count().sort_values(ascending=False).head()

df2.to_excel('input_data.xlsx')

max_points_scored_vs_opponent = df2.apply(abs).groupby(level=1).max()
avg_points_scored_vs_opponent = df2.apply(abs).groupby(level=1).mean()


attendance_by_weeks = (df2.groupby(level=0).count() > 0).T.sum()
court_count_by_weeks = (((df2.groupby(level=0).count() > 0).T.sum() - 1) /
                        2.0).apply(math.ceil).apply(lambda n: min(4, n))

total_matches_by_weeks = df2[df2 != np.nan].groupby(level=0).count().T.sum() // 2

df_courts_attendance = pd.concat([court_count_by_weeks, attendance_by_weeks],
                                 axis=1)
df_courts_attendance.columns = ['courts', 'players']

# costs computation is fairly inaccurate - better disable it
# costs = df_courts_attendance['courts'] * 11.7 / df_courts_attendance['players']
# df_courts_attendance['costs'] = costs

average_points_per_match = df2.apply(abs).mean()
average_points_per_won_match = df2[df2 > 0].mean()
average_points_per_lost_match = df2[df2 < 0].mean().apply(abs)
median_points_per_lost_match = df2[df2 < 0].median().apply(abs)

df_avg_points_per_match = pd.concat([average_points_per_match,
                                     average_points_per_won_match,
                                     average_points_per_lost_match,
                                     median_points_per_lost_match],
                                    axis=1)
df_avg_points_per_match.columns = ['all', 'only wins', 'only losses', 'only '
                                   'losses\n(median)']
df_avg_points_per_match = df_avg_points_per_match.sort_values('all', ascending=False)

points_scored = df2.apply(abs).sum().sort_values(ascending=False)
opponent_points = df2.apply(abs).sum(1).groupby(level=1).sum().sort_values(ascending=False)

scored_vs_opponent_points = pd.concat([points_scored, opponent_points], axis=1)
scored_vs_opponent_points.columns = ['player points', 'opponent points']
scored_vs_opponent_points = pd.concat([scored_vs_opponent_points,
                                       scored_vs_opponent_points['player points']/scored_vs_opponent_points['opponent points']],
                                      axis=1)

scored_vs_opponent_points.columns = ['player points', 'opponent points', 'ratio']

last_number_players = (df2.groupby(level=0).count().iloc[-1] > 0).sum()
last_date = df2.index.values[-1][0].strftime('%d.%m.%Y')
cost = 11.7 * 4 / last_number_players

print(template_main.render(**locals()))

# create directory structure for player vs player graphs + pages
if not os.path.exists(os.path.join('/tmp', 'players')):
    os.mkdir(os.path.join('/tmp', 'players'))

for player in df2.columns:
    os.mkdir(os.path.join('/tmp', 'players', player))

plt.cla()
ax = plt.subplot()
# player vs player graphs
for player, opponent in permutations(df2.columns, 2):
    dfax = pd.concat([df2[player].loc[:, opponent],
                      df2[opponent].loc[:, player]], axis=1)
    # skip if there hasn't been an encounter
    if len(dfax.dropna()) == 0:
        continue
    ax = dfax.plot(ax=ax, kind='bar', width=0.3,
                   title='{} vs {}'.format(player, opponent))
    ax.set_xticklabels([x.strftime('%W/%y') for x in dfax.index],
                       rotation=0,
                       fontsize='small')
    ax.set_ylim([-20, 20])
    ax.set_ylabel('- loss    + win')
    ax.hlines(0, -15, 24)
    ax.hlines(15, -15, 24, colors='red')
    ax.hlines(-15, -15, 24, colors='red')
    ax.figure.savefig('/tmp/players/{0}/{0}_vs_{1}.png'.format(player,
                                                               opponent))
    plt.cla()

# player vs player html pages
for player in df2.columns:
    with open('/tmp/players/{}.html'.format(player), 'w') as f:
        os.chdir('/tmp/players/{}'.format(player))
        f.write(template_player2player.render(images=sorted(glob('*.png')),
                                              player=player))
