#!/usr/bin/python3

import time
from flask import url_for
from .util import live_server_setup, extract_UUID_from_client, extract_api_key_from_UI

def set_response_with_ldjson():
    test_return_data = """<html>
       <body>
     Some initial text<br>
     <p>Which is across multiple lines</p>
     <br>
     So let's see what happens.  <br>
     <div class="sametext">Some text thats the same</div>
     <div class="changetext">Some text that will change</div>
     <script type="application/ld+json">
        {
           "@context":"https://schema.org/",
           "@type":"Product",
           "@id":"https://www.some-virtual-phone-shop.com/celular-iphone-14/p",
           "name":"Celular Iphone 14 Pro Max 256Gb E Sim A16 Bionic",
           "brand":{
              "@type":"Brand",
              "name":"APPLE"
           },
           "image":"https://www.some-virtual-phone-shop.com/15509426/image.jpg",
           "description":"You dont need it",
           "mpn":"111111",
           "sku":"22222",
           "offers":{
              "@type":"AggregateOffer",
              "lowPrice":8097000,
              "highPrice":8099900,
              "priceCurrency":"COP",
              "offers":[
                 {
                    "@type":"Offer",
                    "price":8097000,
                    "priceCurrency":"COP",
                    "availability":"http://schema.org/InStock",
                    "sku":"102375961",
                    "itemCondition":"http://schema.org/NewCondition",
                    "seller":{
                       "@type":"Organization",
                       "name":"ajax"
                    }
                 }
              ],
              "offerCount":1
           }
        }
       </script>
     </body>
     </html>
"""

    with open("test-datastore/endpoint-content.txt", "w") as f:
        f.write(test_return_data)
    return None

def set_response_without_ldjson():
    test_return_data = """<html>
       <body>
     Some initial text<br>
     <p>Which is across multiple lines</p>
     <br>
     So let's see what happens.  <br>
     <div class="sametext">Some text thats the same</div>
     <div class="changetext">Some text that will change</div>     
     </body>
     </html>
"""

    with open("test-datastore/endpoint-content.txt", "w") as f:
        f.write(test_return_data)
    return None

# actually only really used by the distll.io importer, but could be handy too
def test_check_ldjson_price_autodetect(client, live_server):
    live_server_setup(live_server)

    # Give the endpoint time to spin up
    time.sleep(1)

    set_response_with_ldjson()

    # Add our URL to the import page
    test_url = url_for('test_endpoint', _external=True)
    res = client.post(
        url_for("import_page"),
        data={"urls": test_url},
        follow_redirects=True
    )
    assert b"1 Imported" in res.data
    time.sleep(3)

    # Should get a notice that it's available
    res = client.get(url_for("index"))
    assert b'ldjson-price-track-offer' in res.data

    # Accept it
    uuid = extract_UUID_from_client(client)

    client.get(url_for('price_data_follower.accept', uuid=uuid, follow_redirects=True))
    time.sleep(2)

    # Trigger a check
    client.get(url_for("form_watch_checknow"), follow_redirects=True)
    time.sleep(2)
    # Offer should be gone
    res = client.get(url_for("index"))
    assert b'Embedded price data' not in res.data
    assert b'tracking-ldjson-price-data' in res.data

    # and last snapshop (via API) should be just the price
    api_key = extract_api_key_from_UI(client)
    res = client.get(
        url_for("watchsinglehistory", uuid=uuid, timestamp='latest'),
        headers={'x-api-key': api_key},
    )

    # Should see this (dont know where the whitespace came from)
    assert b'"highPrice": 8099900' in res.data
    # And not this cause its not the ld-json
    assert b"So let's see what happens" not in res.data

    client.get(url_for("form_delete", uuid="all"), follow_redirects=True)

    ##########################################################################################
    # And we shouldnt see the offer
    set_response_without_ldjson()

    # Add our URL to the import page
    test_url = url_for('test_endpoint', _external=True)
    res = client.post(
        url_for("import_page"),
        data={"urls": test_url},
        follow_redirects=True
    )
    assert b"1 Imported" in res.data
    time.sleep(3)
    res = client.get(url_for("index"))
    assert b'ldjson-price-track-offer' not in res.data
    
    ##########################################################################################
    client.get(url_for("form_delete", uuid="all"), follow_redirects=True)
