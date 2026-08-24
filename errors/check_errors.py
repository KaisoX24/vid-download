import yt_dlp.utils as ytdlp_utlis
from yt_dlp.networking.exceptions import HTTPError as ytdlpError
from errors.errors import FetchError,_STATUS_MAP

def classify_download_errors(exc:Exception) -> FetchError:
    "Classifies the error given by the YT_dlp to provide proper error message"

    candidates=[]
    cause=getattr(exc,'cause',None)
    if cause is not None: candidates.append(cause)

    exc_info=getattr(exc,'exc_info',None)
    if exc_info and len(exc_info)>1 and exc_info[1] is not None:
        candidates.append(exc_info[1])

    for candidate in candidate:
        if isinstance(candidate,ytdlpError):
            return _STATUS_MAP.get(candidate.status,FetchError.UNKNOWN)

    if isinstance(exc,ytdlp_utlis.UnavailableVideoError):
        return FetchError.UNAVAILABLE

    return FetchError.UNKNOWN