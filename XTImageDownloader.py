import os
import os.path
import re
import urllib2


class Picture(object):

    def __init__(self, name, url, dir_path, index):
        self.index = index
        self.name = name
        self.url = url
        self.dir_path = dir_path
        self.error_reason = None

    def start_download_pic(self):
        pic_path = self.build_pic_name()

        # return
        if os.path.exists(pic_path):
            print ('pic has existed:' + self.url)
            self.error_reason = "pic has existed:"
            return self.error_reason

        if not self.url.startswith("http"):
            print ('pic has invalid url:' + self.url)
            self.error_reason = "pic has invalid url"
            return self.error_reason

        header = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.114 Safari/537.36',
            'Cookie': 'AspxAutoDetectCookieSupport=1',
        }

        request = urllib2.Request(self.url, None, header)
        try:
            response = urllib2.urlopen(request, timeout=10)
        except Exception, error:
            print ('pic cannot download:' + self.url)
            self.error_reason = str(error)
            return self.error_reason

        try:
            fp = open(pic_path, 'wb')
            fp.write(response.read())
            fp.close()
        except IOError, error:
            print(error)
            self.error_reason = str(error)
            return self.error_reason

    def build_pic_name(self):
        pic_url = self.url.split("?")[0]

        urls = pic_url.split(".")
        if len(urls) > 1:
            pic_type = urls[len(urls)-1]
        else:
            pic_type = "jpg"

        if self.name is not None and len(self.name) > 0:
            pic_name = self.name + "." + pic_type
        else:
            pic_name = "no_name_" + str(self.index) + "." + pic_type

        pic_path = os.path.join(self.dir_path, pic_name)
        return pic_path


class Article(object):

    def __init__(self, path):
        self.article_path = path
        self.article_pic_dir = path.replace(".md", "_Image")
        # new image dir
        self.mkdir_image_dir()
        # search pic
        self.pic_list = self.find_pics(self.article_path)

    def find_pics(self, article_path):
        f = open(article_path, 'r')
        content = f.read()
        pics = []

        # match ![]()
        results = re.findall(r"!\[(.+?)\)", content)

        index = 0
        for result in results:
            temp_pic = result.split("](")
            if len(temp_pic) == 2:
                pic = Picture(temp_pic[0], temp_pic[1], self.article_pic_dir, index)
                pics.append(pic)
            index += 1

        return pics

    def mkdir_image_dir(self):
        if not os.path.exists(self.article_pic_dir):
            os.mkdir(self.article_pic_dir)


def find_sub_path(path):
    article_list = []

    temp_files = os.listdir(path)

    for temp_file in temp_files:
        # full path
        full_path = os.path.join(path, temp_file)

        # find .md
        if os.path.isfile(full_path) and os.path.splitext(full_path)[1] == ".md":
            article = Article(full_path)
            article_list.append(article)
        # find dir
        elif os.path.isdir(full_path):
            article_list.extend(find_sub_path(full_path))

    return article_list


def find_markdown_pic(root_path):
    article_list = find_sub_path(root_path)

    all_pic_count = 0
    current_pic_index = 0
    download_error_list = []

    for article in article_list:
        all_pic_count += len(article.pic_list)

    for article in article_list:
        for pic in article.pic_list:
            # download pic
            error = pic.start_download_pic()
            if error is not None and len(error) > 0:
                download_error_list.append(pic)

            current_pic_index += 1
            print('finish:' + str(current_pic_index) + '/' + str(all_pic_count))

    print("-----------------------------------")
    print("some pic download failure:")
    for pic in download_error_list:
        print("")
        print("name:" + pic.name)
        print("url:" + pic.url)
        print("error_reason:" + pic.error_reason)


# root_path = input()
# FindPaths(root_path)
find_markdown_pic("/Users/xietao/Desktop/files/user-1319710-1513223040")




