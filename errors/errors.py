from enum import Enum,auto

class FetchError(Enum):
    NOT_FOUND=auto()
    FORBIDDEN=auto()
    RATE_LIMITED=auto()
    UNAVAILABLE=auto()
    UNKNOWN=auto()


_STATUS_MAP={
    404:FetchError.NOT_FOUND,
    429:FetchError.RATE_LIMITED,
    403:FetchError.FORBIDDEN
}

MESSAGES={
    FetchError.NOT_FOUND: "Video not found it may have been removed, or the URL is wrong.",
    FetchError.FORBIDDEN: "Access forbidden this video may be private or region-locked.",
    FetchError.RATE_LIMITED: "Rate limited by the server try again in a few hours.",
    FetchError.UNAVAILABLE: "This video is unavailable (deleted, private, or age-restricted).",
    FetchError.UNKNOWN: "Download failed for an unrecognized reason — see details below.",
}

class DownloadFailure(Exception):
    def __init__(self, error_type:FetchError,original_message:str):
        self.error_type=error_type
        self.original_message=original_message
        super().__init__(MESSAGES.get(error_type,original_message))
