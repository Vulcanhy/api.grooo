__author__ = 'Vulcanhy & responsible'
import base64
import requests
import json


def jpush_msg(title, description, RID):
    try:
        posturl = "https://api.jpush.cn/v3/push"
        AppKey = b"685504ef5a4d0c66ca018f9d"
        MasterSecret = b"d35787991c210b4ec2e6568d"
        post_json = {"platform": "all",
                     "audience": {"registration_id": [RID]},
                     "notification": {
                         "android": {"alert": description,
                                     "title": title,
                                     "builder_id": 1}
                     },
                     "message": {"msg_content": "play"},
                     "options": {"apns_production": False}
                     }
        requests.post(posturl, data=json.dumps(post_json),
                      headers={"Authorization":
                                   "Basic %s" % str(base64.b64encode(b"%s:%s" % (AppKey, MasterSecret)))[2:-1]})
    except:
        pass
