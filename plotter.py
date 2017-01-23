import requests
import six

from bokeh.client import push_session
from bokeh.layouts import gridplot
from bokeh.plotting import figure, curdoc

# http://bokeh.pydata.org/en/latest/docs/user_guide/server.html#connecting-with-bokeh-client

# here we'll keep configurations
config = {'figures': [{'charts':
                           [{'color': 'black', 'legend': 'average response time', 'marker': 'diamond',
                             'key': 'avg_response_time'},
                            {'color': 'blue', 'legend': 'median response time', 'marker': 'triangle',
                             'key': 'median_response_time'},
                            {'color': 'green', 'legend': 'min response time', 'marker': 'inverted_triangle',
                             'key': 'min_response_time'},
                            {'color': 'red', 'legend': 'max response time', 'marker': 'circle',
                             'key': 'max_response_time'}],
                       'xlabel': 'Requests count',
                       'ylabel': 'Milliseconds',
                       'title': '{} response times'
                       },
                      {'charts': [{'color': 'green', 'legend': 'current rps', 'marker': 'circle',
                                   'key': 'current_rps'},
                                  {'color': 'red', 'legend': 'failures', 'marker': 'cross',
                                   'key': 'num_failures', 'skip_null': True}],
                       'xlabel': 'Requests count',
                       'ylabel': 'RPS/Failures count',
                       'title': '{} RPS/Failures'
                       }],
          'url': 'http://localhost:8089/stats/requests',  # locust json stats url
          'states': ['hatching', 'running'],  # locust states for which we'll plot the graphs
          'requests_key': 'num_requests'
          }

data_sources = {}  # dict with data sources for our figures
figures = []  # list of figures for each state
for state in config['states']:
    data_sources[state] = {}  # dict with data sources for figures for each state
    for figure_data in config['figures']:
        # initialization of figure
        new_figure = figure(title=figure_data['title'].format(state.capitalize()))
        new_figure.xaxis.axis_label = figure_data['xlabel']
        new_figure.yaxis.axis_label = figure_data['ylabel']
        # adding charts to figure
        for chart in figure_data['charts']:
            # adding both markers and line for chart
            marker = getattr(new_figure, chart['marker'])
            scatter = marker(x=[0], y=[0], color=chart['color'], size=10, legend=chart['legend'])
            line = new_figure.line(x=[0], y=[0], color=chart['color'], line_width=1, legend=chart['legend'])
            # adding data source for markers and line
            data_sources[state][chart['key']] = scatter.data_source = line.data_source
        figures.append(new_figure)

requests_key = config['requests_key']
url = config['url']


# Next line opens a new session with the Bokeh Server, initializing it with our current Document.
# This local Document will be automatically kept in sync with the server.
session = push_session(curdoc())


# The next few lines define and add a periodic callback to be run every 1 second:
def update():
    try:
        resp = requests.get(url)
    except requests.RequestException:
        return
    resp_data = resp.json()
    data = resp_data['stats'][-1]  # Getting "Total" data from locust
    if resp_data['state'] in config['states']:
        for key, data_source in six.iteritems(data_sources[resp_data['state']]):
            # adding data from locust to data_source of our graphs
            data_source.data['x'].append(data[requests_key])
            data_source.data['y'].append(data[key])
            # trigger data source changes
            data_source.trigger('data', data_source.data, data_source.data)

curdoc().add_periodic_callback(update, 1000)

session.show(gridplot(figures, ncols=2))  # open browser with gridplot containing 2 figures in row for each state

session.loop_until_closed()  # run forever
