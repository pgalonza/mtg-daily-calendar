import calendar
import yaml
import collections
import datetime
import json
import requests
import urllib.parse
import locale

SETTINGS_FILE = 'settings-example.yaml'


class MTGCalendar:
    def __init__(self, clubs_list: dict):
        self.timetable = collections.defaultdict(list)
        self.clubs_list = clubs_list
        self.month_events = dict()
        self._create_events_schedule()

    def _create_events_schedule(self):
        for club in self.clubs_list:
            for event_day, event_time in club['schedule'].items():
                self.timetable[event_day].append(dict(club_name=club['club_name'], time=event_time))

    def create_month_schedule(self):
        current_date: 'datetime' = datetime.datetime.now()
        general_calendar: 'calendar' = calendar.Calendar()
        current_month = general_calendar.itermonthdates(current_date.year, current_date.month)

        for month_day in current_month:
            print(month_day, self.timetable[month_day.strftime('%A')])

    def get_next_events(self, next_delta: int = 1):
        current_date: 'datetime' = datetime.datetime.now()
        next_date: 'datetime' = current_date + datetime.timedelta(days=next_delta)
        clubs_list: list = self.timetable[next_date.strftime('%A')]
        if not clubs_list:
            return None
        locale.setlocale(locale.LC_TIME, "ru_RU.utf8")
        locale_date: str = next_date.strftime('%a %d-%B')
        return {'event_date': locale_date, 'clubs_list': clubs_list}


class VKGroup:
    def __init__(self, user_token: str, api_url: str, group_id: str):
        self.user_token = user_token
        self.api_version = '5.130'
        self.api_url = api_url
        self.group_id = group_id

    def create_poll(self, day_events):
        clubs_choice = list()
        for club_info in day_events['clubs_list']:
            clubs_choice.append(f'{club_info["club_name"]} в {club_info["time"]}')
        else:
            clubs_choice.append('Не иду')
        params = {
            'access_token': self.user_token,
            'v': self.api_version,
            'question': day_events['event_date'],
            'is_multiple': 0,
            # 'end_date': 0,
            'owner_id': self.group_id,
            'add_answers': json.dumps(clubs_choice),
            'background_id': 8,
        }
        api_url = urllib.parse.urljoin(self.api_url, 'method/polls.create')

        result: 'requests' = requests.post(api_url, params=params)
        return result.json()['response']['id']

    def create_post(self, poll_id: str, post_date=None):

        params = {
            'access_token': self.user_token,
            'v': self.api_version,
            'owner_id': self.group_id,
            'signed': 0,
            'from_group': 1,
            # 'message': 'Testing',
            'attachments': f'poll{self.group_id}_{poll_id}'
        }

        if post_date:
            current_date: 'datetime' = datetime.datetime.now()
            next_date: 'datetime' = current_date + datetime.timedelta(days=post_date)
            next_date: 'datetime' = next_date.replace(hour=0, minute=0, second=0, microsecond=0)
            params['publish_date'] = next_date.timestamp(),

        api_url = urllib.parse.urljoin(self.api_url, 'method/wall.post')
        result = requests.post(api_url, params=params)
        print(result.json())


def main():
    with open(SETTINGS_FILE) as file_object:
        config = yaml.load(file_object, Loader=yaml.FullLoader)

    with open(config['clubs_file']) as file_object:
        clubs_list = yaml.load(file_object, Loader=yaml.FullLoader)

    mtg_calendar = MTGCalendar(clubs_list)

    next_events = mtg_calendar.get_next_events(2)
    vkontakte = config['vkontakte']
    mtg_vk = VKGroup(**vkontakte)
    if next_events:
        poll_id = mtg_vk.create_poll(next_events)
        mtg_vk.create_post(poll_id, 1)


if __name__ == '__main__':
    main()
