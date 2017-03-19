# Load testing with Locust and Bokeh

Scalability testing is important part of getting web service production ready.
There are a lot of tools for load testing like Gatling, Apache JMeter, The Grinder, Tsung and others. Also there is one (and my favorite) written in Python and built on the [Requests](http://docs.python-requests.org/en/master/) library: [Locust](http://locust.io/).

As noticed on Locust website:
> A fundamental feature of Locust is that you describe all your test in Python code. No need for clunky UIs or bloated XML, just plain code.

## Locust installation
Locust load testing library requires **Python 2.6+**. It is not currently compatible with Python 3.x.
Performance testing python module Locust is available on PyPI and can be installed through pip or easy_install

`pip install locustio` or: `easy_install locustio`

## Example locustfile.py
Then create *locustfile.py* following [example](http://docs.locust.io/en/latest/quickstart.html#example-locustfile-py) from docs. To test Django project I had to add some headers for csrftoken support and ajax requests. Resulting *locustfile.py* could be something like following:

```python
# locustfile.py
from locust import HttpLocust, TaskSet, task


class UserBehavior(TaskSet):

    def on_start(self):
        self.login()

    def login(self):
        # GET login page to get csrftoken from it
        response = self.client.get('/accounts/login/')
        csrftoken = response.cookies['csrftoken']
        # POST to login page with csrftoken
        self.client.post('/accounts/login/',
                         {'username': 'username', 'password': 'P455w0rd'},
                         headers={'X-CSRFToken': csrftoken})

    @task(1)
    def index(self):
        self.client.get('/')

    @task(2)
    def heavy_url(self):
        self.client.get('/heavy_url/')

    @task(2)
    def another_heavy_ajax_url(self):
        # ajax GET
        self.client.get('/another_heavy_ajax_url/',
        headers={'X-Requested-With': 'XMLHttpRequest'})


class WebsiteUser(HttpLocust):
    task_set = UserBehavior
```

## Start Locust

To run Locust with the above python locust file, if it was named *locustfile.py*, we could run (in the same directory as *locustfile.py*):

`locust --host=http://example.com`

When python load testing app Locust is started you should visit [http://127.0.0.1:8089/](http://127.0.0.1:8089/) and there you'll find web-interface of our Locust instance. Then input **Number of users to simulate** (e.g. 300) and **Hatch rate (users spawned/second)** (e.g. 10) and press **Start swarming**. After that Locust will start "hatching" users and you can see results in table.

## Python Data Visualization
So table is nice but we'd prefer to see results on graph. There is an [issue](https://github.com/locustio/locust/issues/144) in which people ask to add graphical interface to Locust and there are several propositions how to display graphs for Locust data. I've decided to use Python interactive visualization library [Bokeh](http://bokeh.pydata.org/en/latest/).

It is easy to install python graphing library Bokeh from PyPI using pip:

`pip install bokeh`

Here is an [example](http://bokeh.pydata.org/en/latest/docs/user_guide/server.html#connecting-with-bokeh-client) of running Bokeh server.

We can get Locust data in JSON format visiting [http://localhost:8089/stats/requests]. Data there should be something like:
```json
{
   "errors": [],
   "stats": [
       {
           "median_response_time": 350,
           "min_response_time": 311,
           "current_rps": 0.0,
           "name": "/",
           "num_failures": 0,
           "max_response_time": 806,
           "avg_content_length": 17611,
           "avg_response_time": 488.3333333333333,
           "method": "GET",
           "num_requests": 9
       },
       {
           "median_response_time": 350,
           "min_response_time": 311,
           "current_rps": 0.0,
           "name": "Total",
           "num_failures": 0,
           "max_response_time": 806,
           "avg_content_length": 17611,
           "avg_response_time": 488.3333333333333,
           "method": null,
           "num_requests": 9
       }
   ],
   "fail_ratio": 0.0,
   "slave_count": 2,
   "state": "stopped",
   "user_count": 0,
   "total_rps": 0.0
}
```

To display this data on interactive plots we'll create *plotter.py* file, built on usage of python visualization library Bokeh, and put it to the  directory in which our *locustfile.py* is:

```python
# plotter.py
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

```

## Running all together

So our Locust is running (if no, start it with `locust --host=http://example.com`) and now we should start Bokeh server with `bokeh serve` and then run our *plotter.py* with `python plotter.py`. As our script calls **show** a browser tab is automatically opened up to the correct URL to view the document.

If Locust is already running the test you'll see results on graphs immediately. If no start new test at [http://localhost:8089/]() and return to the Bokeh tab and watch the results of testing in real time.

That's it. You can find all code at [https://github.com/steelkiwi/locust-bokeh-load-test](https://github.com/steelkiwi/locust-bokeh-load-test).

Feel free to clone it and run example. Don't forget to use **Python 2.6+** (Locust is not Python 3.x compatible for now):
```
git clone https://github.com/steelkiwi/locust-bokeh-load-test.git
cd locust-bokeh-load-test
pip install -r requirements.txt
locust --host=<place here link to your site>
bokeh serve
python plotter.py
```

You should have Bokeh tab opened in browser after running these commands. Now visit [http://localhost:8089/] and start test there. Return to Bokeh tab and enjoy the graphs.
