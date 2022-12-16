
from distutils.util import strtobool
from flask import Blueprint, flash, redirect, url_for
from flask_login import login_required
from changedetectionio.store import ChangeDetectionStore
from changedetectionio import queuedWatchMetaData
from queue import PriorityQueue

PRICE_DATA_TRACK_ACCEPT = 'accepted'
PRICE_DATA_TRACK_REJECT = 'rejected'

def construct_blueprint(datastore: ChangeDetectionStore, update_q: PriorityQueue):

    price_data_follower_blueprint = Blueprint('price_data_follower', __name__)

    @login_required
    @price_data_follower_blueprint.route("/<string:uuid>/accept", methods=['GET'])
    def accept(uuid):
        datastore.data['watching'][uuid]['track_ldjson_price_data'] = PRICE_DATA_TRACK_ACCEPT
        update_q.put(queuedWatchMetaData.PrioritizedItem(priority=1, item={'uuid': uuid, 'skip_when_checksum_same': False}))
        return redirect(url_for("form_watch_checknow", uuid=uuid))


    @login_required
    @price_data_follower_blueprint.route("/<string:uuid>/reject", methods=['GET'])
    def reject(uuid):
        datastore.data['watching'][uuid]['track_ldjson_price_data'] = PRICE_DATA_TRACK_REJECT
        return redirect(url_for("index"))


    return price_data_follower_blueprint


