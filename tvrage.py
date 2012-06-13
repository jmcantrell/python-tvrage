import urllib
from datetime import datetime
from lxml import etree

API_KEY = None


def is_list(value):
    return isinstance(value, (tuple, list))


class Element(object):  # {{{1

    def __init__(self, e):
        super(Element, self).__init__()
        self.e = e

    def set_attribute(self, name, f=None):
        value = self.e.get(name)
        try:
            if f:
                value = f(value)
        except TypeError:
            pass
        setattr(self, name, value)

    def set_element(self, name, f=None):
        try:
            value = self.e.find(name).text
            if f:
                value = f(value)
        except AttributeError:
            value = None
        setattr(self, name, value)

    def set_elements(self, names, f=None):
        for name in names:
            self.set_element(name, f)

    def set_dict(self, name, keys):
        e = self.e.find(name)
        data = {}
        for key in keys:
            f = None
            if is_list(key):
                key, f = key
            value = e.find(key).text
            if f:
                value = f(value)
            data[key] = value
        setattr(self, name, data)

    def set_element_list(self, name, f=None):
        values = []
        for x in self.e.find(name):
            value = x.text
            if f:
                value = f(value)
            values.append(value)
        setattr(self, name, values)

    def set_element_dict(self, name, key, fkey=None, fvalue=None):
        data = {}
        for x in self.e.find(name):
            k = x.get(key)
            if fkey:
                k = fkey(k)
            v = x.text
            if fvalue:
                v = fvalue(v)
            data[k] = v
        setattr(self, name, data)


class TVRage(object):  # {{{1

    url = 'http://services.tvrage.com/myfeeds/{command}.php?key={api_key}&{parameters}'

    def __init__(self, api_key=None):
        super(TVRage, self).__init__()
        self.api_key = api_key or API_KEY

    def get_results(self, command, parameters=None):
        data = {
                'api_key': self.api_key,
                'command': command,
                'parameters': '',
                }
        if parameters:
            data['parameters'] = urllib.urlencode(parameters)
        url = self.url.format(**data).strip('&')
        return etree.parse(urllib.urlopen(url)).getroot()

    def search(self, show):
        return [Show(e) for e in self.get_results('search', {'show': show})]

    def get_showinfo(self, showid):
        return ShowInfo(self.get_results('showinfo', {'sid': showid}))

    def get_episode_list(self, showid):
        return EpisodeList(self.get_results('episode_list', {'sid': showid}))

    def get_episodeinfo(self, showid, season, episode):
        return EpisodeInfo(
                self.get_results('episodeinfo', {
                    'sid': showid,
                    'ep': '{}x{}'.format(season, episode)
                    })
                )

    def get_fullschedule(self):
        return FullSchedule(self.get_results('fullschedule'))

    def get_countdown(self):
        return Countdown(self.get_results('countdown'))

    def get_currentshows(self):
        return CurrentShows(self.get_results('currentshows'))


class Show(Element):  # {{{1

    def __init__(self, e):
        super(Show, self).__init__(e)
        self.set_elements([
            'name',
            'link',
            'status',
            'classification',
            'country',
            ])
        self.set_elements([
            'showid',
            'started',
            'ended',
            'seasons',
            ], int)
        self.set_element_list('genres')

    def __repr__(self):
        return self.name


class ShowInfo(Element):  # {{{1

    def __init__(self, e):
        super(ShowInfo, self).__init__(e)
        self.set_elements([
            'showname',
            'showlink',
            'image',
            'origin_country',
            'status',
            'classification',
            'airtime',
            'airday',
            'timezone',
            ])
        self.set_elements([
            'showid',
            'seasons',
            'started',
            'runtime',
            ], int)
        self.set_elements([
            'startdate',
            'ended',
            ], self.parse_date)
        self.set_element_list('genres')
        self.set_element_dict('network', 'country')
        self.set_element_dict('akas', 'country')

    def parse_date(self, s):
        try:
            return datetime.strptime(s, '%b/%d/%Y')
        except ValueError:
            return None

    def __repr__(self):
        return self.showname


class EpisodeList(Element):  # {{{1

    def __init__(self, e):
        super(EpisodeList, self).__init__(e)
        self.set_element('name')
        self.set_element('totalseasons', int)
        self.seasons = [Season(x) for x in e.find('Episodelist')]

    def __repr__(self):
        return self.name


class Season(Element):  # {{{1

    def __init__(self, e):
        super(Season, self).__init__(e)
        self.set_attribute('no', int)
        self.episodes = [Episode(x) for x in e]

    def __repr__(self):
        return '{:02d}'.format(self.no)


class Episode(Element):  # {{{1

    def __init__(self, e):
        super(Episode, self).__init__(e)
        self.set_elements([
            'prodnum',
            'link',
            'title',
            'screencap',
            ])
        self.set_elements([
            'epnum',
            'seasonnum',
            ], int)
        self.set_element('rating', float)
        self.set_element('airdate', self.parse_date)

    def parse_date(self, s):
        try:
            return datetime.strptime(s, '%Y-%m-%d')
        except ValueError:
            return None

    def __repr__(self):
        return '{:02d}'.format(self.seasonnum)


class EpisodeInfo(Element):  # {{{1

    def __init__(self, e):
        super(EpisodeInfo, self).__init__(e)
        self.set_elements([
            'name',
            'link',
            'country',
            'status',
            'classification',
            'airtime',
            ])
        self.set_elements([
            'runtime',
            ], int)
        self.set_element_list('genres')
        self.set_dict('episode', [
            'number', 'title', 'url',
            ('airdate', self.parse_date),
            ])
        self.set_dict('latestepisode', [
            'number', 'title',
            ('airdate', self.parse_date),
            ])

    def parse_date(self, s):
        return datetime.strptime(s, '%Y-%m-%d')

    def __repr__(self):
        return self.name


class FullSchedule(Element):  # {{{1

    def __init__(self, e):
        super(FullSchedule, self).__init__(e)
        self.dates = {}
        for day in e:
            for time in day:
                times = {}
                for show in time:
                    times[show.get('name')] = {
                            'network': show.find('network').text,
                            'title': show.find('title').text,
                            'ep': show.find('ep').text,
                            'link': show.find('link').text,
                            }
                s = '{} {}'.format(day.get('attr'), time.get('attr'))
                dt = datetime.strptime(s, '%Y-%m-%d %I:%M %p')
                self.dates[dt] = times


class Countdown(Element):  # {{{1

    def __init__(self, e):
        super(Countdown, self).__init__(e)
        self.countries = {}
        for country in e:
            shows = []
            for show in country:
                ep = show.find('upcomingep')
                shows.append({
                        'showid': show.find('showid').text,
                        'showname': show.find('showname').text,
                        'showlink': show.find('showlink').text,
                        'upcomingep': {
                            'link': ep.find('link').text,
                            'title': ep.find('title').text,
                            'epnum': ep.find('epnum').text,
                            'airdate': self.parse_date(
                                ep.find('airdate').text),
                            'relativedate': ep.find('relativedate').text,
                            }
                        })
            self.countries[country.get('name')] = shows

    def parse_date(self, s):
        try:
            return datetime.strptime(s, '%b/%d/%Y')
        except ValueError:
            return None


class CurrentShows(Element):  # {{{1

    def __init__(self, e):
        super(CurrentShows, self).__init__(e)
        self.countries = {}
        for country in e:
            shows = []
            for show in country:
                shows.append({
                    'showid': show.find('showid').text,
                    'showname': show.find('showname').text,
                    'showlink': show.find('showlink').text,
                    })
            self.countries[country.get('name')] = shows
