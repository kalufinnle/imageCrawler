# TODO:add key to feeder_kwargs
from icrawler import Feeder, Crawler, ImageDownloader
from icrawler.builtin import GoogleParser
from six.moves.urllib.parse import urlencode
import logging
import os
import shutil

keywords = [line.strip() for line in open('keywords.txt', 'r').readlines()]
storage_prefix = 'data/'
type = 'photo'  # None, 'face', 'photo', 'clipart', 'lineart', 'animated'


class MyFeeder(Feeder):
    def feed(self,
             keyword,
             offset,
             max_num,
             date_min=None,
             date_max=None,
             language=None,
             usage_rights=None,
             type=None):  # TODO: add params
        base_url = 'https://www.google.com/search?'
        if usage_rights and usage_rights not in ['f', 'fc', 'fm', 'fmc']:
            # f: non-commercial reuse
            # fm: non-commercial reuse with modification
            # fc: reuse
            # fmc: reuse with modification
            raise ValueError(
                '"usage_rights" must be one of the following: f, fc, fm, fmc')
        if type and type not in ['face', 'photo', 'clipart', 'lineart', 'animated']:
            raise ValueError(
                '"type" must be one of the following: face, photo, clipart, lineart, animated')
        for i in range(offset, offset + max_num, 100):
            cd_min = date_min.strftime('%m/%d/%Y') if date_min else ''
            cd_max = date_max.strftime('%m/%d/%Y') if date_max else ''
            lang = 'lang_' + language if language else ''
            usage_rights = '' if usage_rights is None else usage_rights
            tbs = 'cdr:1,cd_min:{},cd_max:{},sur:{}'.format(cd_min, cd_max,
                                                            usage_rights)
            if type is not None:
                tbs += ',itp:{}'.format(type)
            # TODO: add params
            params = dict(
                q=keyword,
                ijn=int(i / 100),
                start=i,
                tbs=tbs,
                tbm='isch',
                lr=lang)
            url = base_url + urlencode(params) + '&chips=q:' + keyword + \
                  ',g:construction%20site'  # add tag: construction site
            self.out_queue.put(url)
            self.logger.debug('put url to url_queue: {}'.format(url))


class MyCrawler(Crawler):
    def __init__(self,
                 feeder_cls=MyFeeder,
                 parser_cls=GoogleParser,
                 downloader_cls=ImageDownloader,
                 *args,
                 **kwargs):
        super(MyCrawler, self).__init__(
            feeder_cls, parser_cls, downloader_cls, *args, **kwargs)

    def crawl(self,
              keyword,
              offset=0,
              max_num=1000,
              date_min=None,
              date_max=None,
              min_size=None,
              max_size=None,
              language=None,
              usage_rights=None,
              type=None,
              file_idx_offset=0):  # TODO: add params
        if offset + max_num > 1000:
            if offset > 1000:
                self.logger.error(
                    '"Offset" cannot exceed 1000, otherwise you will get '
                    'duplicated searching results.')
                return
            elif max_num > 1000:
                max_num = 1000 - offset
                self.logger.warning(
                    'Due to Google\'s limitation, you can only get the first '
                    '1000 result. "max_num" has been automatically set to %d. '
                    'If you really want to get more than 1000 results, you '
                    'can specify different date ranges.', 1000 - offset)

        feeder_kwargs = dict(
            keyword=keyword,
            offset=offset,
            max_num=max_num,
            date_min=date_min,
            date_max=date_max,
            language=language,
            usage_rights=usage_rights,
            type=type)  # TODO: add params
        downloader_kwargs = dict(
            max_num=max_num,
            min_size=min_size,
            max_size=max_size,
            file_idx_offset=file_idx_offset)
        super(MyCrawler, self).crawl(
            feeder_kwargs=feeder_kwargs, downloader_kwargs=downloader_kwargs)


if __name__ == '__main__':
    for keyword in keywords:
        if os.path.exists(keyword):
            shutil.rmtree(keyword)
        crawler = MyCrawler(parser_threads=2,
                            downloader_threads=4,
                            storage={'root_dir': storage_prefix + keyword},
                            log_level=logging.INFO)
        crawler.crawl(keyword=keyword, max_num=1000,
                      date_min=None, date_max=None,
                      min_size=(256, 256), max_size=None,
                      type=type)
