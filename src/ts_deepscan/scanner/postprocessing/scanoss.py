import re
import typing as t

from scanoss.scanossapi import ScanossApi

from . import PostProcessor
from .. import ScanResults




class ScanossPostProcessor(PostProcessor):
    def __init__(self, api_key: t.Optional[str] = None):
        self._api_key = api_key

    def apply(self, results: ScanResults) -> ScanResults:                        
        wfps = []
        analysis = {}

        for analysis_result in results.values():
            for res in analysis_result:
                if res.category == 'scanoss' and 'scan' not in res.data:  # if there is no scan data yet
                  # Because of caching we cannot rely on the file path, we need to extract the file hash from the WFP
                  # And use it to map the results later 
                  wfp = res.data.get('wfp')
                  # WFP contains file hash in format file=<md5hash>, that is always 32 hex characters
                  matches = re.findall(r'file=([a-f0-9]{32})', wfp)
                  for file_hash in matches:
                      wfps.append(wfp)
                      analysis[file_hash] = res                 
                  
        scanoss_api = ScanossApi(api_key=self._api_key) if self._api_key else ScanossApi()

        if wfps:
          wfps_results = {}
          wfps_chunk_size = 999

          for i in range(0, len(wfps), wfps_chunk_size):
              try:
                  wfps_results.update(scanoss_api.scan('\n'.join(wfps[i:i + wfps_chunk_size]))) # type: ignore
              except:
                  continue

          if wfps_results:
            for wfp_results in wfps_results.values():
                for wfp_res in wfp_results:
                    if (res_file_hash := wfp_res.get('file_hash')) and (file_analysis := analysis.get(res_file_hash)):
                        file_analysis.data.setdefault('scan', []).append(wfp_res)

        return results