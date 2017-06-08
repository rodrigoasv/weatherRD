from distutils.core import setup
import py2exe
import sys
from glob import glob
data_files = [("Microsoft.VC90.CRT",
               glob(r'C:\Program Files\Microsoft Visual Studio 9.0\VC\redist\x86\Microsoft.VC90.CRT\*.*')),
              '..\web\images\favicon.ico',
              'realdata.xml']
setup(data_files=data_files)
sys.path.append("C:\\Program Files\\Microsoft Visual Studio 9.0\\VC\\redist\\x86\\Microsoft.VC90.CRT")

setup(
    windows=[
        {
            "script": 'realdata.pyw',
            "icon_resources": [(1, "..\web\images\favicon.ico")]
        }
    ],
      options={
          'py2exe': {
              'dll_excludes': ['api-ms-win-core-processthreads-l1-1-2.dll',
                               'api-ms-win-core-sysinfo-l1-2-1.dll',
                               'api-ms-win-core-heap-l2-1-0.dll',
                               'api-ms-win-core-delayload-l1-1-1.dll',
                               'api-ms-win-core-errorhandling-l1-1-1.dll',
                               'api-ms-win-core-profile-l1-1-0.dll',
                               'api-ms-win-core-libraryloader-l1-2-0.dll',
                               'api-ms-win-core-string-obsolete-l1-1-0.dll',
                               'api-ms-win-security-activedirectoryclient-l1-1-0.dll'],
          }
      })
