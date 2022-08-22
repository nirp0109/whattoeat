import requests
import json

request = {
  'token': 'bZ33MfPAz7uhR30',
  'readable': False,
  'paragraph':  u'במוצר יש חיטה. בחיטה יש גלוטן'
}


result = requests.post('https://hebrew-nlp.co.il/service/Morphology/Analyze', json=request).json()
print(result)
for k in result:
  if type(k) == list:
    print('=============================================')
    for i in k:
      print(i)

# request = {
#   'token': 'bZ33MfPAz7uhR30',
#   'readable': False,
#   'text':  u'מה נשמע חברים?'
# }
# result = requests.post('https://hebrew-nlp.co.il/service/Morphology/Normalize', json=request).json()
# print(result)