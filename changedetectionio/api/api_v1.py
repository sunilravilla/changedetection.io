from changedetectionio import queuedWatchMetaData
from flask_restful import abort, Resource
from flask import request, make_response
import validators
from . import auth



# https://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html

class Watch(Resource):
    def __init__(self, **kwargs):
        # datastore is a black box dependency
        self.datastore = kwargs['datastore']
        self.update_q = kwargs['update_q']

    # Get information about a single watch, excluding the history list (can be large)
    # curl http://localhost:4000/api/v1/watch/<string:uuid>
    # ?recheck=true
    @auth.check_token
    def get(self, uuid):
        from copy import deepcopy
        watch = deepcopy(self.datastore.data['watching'].get(uuid))
        if not watch:
            abort(404, message='No watch exists with the UUID of {}'.format(uuid))

        if request.args.get('recheck'):
            self.update_q.put(queuedWatchMetaData.PrioritizedItem(priority=1, item={'uuid': uuid, 'skip_when_checksum_same': True}))
            return "OK", 200

        # Return without history, get that via another API call
        watch['history_n'] = watch.history_n
        return watch

    @auth.check_token
    def delete(self, uuid):
        if not self.datastore.data['watching'].get(uuid):
            abort(400, message='No watch exists with the UUID of {}'.format(uuid))

        self.datastore.delete(uuid)
        return 'OK', 204


class WatchHistory(Resource):
    def __init__(self, **kwargs):
        # datastore is a black box dependency
        self.datastore = kwargs['datastore']

    # Get a list of available history for a watch by UUID
    # curl http://localhost:4000/api/v1/watch/<string:uuid>/history
    def get(self, uuid):
        watch = self.datastore.data['watching'].get(uuid)
        if not watch:
            abort(404, message='No watch exists with the UUID of {}'.format(uuid))
        return watch.history, 200


class WatchSingleHistory(Resource):
    def __init__(self, **kwargs):
        # datastore is a black box dependency
        self.datastore = kwargs['datastore']

    # Read a given history snapshot and return its content
    # <string:timestamp> or "latest"
    # curl http://localhost:4000/api/v1/watch/<string:uuid>/history/<int:timestamp>
    @auth.check_token
    def get(self, uuid, timestamp):
        watch = self.datastore.data['watching'].get(uuid)
        if not watch:
            abort(404, message='No watch exists with the UUID of {}'.format(uuid))

        if not len(watch.history):
            abort(404, message='Watch found but no history exists for the UUID {}'.format(uuid))

        if timestamp == 'latest':
            timestamp = list(watch.history.keys())[-1]

        with open(watch.history[timestamp], 'r') as f:
            content = f.read()

        response = make_response(content, 200)
        response.mimetype = "text/plain"
        return response


class CreateWatch(Resource):
    def __init__(self, **kwargs):
        # datastore is a black box dependency
        self.datastore = kwargs['datastore']
        self.update_q = kwargs['update_q']

    @auth.check_token
    def post(self):
        # curl http://localhost:4000/api/v1/watch -H "Content-Type: application/json" -d '{"url": "https://my-nice.com", "tag": "one, two" }'
        json_data = request.get_json()
        tag = json_data['tag'].strip() if json_data.get('tag') else ''

        if not validators.url(json_data['url'].strip()):
            return "Invalid or unsupported URL", 400

        extras = {'title': json_data['title'].strip()} if json_data.get('title') else {}

        new_uuid = self.datastore.add_watch(url=json_data['url'].strip(), tag=tag, extras=extras)
        self.update_q.put(queuedWatchMetaData.PrioritizedItem(priority=1, item={'uuid': new_uuid, 'skip_when_checksum_same': True}))
        return {'uuid': new_uuid}, 201

    # Return concise list of available watches and some very basic info
    # curl http://localhost:4000/api/v1/watch|python -mjson.tool
    # ?recheck_all=1 to recheck all
    @auth.check_token
    def get(self):
        list = {}
        for k, v in self.datastore.data['watching'].items():
            list[k] = {'url': v['url'],
                       'title': v['title'],
                       'last_checked': v['last_checked'],
                       'last_changed': v.last_changed,
                       'last_error': v['last_error']}

        if request.args.get('recheck_all'):
            for uuid in self.datastore.data['watching'].keys():
                self.update_q.put(queuedWatchMetaData.PrioritizedItem(priority=1, item={'uuid': uuid, 'skip_when_checksum_same': True}))
            return {'status': "OK"}, 200

        return list, 200

class SystemInfo(Resource):
    def __init__(self, **kwargs):
        # datastore is a black box dependency
        self.datastore = kwargs['datastore']
        self.update_q = kwargs['update_q']

    @auth.check_token
    def get(self):
        import time
        overdue_watches = []

        # Check all watches and report which have not been checked but should have been

        for uuid, watch in self.datastore.data.get('watching', {}).items():
            # see if now - last_checked is greater than the time that should have been
            # this is not super accurate (maybe they just edited it) but better than nothing
            t = watch.threshold_seconds()
            if not t:
                # Use the system wide default
                t = self.datastore.threshold_seconds

            time_since_check = time.time() - watch.get('last_checked')

            # Allow 5 minutes of grace time before we decide it's overdue
            if time_since_check - (5 * 60) > t:
                overdue_watches.append(uuid)

        return {
                   'queue_size': self.update_q.qsize(),
                   'overdue_watches': overdue_watches,
                   'uptime': round(time.time() - self.datastore.start_time, 2),
                   'watch_count': len(self.datastore.data.get('watching', {}))
               }, 200
