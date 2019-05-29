from functools import lru_cache
from typing import Optional, Dict, Any

from sqlalchemy import create_engine
from sqlalchemy.sql import text

from ..logger_factory import LoggerFactory

logger = LoggerFactory.get(__name__)


class Core:
    def __init__(self, base_url: str, db_name: str):
        self.db_name = db_name
        self.base_url = base_url

    @property
    @lru_cache(maxsize=1)
    def engine(self):
        return create_engine(f'{self.base_url}/{self.db_name}')

    def connect(self):
        return self.engine.connect()

    def run(self, query: str, params: Optional[Dict[str, Any]] = None):
        with self.connect() as c:
            # logger.debug('run: %s', query)
            c.execute(text(query), params)

    def run_and_return(self, query: str, params: Optional[Dict[str, Any]] = None):
        with self.connect() as c:
            # logger.debug('run_and_return: %s', query)
            cursor = c.execute(text(query), params) if params else c.execute(text(query))
            result = cursor.fetchall()
        return result


class Session:
    def __init__(self, engine):
        pass

    def __enter__(self):
        pass
        # api_response = boto3.client('s3').create_multipart_upload(Bucket=self.bucket_name,
        #                                                           Key=self.object_key,
        #                                                           ContentType=self.content_type)
        # self.upload_id = api_response['UploadId']
        # self.mp_upload = boto3.resource('s3').MultipartUpload(self.bucket_name, self.object_key, self.upload_id)
        # self.thread_pool = ThreadPoolExecutor(max_workers=MULTIPART_UPLOAD_MAX_WORKERS)
        # return self

    def __exit__(self, etype, value, traceback):
        pass
        # if etype:
        #     logger.error('Upload %s: Error detected within the MPU context.',
        #                  self.upload_id,
        #                  exc_info=(etype, value, traceback)
        #                  )
        #     self.__abort()
        # else:
        #     self.__complete()
