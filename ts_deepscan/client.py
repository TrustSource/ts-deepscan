import requests

from ts_python_client.client import Scanner
from ts_python_client.scan import Scan as TSScan, Dependency, License

from .scanner import Scan as DSScan

class DSScanner(Scanner):
    def __init__(self, scan: DSScan, moduleName: str, deepscanBaseUrl: str):
        super().__init__()
        self._scan = scan
        self._moduleName = moduleName
        self._deepscanBaseUrl = deepscanBaseUrl


    def run(self) -> TSScan:
        print('Uploading results...')

        response = self._upload_scan(self._moduleName, self._deepscanBaseUrl)

        scan_uid = response.get('uid', '')
        scan_url = response.get('url', '')

        if not scan_uid:
            print('Files scan was not uploaded correctly')
            exit(2)

        scan = TSScan(self._moduleName, ns='ds')
        dep = Dependency(key='ds', name=self._moduleName, versions=['0.0.0'])

        dep.licenses = [License(lic) for lic in self._scan.licenses]
        dep.meta = {
            'versions': [{
                'version': '0.0.0',
                "deepScanId": scan_uid,
                "deepScanUrl": scan_url,
                "compatibleLicenses": self._scan.is_compatible_licenses
            }]
        }

        scan.dependencies = [dep]
        return scan


    def _upload_scan(self, moduleName: str, baseUrl: str):
        if not baseUrl:
            baseUrl = 'https://api.prod.trustsource.io/deepscan'

        url = '{}/upload-results?module={}'.format(baseUrl, moduleName)
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': 'ts-deepscan/1.0.0',
            'x-api-key': self.client.settings.apiKey
        }

        response = requests.post(url, json=self._scan.__dict__, headers=headers)

        if response.status_code not in range(200, 300):
            print('Status {}: {}'.format(response.status_code, response.text))
            exit(2)

        try:
            return response.json()
        except ValueError as err:
            print('Cannot decode response')
            print(err)

        return None

