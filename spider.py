from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from lxml import etree


class CnblogSpider(object):

    def worker(self, url):
        response = requests.get(url)
        html = response.text
        page = etree.HTML(html)
        title = page.xpath('//*[@id="cb_post_title_url"]/span/text()')[0]
        writor = page.xpath('//*[@id="Header1_HeaderTitle"]/text()')[0]
        # 文章内容
        data = page.xpath('//*[@id="cnblogs_post_body"]')
        content = data[0].xpath('string(.)').strip()
        print(content)
        # 输出格式化
        res = url + '\n' + title + '\n' + writor + '\n'
        return res

    def run(self, input_file, output_file):
        with open(input_file, 'r') as fr, open(output_file, 'w') as fw:
            with ThreadPoolExecutor(max_workers=10) as exec:
                tasks = [exec.submit(self.worker, url) for url in fr]
                for future in as_completed(tasks):
                    res = future.result()
                    fw.write(res)


if __name__ == '__main__':
    t = CnblogSpider()
    url = "https://www.cnblogs.com/notfound9/p/13041794.html"
    content = t.worker(url)
    print(content)
